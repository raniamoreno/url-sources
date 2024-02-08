import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import random

# Instantiate the OpenAI client with your API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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
            /* CSS Styles */
        </style>
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
                xhr.send("url=" + encodeURIComponent(urls)); // Sends the entire textarea content
                return false; // Prevents default form submission
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
    </head>
    <body>
        <!-- HTML Form -->
    </body>
    </html>
        """
        # Send the HTML form
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

def fetch_and_parse_content(url):
    # Function to fetch and parse content for each URL
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        response = session.get(url)
        response.raise_for_status()
        html_content = response.text
        
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "Title Not Found"
        
        prompt = f"Format the URL '{url}', the title '{title}', and extract the website name and publication date into a single line in the exact format: URL Title, Website Name Publication Date."
        completion = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=0.5,
            max_tokens=150
        )
        
        parsed_response = completion.choices[0].text.strip()
        
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
