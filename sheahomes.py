import re
import json
import requests

from urllib.parse import urljoin
from bs4 import BeautifulSoup

class SheaHomesScraper(object):
    def __init__(self):
        #self.url = 'https://www.sheahomes.com/new-homes/colorado/denver-area/parker/stonewalk-at-stepping-stone/'
        self.url = 'https://www.sheahomes.com/new-homes/florida/central-florida/ocala/trilogy-at-ocala-preserve/'
        self.session = requests.Session()

    def submit_community_aspx(self):
        '''
        We only need to submit the form is there is a View More button. Otherwise
        all of the results are already in the HTML. In the case where there are 
        more homes to load then the AVAILABLE QUICK MOVE-IN HOMES are loaded via 
        an AJAX ASPX POST. 

        We simulate this post and return the HTML from the response

        ref: http://toddhayton.com/2015/05/04/scraping-aspnet-pages-with-ajax-pagination/
        '''
        resp = self.session.get(self.url)
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

        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        }
        
        url = urljoin(self.url, form['action'])
        resp = self.session.post(url, headers=headers, data=data)

        it = iter(resp.text.split('|'))
        kv = dict(zip(it, it))

        return kv[update_div['id']]
    
    def scrape(self):
        lots = []
        
        html = self.submit_community_aspx()
        soup = BeautifulSoup(html, 'html.parser')
        
        for d in soup.select('section#qmi-homes div.card-content'):
            lot = {}
            lot['url'] = urljoin(self.url, d.a['href'])
            
            data = self.scrape_lot(lot['url'])
            
            lot.update(data)
            lots.append(lot)

        print(json.dumps(lots, indent=2))
        
    def scrape_lot(self, url):
        lot = {}
        
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')

        addr = soup.select_one('div.about-address')
        addr.select_one('p.address-label').extract()
        
        addr = addr.text.strip().split('\n')
        addr = ' '.join(a.strip() for a in addr)
        
        lot['addr'] = addr

        # Extract price and sqft
        p = soup.find('p', attrs={'class': 'large'})
        
        r = re.compile('Priced From \$([\d,]+)', re.I)
        m = re.search(r, p.text)
        lot['price'] = m.group(1)

        r = re.compile('([\d,]+) Sq\. Ft', re.I)
        m = re.search(r, p.text)
        lot['sqft'] = m.group(1)

        # Raw text
        lot['blurb'] = '\n'.join([
            t.strip() for t in p.text.split('\n')
            if len(t.strip()) > 0
        ])

        return lot
    
if __name__ == '__main__':
    scraper = SheaHomesScraper()
    scraper.scrape()
