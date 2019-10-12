import requests    
import re    
from urllib.parse import urlparse
from time_enforcer import enforce_time_remaining, TimeRemainingExpired
import time

class PyCrawler(object):    
    def __init__(self, starting_url, threaded_postgreSQL_pool):    
        self.starting_url = starting_url
        self.connection = threaded_postgreSQL_pool.getconn()
        if not self.connection:
            print('[ERROR] Connection in pyCrawler failed')

    def get_html(self, url):    
        try:    
            html = requests.get(url)   
        except Exception as e:    
            print(e)    
            return ""         
        return (html.content.decode('latin-1'), html.elapsed.total_seconds())    

    def get_links(self, url):    
        html, response_time = self.get_html(url)    
        parsed = urlparse(url)    
        base = f"{parsed.scheme}://{parsed.netloc}"    
        links = re.findall('''<a\s+(?:[^>]*?\s+)?href="([^"]*)"''', html)    
        for i, link in enumerate(links):    
            if not urlparse(link).netloc:    
                link_with_base = base + link    
                links[i] = link_with_base    

        # exclude email links
        return (response_time, set(filter(lambda x: 'mailto' not in x, links)))

    def extract_info(self, url):    
        html = self.get_html(url)    
        meta = re.findall("<meta .*?name=[\"'](.*?)['\"].*?content=[\"'](.*?)['\"].*?>", html)    
        return dict(meta)    
    
    def checkVisited(self, link):
        cursor = self.connection.cursor()
        cursor.execute("select * from websites where url='%s';" % (link))
        is_visited = cursor.fetchone()
        if is_visited:
            print('Existed!')
        cursor.close()
        return is_visited

    def addToVisited(self, link, response_time):
        cursor = self.connection.cursor()
        cursor.execute("insert into websites values ('%s', '%g');" % (link, response_time))
        cursor.execute("select * from websites where url='%s' and responseTime='%g';" % (link, response_time))
        is_added = cursor.fetchone()
        self.connection.commit()
        cursor.close()
        return is_added    

    @enforce_time_remaining
    def crawl(self, url, **kwargs):
        # getting all links in the url from html
        response_time, links = self.get_links(url)
        print("[LOGS] Time taken for response: " + str(response_time) + "\n[LOGS] Link: " + url)

        # add link to db 
        if self.addToVisited(url, response_time):
            print("[LOGS] Added link to db: " + url + "\n")

        for link in links:    
            if self.checkVisited(link):    
                continue

            # info = self.extract_info(link)
            # print(f"""  Link: {link}    
            #             Description: {info.get('description')}    
            #             Keywords: {info.get('keywords')}    
            # """)    

            # Delay request rate by 1s
            time.sleep(1)
            self.crawl(link, **kwargs)    

    @enforce_time_remaining
    def start(self, **kwargs):    
        self.crawl(self.starting_url, **kwargs)    