import concurrent.futures
import json
import numpy as np
import requests
from flask import Flask, render_template
from bs4 import BeautifulSoup
import trafilatura

app = Flask(__name__)

@app.route("/")
def index():
    return "Index Page and stuff"

def extract_text_from_single_web_page(url):
    """
    Extract text from a web page using Trafilatura or BeautifulSoup.
    """
    downloaded_url = trafilatura.fetch_url(url)

    def extract_with_trafilatura(downloaded_url):
        try:
            extracted_data = trafilatura.extract(downloaded_url, output_format='json', with_metadata=True, include_comments=False,
                                    date_extraction_params={'extensive_search': True, 'original_date': True})
        except AttributeError:
            extracted_data = trafilatura.extract(downloaded_url, output_format='json', with_metadata=True,
                                    date_extraction_params={'extensive_search': True, 'original_date': True})
        if extracted_data:
            json_output = json.loads(extracted_data)
            return json_output['text']
        else:
            return None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(extract_with_trafilatura, downloaded_url)
        extracted_text = future.result()

    if extracted_text is None:
        try:
            resp = requests.get(url)
            # We will only extract the text from successful requests:
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                text = soup.find_all(text=True)
                blacklist = ['[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script', 'style']
                cleaned_text = ' '.join(item for item in text if item.parent.name not in blacklist).replace('\t', '')
                return cleaned_text.strip()
            else:
                # This line will handle for any failures in both the Trafilature and BeautifulSoup4 functions:
                return np.nan
        # Handling for any URLs that don't have the correct protocol
        except requests.exceptions.MissingSchema:
            return np.nan

    return extracted_text


@app.route('/url', methods=['POST', 'GET'])
def user_request():

    user_url = 'https://en.wikipedia.org/wiki/South_China_Sea'

    _text = extract_text_from_single_web_page(user_url)

    # split the text into paragraphs
    paragraphs = str(_text).split("\n")

    return render_template('./templates/url.html', content=paragraphs)

if __name__ == '__main__':
    app.run()
