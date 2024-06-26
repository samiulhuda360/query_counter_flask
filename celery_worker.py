import requests
from bs4 import BeautifulSoup
import time
import sqlite3
from celery import Celery
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

app = Celery('tasks', broker='redis://redis:6379', backend='redis://redis:6379', broker_connection_retry_on_startup=True)

proxies = {
    "http": "http://letezcbn-rotate:6792gwkuo8oo@p.webshare.io:80/",
    "https": "http://letezcbn-rotate:6792gwkuo8oo@p.webshare.io:80/"
}

def get_db_connection():
    conn = sqlite3.connect('scraping_results.db')
    return conn
@app.task(bind=True)
def scrape_website(self, sl_no, url, keyword):
    try:
        with requests.Session() as session:
            response = session.get(url, proxies=proxies)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            h1_count = sum(keyword.lower() in h1.get_text().lower() for h1 in soup.find_all('h1'))
            h2_count = sum(keyword.lower() in h2.get_text().lower() for h2 in soup.find_all('h2'))
            body_count = soup.get_text().lower().count(keyword.lower())

            # Save the scraping results to the database
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('INSERT INTO results (sl_no, url, keyword, h1_count, h2_count, body_count) VALUES (?, ?, ?, ?, ?, ?)',
                      (sl_no, url, keyword, str(h1_count), str(h2_count), str(body_count)))
            conn.commit()
            conn.close()

            return sl_no, h1_count, h2_count, body_count
    except Exception as e:
        print(f"Error occurred while scraping the website: {e}")
        # Skip the task and continue with the next one
        return sl_no, '?', '?', '?'