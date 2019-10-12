import requests    
import re    
from urllib.parse import urlparse
from time_enforcer import enforce_time_remaining, TimeRemainingExpired
import time

class PyCrawler(object):    
    def __init__(self, starting_url):    
        self.starting_url = starting_url    
        self.visited = set()    

    def get_html(self, url):    
        try:    
            html = requests.get(url)   
        except Exception as e:    
            print(e)    
            return ""    
        print("[LOGS] Time taken for response: " + str(html.elapsed.total_seconds()) + "\n[LOGS] Link: " + url + "\n")     
        return html.content.decode('latin-1')    

    def get_links(self, url):    
        html = self.get_html(url)    
        parsed = urlparse(url)    
        base = f"{parsed.scheme}://{parsed.netloc}"    
        links = re.findall('''<a\s+(?:[^>]*?\s+)?href="([^"]*)"''', html)    
        for i, link in enumerate(links):    
            if not urlparse(link).netloc:    
                link_with_base = base + link    
                links[i] = link_with_base    

        return set(filter(lambda x: 'mailto' not in x, links))    

    def extract_info(self, url):    
        html = self.get_html(url)    
        meta = re.findall("<meta .*?name=[\"'](.*?)['\"].*?content=[\"'](.*?)['\"].*?>", html)    
        return dict(meta)    
    
    @enforce_time_remaining
    def crawl(self, url, **kwargs):    
        for link in self.get_links(url):    
            if link in self.visited:    
                continue    
            self.visited.add(link)    
            # info = self.extract_info(link)

#             print(f"""Link: {link}    
# Description: {info.get('description')}    
# Keywords: {info.get('keywords')}    
#             """)    

            # Delay request rate by 1s
            time.sleep(1)
            self.crawl(link, **kwargs)    

    @enforce_time_remaining
    def start(self, **kwargs):    
        self.crawl(self.starting_url, **kwargs)    