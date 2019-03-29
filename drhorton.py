import re
import csv
import json
import time
import logging
import requests

from redis import StrictRedis
from redis.exceptions import RedisError
from rediscache import RedisCache
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class DRHortonScraper(object):
    radius = 500 
    states = [
        {
            "name": "hawaii",
            "url": "https://www.drhorton.com/hawaii",
            "center": [
                "21.09938",
                "-156.8953"
            ]
        },
        {
            "name": "florida",
            "url": "https://www.drhorton.com/florida",
            "center": [
                "28.73217",
                "-81.79927"
            ]
        },
        {
            "name": "south-carolina",
            "url": "https://www.drhorton.com/south-carolina",
            "center": [
                "33.93228",
                "-80.67388"
            ]
        },
        {
            "name": "georgia",
            "url": "https://www.drhorton.com/georgia",
            "center": [
                "32.86183",
                "-83.49816"
            ]
        },
        {
            "name": "alabama",
            "url": "https://www.drhorton.com/alabama",
            "center": [
                "32.5593",
                "-86.88033"
            ]
        },
        {
            "name": "tennessee",
            "url": "https://www.drhorton.com/tennessee",
            "center": [
                "35.78239",
                "-86.32741"
            ]
        },
        {
            "name": "new-jersey",
            "url": "https://www.drhorton.com/new-jersey",
            "center": [
                "39.94444",
                "-74.95459"
            ]
        },
        {
            "name": "pennsylvania",
            "url": "https://www.drhorton.com/pennsylvania",
            "center": [
                "40.18119",
                "-75.54797"
            ]
        },
        {
            "name": "delaware",
            "url": "https://www.drhorton.com/delaware",
            "center": [
                "38.98546",
                "-75.51675"
            ]
        },
        {
            "name": "maryland",
            "url": "https://www.drhorton.com/maryland",
            "center": [
                "39.07114",
                "-76.74081"
            ]
        },
        {
            "name": "washington",
            "url": "https://www.drhorton.com/washington",
            "center": [
                "47.27816",
                "-120.67"
            ]
        },
        {
            "name": "texas",
            "url": "https://www.drhorton.com/texas",
            "center": [
                "31.21203",
                "-98.8404"
            ]
        },
        {
            "name": "california",
            "url": "https://www.drhorton.com/california",
            "center": [
                "36.92287",
                "-120.3086"
            ]
        },
        {
            "name": "arizona",
            "url": "https://www.drhorton.com/arizona",
            "center": [
                "34.28866",
                "-111.7392"
            ]
        },
        {
            "name": "nevada",
            "url": "https://www.drhorton.com/nevada",
            "center": [
                "38.98648",
                "-116.8407"
            ]
        },
        {
            "name": "utah",
            "url": "https://www.drhorton.com/utah",
            "center": [
                "40.76953",
                "-111.9182"
            ]
        },
        {
            "name": "colorado",
            "url": "https://www.drhorton.com/colorado",
            "center": [
                "39.08336",
                "-105.4412"
            ]
        },
        {
            "name": "new-mexico",
            "url": "https://www.drhorton.com/new-mexico",
            "center": [
                "34.19944",
                "-106.3048"
            ]
        },
        {
            "name": "oregon",
            "url": "https://www.drhorton.com/oregon",
            "center": [
                "43.8485",
                "-120.6598"
            ]
        },
        {
            "name": "louisiana",
            "url": "https://www.drhorton.com/louisiana",
            "center": [
                "30.81851",
                "-92.11426"
            ]
        },
        {
            "name": "virginia",
            "url": "https://www.drhorton.com/virginia",
            "center": [
                "37.49055",
                "-78.71546"
            ]
        },
        {
            "name": "illinois",
            "url": "https://www.drhorton.com/illinois",
            "center": [
                "39.87584",
                "-88.96261"
            ]
        },
        {
            "name": "oklahoma",
            "url": "https://www.drhorton.com/oklahoma",
            "center": [
                "35.51939",
                "-98.6967"
            ]
        },
        {
            "name": "minnesota",
            "url": "https://www.drhorton.com/minnesota",
            "center": [
                "44.96167",
                "-93.25771"
            ]
        },
        {
            "name": "north-carolina",
            "url": "https://www.drhorton.com/north-carolina",
            "center": [
                "35.69635",
                "-79.43424"
            ]
        },
        {
            "name": "mississippi",
            "url": "https://www.drhorton.com/mississippi",
            "center": [
                "32.7201",
                "-89.60005"
            ]
        },
        {
            "name": "west-virginia",
            "url": "https://www.drhorton.com/west-virginia",
            "center": [
                "38.73081",
                "-80.6711"
            ]
        },
        {
            "name": "iowa",
            "url": "https://www.drhorton.com/iowa",
            "center": [
                "42.06827",
                "-93.5092"
            ]
        },
        {
            "name": "indiana",
            "url": "https://www.drhorton.com/indiana",
            "center": [
                "39.64506",
                "-86.13032"
            ]
        },
        {
            "name": "wisconsin",
            "url": "https://www.drhorton.com/wisconsin",
            "center": [
                "42.58053",
                "-87.86542"
            ]
        }
    ]

    def __init__(self):
        self.url = 'https://www.drhorton.com'
        self.session = requests.Session()
        self.headers = {
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        FORMAT = "%(asctime)s [ %(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
        logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.cache = None
        #self.init_cache()

    def init_cache(self):
        redis_config = {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': 'foobared'
        }

        client = StrictRedis(**redis_config)
        try:
            client.ping()
        except RedisError as ex:
            exit(f'Failed to connect to Redis - {ex}, exiting...' )

        self.cache = RedisCache(client=client)

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

        with open('DRHorton.csv', 'w') as fp:
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

    def scrape_home_attrs(self, home_info_div):
        h = home_info_div
        home = {}

        p = h.select_one('div.info-frame > p.title')
        a = p.find_next_sibling('p').a

        address = lambda s: ' '.join(s.strip().split())

        home['url'] = urljoin(self.url, a['href'])
        home['address'] = address(a.text)

        s = h.select_one('div.sq-ft > p > strong')
        home['sqft'] = s.text.strip()

        p = h.select_one('div.cost > p.price')
        if p: # Sometimes price not listed if under contract
            home['price'] = p.text.strip()
        else:
            home['price'] = ''
            
        for li in h.select('ul.specs > li'):
            k = li.contents[-1].strip().lower()
            home[k] = li.strong.text.strip()

        return home
    
    #########################################################################
    # They're using sitecore on the backend to do these queries in
    # CommunityFinderMap.ts
    #
    # Sitecore won't give us back more than 1000 results so we can't just do
    # a blanket search of the US as it will only give us back the first 1000
    # results:
    #
    #   https://answers.coveo.com/questions/6103/coveopager-not-supporting-page-101-or-higher.html
    #
    # The way the search appears to work per-state is that they pass a
    # (lat,lng) pair for the middle of the state along with a radius/distance
    # and sitecore returns a list of communities within the geographic range
    #########################################################################    
    def get_state_communities(self, state, communities):
        '''
        Return a list of community IDs for state
        '''
        skipped = []
        lat,lng = state['center'][0], state['center'][1]
        
        url = 'https://www.drhorton.com/coveo/rest/v2'
        data = {
            'firstResult': 0,
            'numberOfResults': 1000,
            'queryFunctions': json.dumps([
                {
                    "function": f"dist(@fcoordinatesz32xlatitude33386, @fcoordinatesz32xlongitude33386, {lat}, {lng})/1610",
                    "fieldName": "@fdistance33386"
                }
            ]),
            'aq': f'(@fdistance33386<{self.radius})'
        }

        resp = self.session.post(url, data=data)
        resp_data = resp.json()

        self.logger.info(f"Returning {len(resp_data['results'])} communities for {state}")
        
        for r in resp_data['results']:
            k = next(
                k for k in r['raw'].keys()
                if k.startswith('fid')
            )
            v = r['raw'][k]

            if v not in communities:
                communities.append(v)
            else:
                #self.logger.info(f'{v} already in communities')
                skipped.append(v)

        self.logger.info(f'Skipped {len(skipped)} duplicates')
        return communities
    
    def get_movein_ready(self, community_id):
        '''
        Return the HTML for the Move In Ready homes using internal API
        '''
        homes = []
        
        # {EA8CC92D-EEEA-4CC5-8BD1-AD65388128F4} has more than 8 for testing
        #community_id = '{EA8CC92D-EEEA-4CC5-8BD1-AD65388128F4}'
        
        url = 'https://www.drhorton.com/api/drh/moveinreadyapi/getrelated'
        data = {
            'ItemId': community_id,
            'StartIndex': 0,
            'Count': 8
        }

        self.logger.debug(f'Getting move in ready homes for {community_id}')

        if self.cache:
            try:
                cached_homes = self.cache[community_id]
            except KeyError:
                pass
            else:
                homes = json.loads(cached_homes)
                self.logger.info(f'Returning {len(homes)} homes from cache')
                return homes

        while True:
            time.sleep(5)
            try:            
                resp = self.session.post(url, data=data)
                jdat = resp.json()
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f'Exception {e}')
                time.sleep(60)
                continue
            except Exception as e:
                self.logger.warning(f'Exception {e}')
                homes = [] # reset homes
                break

            for item in jdat['HtmlItems']:
                h = BeautifulSoup(item, 'html.parser')
                home = self.scrape_home_attrs(h)
                homes.append(home)

            self.logger.debug(f"Got {len(homes)} / {jdat['TotalItems']} homes")
            
            if len(homes) >= jdat['TotalItems'] or len(jdat['HtmlItems']) == 0:
                break
            
            data['StartIndex'] = len(homes)

        if self.cache and len(homes) > 0:
            self.cache[community_id] = json.dumps(homes)

        return homes
    
    def scrape(self):
        homes = []
        communities = []

        for state in DRHortonScraper.states:
            self.get_state_communities(state, communities)
            time.sleep(5)

        self.logger.info(f'{len(communities)} communities')
        
        for i,cid in enumerate(communities, 1):
            self.logger.info(f'{i}/{len(communities)}')
            m = self.get_movein_ready(cid)
            homes += m

        self.logger.info(f'Scraped {len(homes)} in total')
        self.csv_save(homes)

        return homes
    
if __name__ == '__main__':
    scraper = DRHortonScraper()
    scraper.scrape()
