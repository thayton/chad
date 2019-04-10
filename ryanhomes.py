import re
import csv
import time
import json
import logging
import requests

from urllib.parse import urljoin
from bs4 import BeautifulSoup

class RyanHomesScraper(object):
    def __init__(self):
        self.url = 'https://www.ryanhomes.com/homelist/search'
        self.data = {
            "county":" ",
            "homeType":" ",
            "homeTypeString":" ",
            "isModelInvestment":False,
            "isQuickMoveIn":True,
            "modelName":" ",
            "squareFootage":" ",
            "state":" ",
            "market":" ",
            "pageSize":10
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
            'Beds',
            'Baths',
            'Garage'
        ]

        with open('ryanhomes.csv', 'w') as fp:
            writer = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(headers)

            for d in data:
                row = [
                    d.get('url', ''),
                    d.get('address', ''),
                    d.get('sqft', ''),
                    d.get('price', ''),
                    d.get('bed', ''),
                    d.get('bath', ''),
                    d.get('car', '')
                ]
                writer.writerow(row)

    def gen_listing_url(self, options, item):
        def get_state_name(abbrev):
            for s in options['states']:
                if s['value'] == abbrev:
                    return s['text']

            return abbrev

        # From their code to generate listing URLs (https://www.ryanhomes.com/bundles/angular)
        #
        # listingUrl = '/find-your-home/our-communities/' +
        #              vm.findState(result.state).text.trim().toLowerCase().replace(/\s+/g, "-") + '/' +
        #              result.city.trim().toLowerCase().replace(/\s+/g, "-") + '/' +
        #              result.communitySeoUrl + '/' + productSeo + '/' + result.id;
        #
        if item['productSeoUrl']:
            product_seo = item['productSeoUrl']
        else:
            product_seo = item['name'].replace(' ', '-')

        url = '/find-your-home/our-communities/' + \
              get_state_name(item['state']).strip().lower().replace(' ', '-') + '/' + \
              item['city'].strip().lower().replace(' ', '-') + '/' + \
              item['communitySeoUrl'] + '/' + product_seo + '/' + str(item['id'])

        return urljoin(self.url, url)

    def scrape_home_addr(self, home):
        resp = self.session.get(home['url'])
        soup = BeautifulSoup(resp.text, 'html.parser')

        li = soup.select_one('li.header-locDetails')
        home['address'] = li.text.strip()
        
    def scrape_home_attrs(self, options, item):
        home = {}
        home['sqft'] = item['squareFootage']
        home['price'] = item['startingPrice']
        home['car'] = item['numberGarageSpaces']
        home['bed'] = item['bedrooms']
        home['bath'] = str(item['bathrooms'])
        
        if item['halfBath']:
            home['bath'] += '.5'

        home['url'] = self.gen_listing_url(options, item)
        return home

    def scrape(self):
        homes = []
        
        resp = self.session.post(self.url, json=self.data)
        data = resp.json()
        
        for item in data['items']:
            home = self.scrape_home_attrs(data['options'], item)
            homes.append(home)

        self.logger.info(f'Scraped {len(homes)} homes')

        # Unfortunately we have to load each homes page just to
        # get the address...
        for home in homes:
            self.logger.info(f"Getting address of home at {home['url']}")
            self.scrape_home_addr(home)
            time.sleep(2) # don't hit their servers too quickly...

        self.csv_save(homes)
        
if __name__ == '__main__':
    scraper = RyanHomesScraper()
    scraper.scrape()
                
