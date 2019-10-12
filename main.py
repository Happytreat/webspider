import psycopg2
from psycopg2 import pool
from concurrent.futures import ThreadPoolExecutor, as_completed
from time_enforced_crawler import PyCrawler
from time_enforcer import TimeRemainingExpired
import time
import urllib.request

EXPIRE_TIME = 10 # amount of time before automatically kill crawl
NUM_WORKERS = 5 # max number of threads spawn simultaneously

URLS = ['https://melodiessim.netlify.com',
        'https://www.hodlnaut.com/',
        'http://definitelytyped.org/directory/learn.html',
        'http://www.bbc.co.uk/',
        'http://some-made-up-domain.com/']

# Format STDOUT of all links/responseTimes at the end of the program
def formatResult(result):
    print('no.' + '      ' + 'link' + '                                ' + 'response time')
    for i, val in enumerate(result):
        link, response_time = val
        print(str(i) + '        ' + link + '        ' + str(response_time))
    print('\n')    

if __name__ == "__main__":  
    # TODO: Connect to postgres db hosted on heroku
    # Psycopg is level 2 thread safe
    try:
        threaded_postgreSQL_pool = pool.ThreadedConnectionPool(
                                    1,
                                    10, 
                                    user = "ufutlmdalowgfq",
                                    password = "a6a069571a7a58935db7caeb0bba7b62ebb56a4677a610a867c9bf6c11f1b133",
                                    host = "ec2-54-197-238-238.compute-1.amazonaws.com",
                                    port = "5432",
                                    database = "d7b5eg8oinsv4n")

        print("[INFO] Postgres connection pool created successfully")

        print("[INFO] Postgres initialising...")

        # Use getconn() method to Get Connection from connection pool
        ps_connection  = threaded_postgreSQL_pool.getconn()
        if(ps_connection):
            ps_cursor = ps_connection.cursor()
            # Delete table if exists
            ps_cursor.execute("drop table websites;")
            print('[INFO] Deleted websites table')

            ps_cursor.execute("create table websites(url VARCHAR (3000) PRIMARY KEY, responseTime NUMERIC UNIQUE NOT NULL);")
            print('[INFO] Created websites table')
            ps_connection.commit()
            ps_cursor.close()

        def runCrawler(url, threaded_postgreSQL_pool):
            # Run crawler with START_URL
            crawler = PyCrawler(url, threaded_postgreSQL_pool)
            print("[INFO] Starting to crawl from " + url)
            try:
                crawler.start(time_remaining=EXPIRE_TIME) # alter time_remaining to allow crawler to run for max time_remaining secs
            except TimeRemainingExpired:
                print('[EXPIRED] Time has expired. Killing crawlers...')


        # We can use a with statement to ensure threads are cleaned up promptly
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(runCrawler, url, threaded_postgreSQL_pool) for url in URLS}

    except (Exception, psycopg2.DatabaseError) as error :
        print ("[ERROR] Error connecting to PostgreSQL: ", error)
    finally:
        # print out all entries in db
        ps_cursor = ps_connection.cursor()
        ps_cursor.execute("select * from websites;")
        result = ps_cursor.fetchall()
        print("[INFO] Printing all links visited")
        formatResult(result)

        #closing database threaded pool connection.
        if(threaded_postgreSQL_pool):
            threaded_postgreSQL_pool.closeall()
            print("[INFO] PostgreSQL threaded_postgreSQL_pool closed")