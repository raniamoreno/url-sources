import requests
from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import random
from datetime import datetime
import re

# Instantiate the OpenAI client with your API key

# Define a list of user-agents to rotate through
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
]

class Handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        html_form = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Web Parser</title>
        <style>
            body, html {
                height: 100%;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                flex-direction: column;
                font-family: Arial, sans-serif;
            }
            form, #result {
                text-align: center;
                margin: 10px;
                width: 80%;
                max-width: 600px;
            }
            textarea {
                width: 100%;
                padding: 10px;
                margin-bottom: 20px;
            }
            #result {
                text-align: left;
                word-wrap: break-word;
                margin-top: 20px;
            }
            pre {
                white-space: pre-wrap;
                word-break: break-word;
                max-width: 100%;
            }
            button {
                display: inline-block;
                margin-top: 10px;
                padding: 10px 20px;
                cursor: pointer;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                text-align: center;
            }
            input[type="submit"] {
                width: auto;
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <form onsubmit="return fetchContent();">
            URLs (one per line): <textarea id="url" name="url" rows="5"></textarea>
            <input type="submit" value="Fetch and Parse">
        </form>
        <div id="result">
            <!-- The result will be dynamically inserted here -->
        </div>
        <script>
            function fetchContent() {
                var xhr = new XMLHttpRequest();
                var urlField = document.getElementById('url');
                var urls = urlField.value;
                xhr.open("POST", "/", true);
                xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4 && xhr.status === 200) {
                        updateResult(this.responseText);
                    }
                };
                xhr.send("url=" + encodeURIComponent(urls));
                return false;
            }

            function updateResult(text) {
                var resultDiv = document.getElementById('result');
                resultDiv.innerHTML = '<pre>' + text + '</pre>';
                createCopyButton(text);
            }

            function createCopyButton(text) {
                var copyBtn = document.createElement('button');
                copyBtn.textContent = 'Copy Result';
                copyBtn.onclick = function() {
                    navigator.clipboard.writeText(text);
                };
                var resultDiv = document.getElementById('result');
                resultDiv.appendChild(copyBtn);
            }
        </script>
    </body>
    </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_form.encode())


    def do_POST(self):
        # Handle POST request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_data = parse_qs(post_data)
        urls_text = parsed_data.get('url', [None])[0]

        response_messages = []
        if urls_text:
            urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
            for url in urls:
                parsed_content = fetch_and_parse_content(url)
                response_messages.append(f"{url}: {parsed_content}")
            response_message = "<br>".join(response_messages)
        else:
            response_message = "URLs not provided."
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(response_message.encode())

def extract_date(soup):
    # Define patterns to search for within meta tags
    date_patterns = ['article:published_time', 'datePublished', 'pubDate', 'og:published_time']
    for pattern in date_patterns:
        meta_date = soup.find('meta', property=pattern) or soup.find('meta', attrs={"name": pattern})
        if meta_date and meta_date.get('content'):
            return meta_date['content']

    # Fallback to regex search within the page text
    # This pattern matches common date formats, adjust as needed
    date_regex_patterns = [
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',  # Matches YYYY-MM-DD
        r'\b\d{1,2}/\d{1,2}/\d{4}\b'   # Matches DD/MM/YYYY or MM/DD/YYYY
    ]
    for pattern in date_regex_patterns:
        match = re.search(pattern, soup.get_text())
        if match:
            return match.group()

    return None

def fetch_and_parse_content(url):
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        response = session.get(url)
        response.raise_for_status()
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "Title Not Found"
        
        # Extract website name from URL or meta tag
        website_name = re.findall('(?:http[s]?://)?([^/]+)', url)[0] if url else "Website Name Not Found"
        
        # Extract publication date using enhanced extraction logic
        date_str = extract_date(soup)
        if date_str:
            try:
                # Try parsing with known format
                pub_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z').strftime('%d.%m.%Y')
            except ValueError:
                # Fallback for different date format
                try:
                    pub_date = datetime.strptime(date_str, '%d/%m/%Y').strftime('%d.%m.%Y')
                except ValueError:
                    pub_date = "Date format not recognized"
        else:
            pub_date = "Publication Date Not Found"
        
        # Format the output correctly
        parsed_response = f"{url} {title}, {website_name} {pub_date}"
        
        return parsed_response

    except requests.RequestException as e:
        return f"Error fetching the page: {e}"
    except Exception as e:
        return f"Error processing the request: {e}"




if __name__ == "__main__":
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, Handler)
    print("Server running on port 8000...")
    httpd.serve_forever()
