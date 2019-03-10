import re
import json
import requests

from urllib.parse import urljoin
from bs4 import BeautifulSoup

class PulteScraper(object):
    def __init__(self):
        self.url = 'https://www.pulte.com/api/Qmi/Search'
        self.session = requests.Session()
        self.headers = {
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        self.params = {
            'brand': 'Pulte',
            'state': 'Georgia',
            'region': None,
            'cityNames': None,
            'minPrice': None,
            'maxPrice': None,
            'minBedrooms': None,
            'maxBedrooms': None,
            'minBathrooms': None,
            'maxBathrooms': None,
            #'pageSize': 10,
            'pageSize': 50,
            'pageNumber': 0
        }

    def scrape_listings(self, soup):
        homes = []
        
        address = lambda s: ' '.join(s.strip().split())
        community = lambda s: s.replace('Community:', '').strip()
        
        re_price = re.compile(r'(\$[\d,]+)')
        match_price = lambda t: t.name == 'div' and \
                      'data-value' in t.get('class', []) and \
                      'stat-line' not in t.get('class', []) and \
                      re.search(re_price, t.text)
        
        for div in soup.select('div.HomeDesignSummary--qmi'):
            home = {}

            a = div.select_one('div.community-name > a')
            
            home['community'] = community(a.text)
            home['community_url'] = urljoin(self.url, a['href'])
            home['address'] = address(div.select_one('div.address-phone > div.address').text)

            f = lambda t: t.name == 'a' and t.text.strip() == 'View Home'
            a = div.find(f)

            home['url'] = urljoin(self.url, a['href'])
            
            d = div.find(match_price)
            home['price'] = d.text.strip()
            homes.append(home)

        return homes

    def get_states(self):
        resp = self.session.get('https://www.pulte.com/homes/georgia')
        soup = BeautifulSoup(resp.text, 'html.parser')

        r = re.compile(r'LocationSelectionData.locations =\s+(\[[^;]+)')
        match_script = lambda t: t.name == 'script' and re.search(r, t.text.strip())
        
        script = soup.find(match_script)

        m = re.search(r, script.text)
        data = json.loads(m.group(1))

        states = [
            d['StateName'] for d in data[0]['States']
        ]
        
        return states
        
    def scrape(self):
        homes = []        
        states = self.get_states()

        for state in states:
            self.params['state'] = state
            
            while True:
                resp = self.session.get(self.url, headers=self.headers, params=self.params)
                if len(resp.text.strip()) == 0:
                    break
            
                soup = BeautifulSoup(resp.text, 'html.parser')

                homes += self.scrape_listings(soup)

                self.params['pageNumber'] += 1
            
        return homes
    
if __name__ == '__main__':
    scraper = PulteScraper()
    scraper.scrape()
