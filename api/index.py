import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
from openai import OpenAI

# Instantiate the OpenAI client with your API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        # Display the form
        html_form = """
        <html>
        <body>
        <form action="/" method="post">
          URL: <input type="text" name="url">
          <input type="submit" value="Fetch and Parse">
        </form>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_form.encode())

    def do_POST(self):
        # Parse posted data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_data = parse_qs(post_data)
        url = parsed_data.get('url', [None])[0]

        if url:
            try:
                parsed_content = fetch_and_parse_content(url)
                response_message = f"<pre>{parsed_content}</pre>"
            except Exception as e:
                response_message = f"Error processing the request: {e}"
        else:
            response_message = "URL not provided."
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(response_message.encode())

def fetch_and_parse_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP request errors
        html_content = response.text
    except requests.RequestException as e:
        # If requests encounters an HTTP error
        return f"Error fetching the page with requests: {e}"

    try:
        if "robot" in html_content.lower() or not html_content:
            raise ValueError("Robot check detected or empty response, using Selenium as a fallback.")
    except ValueError as e:
        # Fallback to Selenium for complex bot protection or empty response from requests
        try:
            options = Options()
            options.headless = True
            options.add_argument("--window-size=1920,1080")
            options.add_argument(f"user-agent={headers['User-Agent']}")
            
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
            html_content = driver.page_source
            driver.quit()
        except Exception as selenium_error:
            return f"Error fetching the page with Selenium: {selenium_error}"

    try:
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "Title Not Found"
        
        # Construct the prompt for the Chat Completion API
        prompt = f"Format the URL '{url}', the title '{title}', and extract the website name and publication date into a single line in the format: 'URL Title, Website Name Publication Date'."
        
        # Use the instantiated client to send the prompt
        completion = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=0.5,
            max_tokens=150
        )
        
        # Extract the assistant's response from the completion
        parsed_response = completion.choices[0].text.strip()
        
        return parsed_response
    except Exception as e:
        return f"Error processing the content or OpenAI API call: {e}"
