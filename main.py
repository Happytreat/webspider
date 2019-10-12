import psycopg2
from psycopg2 import pool
from concurrent.futures import ThreadPoolExecutor, as_completed
from time_enforced_crawler import PyCrawler
from time_enforcer import TimeRemainingExpired
import time
import urllib.request

EXPIRE_TIME = 5
START_URL = 'https://melodiessim.netlify.com'

def d(s):
    for i in range(10):
        time.sleep(0.1)
        print(s + str(i))


if __name__ == "__main__":  
    # TODO: Connect to postgres db hosted on heroku
    # Psycopg is level 2 thread safe
    try:
        threaded_postgreSQL_pool = pool.ThreadedConnectionPool(
                                    1,
                                    10, 
                                    user = "melodies",
                                    password = "postgres",
                                    host = "127.0.0.1",
                                    port = "5432",
                                    database = "sequeltest")

        print("[INFO] Postgres connection pool created successfully")

        
        print("[INFO] Postgres initialising...")

        # Use getconn() method to Get Connection from connection pool
        ps_connection  = threaded_postgreSQL_pool.getconn()
        if(ps_connection):
            ps_cursor = ps_connection.cursor()
            # Delete table if exists
            ps_cursor.execute("drop table websites;")
            print('[INFO] Deleted websites table')
            # table_exists = ps_cursor.fetchone()[0]
            # if table_exists:
            #     ps_cursor.execute("drop table websites;")
            #     print('[INFO] Deleted websites table')

            ps_cursor.execute("create table websites(url VARCHAR (3000) PRIMARY KEY, responseTime NUMERIC UNIQUE NOT NULL);")
            print('[INFO] Created websites table')
            ps_connection.commit()
            ps_cursor.close()

        # Run crawler
        crawler = PyCrawler(START_URL, threaded_postgreSQL_pool)
        print("[INFO] Starting to crawl from " + START_URL)

        # URLS = ['http://www.foxnews.com/',
        #         'http://www.cnn.com/',
        #         'http://europe.wsj.com/',
        #         'http://www.bbc.co.uk/',
        #         'http://some-made-up-domain.com/']

        # # Retrieve a single page and report the URL and contents
        # def load_url(url, timeout):
        #     with urllib.request.urlopen(url, timeout=timeout) as conn:
        #         return conn.read()

        # # We can use a with statement to ensure threads are cleaned up promptly
        # with ThreadPoolExecutor(max_workers=5) as executor:
        #     # Start the load operations and mark each future with its URL
        #     future_to_url = {executor.submit(load_url, url, 60): url for url in URLS}
        #     for future in as_completed(future_to_url):
        #         url = future_to_url[future]
        #         try:
        #             data = future.result()
        #         except Exception as exc:
        #             print('%r generated an exception: %s' % (url, exc))
        #         else:
        #             print('%r page is %d bytes' % (url, len(data)))

        try:
            crawler.start(time_remaining=EXPIRE_TIME) # alter time_remaining to allow crawler to run for max time_remaining secs
        except TimeRemainingExpired:
            print('[INFO] Time has expired. Killing crawlers...')

    except (Exception, psycopg2.DatabaseError) as error :
        print ("[ERROR] Error connecting to PostgreSQL: ", error)
    finally:
        #closing database threaded pool connection.
            if(threaded_postgreSQL_pool):
                threaded_postgreSQL_pool.closeall()
                print("[INFO] PostgreSQL threaded_postgreSQL_pool closed")