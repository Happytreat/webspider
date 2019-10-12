import requests    
import re    
from urllib.parse import urlparse   
import time 
import psycopg2

class TimeRemainingExpired(Exception):
    pass

# Set time limit to crawling
def enforce_time_remaining(f):
    """ decorator to check time remaining and raise if expired """
    def new_f(*args, **kwargs):
        if kwargs.get('_time_remaining_end_time') is None:
            kwargs['_time_remaining_end_time'] = \
                time.time() + kwargs['time_remaining']
            #print(kwargs['_time_remaining_end_time'])
            #print(kwargs['time_remaining'])
        if time.time() >= kwargs['_time_remaining_end_time']:
            raise TimeRemainingExpired
        return f(*args, **kwargs)

    return new_f


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
        print("Time taken for response: " + str(html.elapsed.total_seconds()) + "\nLink: " + url + "\n")     
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


if __name__ == "__main__":  
    # Connect to Postgres db with ACID properties 
    try:
        connection = psycopg2.connect(user = "melodies",
                                    password = "postgres",
                                    host = "127.0.0.1",
                                    port = "5432",
                                    database = "sequeltest")

        cursor = connection.cursor()
        # Print PostgreSQL Connection properties
        print ( connection.get_dsn_parameters(),"\n")

        # Print PostgreSQL version
        cursor.execute("SELECT version();")
        record = cursor.fetchone()
        print("You are connected to - ", record,"\n")

        # Run crawler
        crawler = PyCrawler("https://melodiessim.netlify.com")

        try:
            crawler.start(time_remaining=5) # alter time_remaining to allow crawler to run for max time_remaining secs
        except TimeRemainingExpired:
            print('Time Expired')

    except (Exception, psycopg2.Error) as error :
        print ("Error while connecting to PostgreSQL", error)
    finally:
        #closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")