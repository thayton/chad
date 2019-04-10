import re
import csv
import json
import logging
import requests

from urllib.parse import urljoin
from bs4 import BeautifulSoup

class SheaHomesScraper(object):
    def __init__(self):
        self.url = 'https://www.sheahomes.com/new-homes/'
        self.params = {
            'state': 'any',
            'bedrooms': 'any',
            'bathrooms': 'any',
            'pricemin': 'any',
            'pricemax': 'any',
            'quickmovein': 'on'
        }
        self.headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        }

        FORMAT = "%(asctime)s [ %(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
        logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.session = requests.Session()

    def csv_save(self, data):
        headers = [
            'URL',
            'Address',
            'Sqft',
            'Price',
            'Stories',
            'Beds',
            'Baths',
            'Garage'
        ]

        with open('sheahomes.csv', 'w') as fp:
            writer = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(headers)

            for d in data:
                row = [
                    d.get('url', ''),
                    d.get('address', ''),
                    d.get('sqft', ''),
                    d.get('price', ''),
                    d.get('story', ''),
                    d.get('bed', ''),
                    d.get('bath', ''),
                    d.get('car', '')
                ]
                row = [ i for i in row  ]
                writer.writerow(row)

    def submit_community_aspx(self, url):
        '''
        We only need to submit the form is there is a View More button. Otherwise
        all of the results are already in the HTML. In the case where there are 
        more homes to load then the AVAILABLE QUICK MOVE-IN HOMES are loaded via 
        an AJAX ASPX POST. 

        We simulate this post and return the HTML from the response

        ref: http://toddhayton.com/2015/05/04/scraping-aspnet-pages-with-ajax-pagination/
        '''
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')

        form = soup.find('form', id='form')
        data = []

        i = form.find('input', attrs={'value': 'View More'})
        if not i:
            return soup.prettify()

        # The ID of this div is the same as what gets passed in the manScript form data
        # but with the '_' characters replaced with '$'
        r = re.compile(r'^p_lt_ctl\d+_pageplaceholder_p_lt_ctl\d+_QMIHomes_CMSUpdatePanel\d+$')
        update_div = soup.find('div', id=r)
        update_div_v = update_div['id'].replace('_', '$')
        
        # Load form <inputs>
        for i in form.find_all('input', attrs={'name': True}):
            if i.get('type') == 'submit' and i.get('value') == 'View More':
                data.append(('manScript', update_div_v + '|' + i['name']))
                data.append((i['name'], i.get('value')))                
            elif i['type'] == 'checkbox':
                data.append((i['name'], i.get('checked') == '' and 'on' or 'off'))
            else:
                data.append((i['name'], i.get('value')))

        data = dict(data)

        # The following are set dynamically by javascript code
        data['__ASYNCPOST'] = 'true'
        data['__EVENTTARGET'] = None
        data['__EVENTARGUMENT'] = None
        data['__SCROLLPOSITIONX'] = 0        
        data['__SCROLLPOSITIONY'] = 0

        url = urljoin(self.url, form['action'])
        resp = self.session.post(url, headers=self.headers, data=data)

        it = iter(resp.text.split('|'))
        kv = dict(zip(it, it))

        return kv[update_div['id']]

    def submit_quick_moveins_search(self):
        resp = self.session.get(self.url, params=self.params)
        soup = BeautifulSoup(resp.text, 'html.parser')

        form = soup.find('form', id='form')
        data = []

        # p_lt_ctl03_pageplaceholder_p_lt_ctl02_FYHSearchResultsFilter_upCommunityListing
        r = re.compile(r'p_lt_ctl\d+_pageplaceholder_p_lt_ctl\d+_FYHSearchResultsFilter_upCommunityListing')
        update_div = soup.find('div', id=r)
        update_div_v = update_div['id'].replace('_', '$')

        # Load form <inputs>
        for i in form.find_all('input', attrs={'name': True}):
            if i['type'] == 'checkbox':
                continue
            elif i.get('type') == 'submit' and i.get('id') == 'btnHiddenDeferInitialDataLoad':
                data.append(('manScript', update_div_v + '|' + i['name']))
                data.append((i['name'], i.get('value')))
            else:
                data.append((i['name'], i.get('value')))

        for s in form.find_all('select', attrs={'name': True}):
            if s['name'] in ['type', 'features']:
                continue
            data.append((s['name'], s.option.get('value')))

        data = dict(data)

        # The following are set dynamically by javascript code
        data['__ASYNCPOST'] = 'true'
        data['__EVENTTARGET'] = None
        data['__EVENTARGUMENT'] = None
        data['__SCROLLPOSITIONX'] = 0
        data['__SCROLLPOSITIONY'] = 0

        url = urljoin(self.url, form['action'])
        resp = self.session.post(url, headers=self.headers, data=data)

        # Looking for something like:
        # |392405|updatePanel|p_lt_ctl03_pageplaceholder_p_lt_ctl02_FYHSearchResultsFilter_upCommunityListing|
        r = re.compile(r'\|(\d+)\|updatePanel\|%s\|' % update_div['id'])
        m = re.search(r, resp.text)

        i = m.end()
        j = m.end() + int(m.group(1))

        return resp.text[i:j]

    def get_community_links(self):
        html = self.submit_quick_moveins_search()
        soup = BeautifulSoup(html, 'html.parser')
        urls = []

        for a in soup.select('a.card-community'):
            url = urljoin(self.url, a['href'])
            urls.append(url)

        self.logger.info(f'Returning {len(urls)} move in ready communities')
        return urls

    def scrape(self):
        lots = []
        urls = self.get_community_links()
        
        for url in urls:
            self.logger.info(f'Getting movein ready homes at {url}')

            html = self.submit_community_aspx(url)
            soup = BeautifulSoup(html, 'html.parser')
            divs = soup.select('section#qmi-homes div.card-content')

            self.logger.info(f'{len(divs)} movein ready homes')

            for d in divs:
                lot = {}
                lot['url'] = urljoin(self.url, d.a['href'])
            
                data = self.scrape_lot(lot['url'])
            
                lot.update(data)
                lots.append(lot)

        self.csv_save(lots)
        
    def scrape_lot(self, url):
        lot = {}
        
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')

        addr = soup.select_one('div.about-address')
        addr.select_one('p.address-label').extract()
        
        addr = addr.text.strip().split('\n')
        addr = ' '.join(a.strip() for a in addr)
        
        lot['address'] = addr

        # Extract price and sqft
        p = soup.find('p', attrs={'class': 'large'})
        
        r = re.compile('Priced From \$([\d,]+)', re.I)
        m = re.search(r, p.text)
        lot['price'] = m.group(1)

        r = re.compile('([\d,]+) Sq\. Ft', re.I)
        m = re.search(r, p.text)
        lot['sqft'] = m.group(1)

        icons = {
            'story': 'Stories Icon',
            'bed': 'Bedroom Icon',
            'bath': 'Bathroom Icon',
            'car': 'Garage Icon'
        }

        for k,v in icons.items():
            img = soup.find('img', attrs={'alt': v})
            li = img.find_parent('li')
            lot[k] = li.p.text.strip()

        # Raw text
        lot['blurb'] = '\n'.join([
            t.strip() for t in p.text.split('\n')
            if len(t.strip()) > 0
        ])

        return lot
    
if __name__ == '__main__':
    scraper = SheaHomesScraper()
    scraper.scrape()
