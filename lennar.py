import csv
import json
import requests
from urllib.parse import urljoin

class LennarScraper(object):
    def __init__(self):
        self.url = 'https://www.lennar.com/Services/Rest/SearchMethods.svc/GetInventoryTabDetails'
        self.session = requests.Session()
        self.data = {
            "CommunityID":"4531",
            "pageState":{
                "ct":"A",
                "pt": u"\u0000",
                "sb":"price",
                "so":"asc",
                "pn":1,
                "ps":17,
                "ic":0,
                "ss":0,
                "attr":"",
                "ius":False
            },
            "tabLocation": {
                "mi":"0",
                "lat":0,
                "long":0
            }
        }

    def csv_save(self, data):
        headers = [
            'Community',
            'Community URL',
            'Address',
            'URL',
            'Price'
        ]

        with open('lennar.csv', 'w') as fp:
            writer = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(headers)

            for d in data:
                row = [
                    d.get('community', ''),
                    d.get('community_url', ''),
                    d.get('address', ''),
                    d.get('url', ''),
                    d.get('price', ''),
                ]
                row = [ i for i in row  ]
                writer.writerow(row)
        
    def scrape(self):
        homes = []
        
        resp = self.session.post(self.url, json=self.data)
        data = resp.json()

        for d in data['ir']:
            home = {}

            home['community'] = d['cnm']
            home['community_url'] = urljoin(self.url, d['cmURL'])
            home['address'] = d['spdAdd'] +  ', ' + d['city'] + ', ' + d['stcd'] + ' ' + d['spZip']
            home['price'] =  d['price']
            home['url'] = urljoin(self.url, d['vtlURL'])

            homes.append(home)
            
        self.csv_save(homes)
        return homes
    
if __name__ == '__main__':
    scraper = LennarScraper()
    scraper.scrape()
