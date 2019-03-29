import os
import re
import csv
import json
import time
import logging
import requests

from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Script to gather the center (lat,lng) of each of the states listed
class DRHortonScraper(object):
    def __init__(self):
        self.url = 'https://www.drhorton.com/no-results'
        self.session = requests.Session()
        self.headers = {
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        FORMAT = "%(asctime)s [ %(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
        logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    # Link at https://www.drhorton.com/no-results#lctm=
    # has an interactive map of states where horton has
    # results
    def get_states(self):
        states = []
        
        resp = self.session.get(self.url)
        soup = BeautifulSoup(resp.text, 'html.parser')

        g = soup.select_one('svg#us-map > g')
        for a in g.find_all('a', href=True):
            state = {}
            state['name'] = os.path.basename(a['href'])
            state['url'] = urljoin(self.url, a['href'])
            states.append(state)
            
        self.logger.info(f'Returning {len(states)} states')
        return states

    def get_state_center_latlng(self, state):
        '''
        Return the (lat,lng) for the center of the state from 
        their map div
        '''
        resp = self.session.get(state['url'])
        soup = BeautifulSoup(resp.text, 'html.parser')

        d = soup.select_one('div.map > div.CoveoCommunityFinderMap')
        lat,lng = d['data-latitude'],d['data-longitude']
        state['center'] = (lat, lng)
        

    def get_state_centers(self):
        states = self.get_states()
        for state in states:
            self.get_state_center_latlng(state)
            time.sleep(5)
        
        print(json.dumps(states, indent=2))
        
if __name__ == '__main__':
    scraper = DRHortonScraper()
    scraper.get_state_centers()
