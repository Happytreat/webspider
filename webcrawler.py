import psycopg2
from psycopg2 import pool
from py_crawler import PyCrawler
from time_enforcer import TimeRemainingExpired

EXPIRE_TIME = 5
START_URL = 'https://melodiessim.netlify.com'


if __name__ == "__main__":  
    # TODO: Connect to postgres db hosted on heroku
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

        # Purge all data in db
        print("[INFO] Postgres initialising...")

        # Use getconn() method to Get Connection from connection pool
        ps_connection  = threaded_postgreSQL_pool.getconn()

        # Run crawler
        crawler = PyCrawler(START_URL)
        print("[INFO] Starting to crawl from " + START_URL)

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