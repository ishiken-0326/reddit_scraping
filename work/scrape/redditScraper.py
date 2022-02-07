import configparser
import praw
import re
import os
import concurrent.futures
import requests
from bs4 import BeautifulSoup
import urllib
from urllib.request import urlopen
import time

class redditImageScraper:
    def __init__(self, sub, limit, order, sleep=1):
        config = configparser.ConfigParser()
        config.read('conf.ini')
        self.sub = sub
        self.limit = limit
        self.order = order
        self.path = f'images/{self.sub}/'
        self.reddit = praw.Reddit(
            client_id=config['REDDIT']['client_id'],
            client_secret=config['REDDIT']['client_secret'],
            user_agent=config['REDDIT']['user_agent']
        )
        self.headers = {
            'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0'
        }
        self.sleep = sleep
    
    def download(self, image):
        r = requests.get(image['url'])
        with open(image['fname'], 'wb') as f:
            f.write(r.content)

    def scrape(self):
        images = []
        try:
            cnt = 0
            if self.order == 'hot':
                submissions = self.reddit.subreddit(self.sub).hot(limit=None)
            elif self.order == 'top':
                submissions = self.reddit.subreddit(self.sub).top(limit=None)
            elif self.order == 'new':
                submissions = self.reddit.subreddit(self.sub).new(limit=None)
            
            for submission in submissions:
                time.sleep(1)
                if not submission.stickied and submission.url.endswith(('jpg', 'png', 'jpeg')):
                    fname = self.path + re.search('(?s:.*)\w/(.*)', submission.url).group(1)
                    if not os.path.isfile(fname):
                        images.append({'url': submission.url, 'fname': fname})
                        print(submission.url)
                        cnt += 1
                        if cnt >= self.limit:
                            break
                
                elif not submission.stickied and submission.url.startswith(('https://www.reddit.com/gallery')):
                    url = submission.url
                    request = urllib.request.Request(url, headers=self.headers)
                    html = urlopen(request)
                    bs_obj = BeautifulSoup(html, 'html.parser')
                    lists = bs_obj.findAll('li')
                    for li in lists:
                        li = li.find('a')
                        link = li.get('href')
                        if re.search('.jpg|.png|.jpeg', link) is not None:
                            e = re.search('.jpg|.png|.jpeg', link).end()
                            s = re.search('preview.redd.it', link).end() + 1
                            # fname = 'images/test/' + re.search('(?s:.*)\w/(.*)', url).group(1) + '_' + link[s:e]
                            fname = self.path + re.search('(?s:.*)\w/(.*)', url).group(1) + '_' + link[s:e]
                            if not os.path.isfile(fname):
                                images.append({'url': link, 'fname': fname})
                                print(link)
                                cnt += 1
                                if cnt >= self.limit:
                                    break
            print('DONE: get image urls')
            if len(images):
                if not os.path.exists(self.path):
                    os.makedirs(self.path)
                # with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ptolemy:
                #     ptolemy.map(self.download, images)
                img_cnt = 0
                for image in images:
                    time.sleep(self.sleep)
                    self.download(image)
                    img_cnt+=1
                    print(f'{img_cnt} / {len(images)} images downloaded')
                    
        except Exception as e:
            print(e)