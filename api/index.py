from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

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
            parsed_content = fetch_and_parse_content(url)
            response_message = f"<pre>{parsed_content}</pre>"
        else:
            response_message = "URL not provided."
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(response_message.encode())

def fetch_and_parse_content(url):
    try:
        # Fetch the HTML content
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP request errors
        html_content = response.text
        
        # Extract the title using BeautifulSoup for accuracy
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "Title Not Found"
        
        # Construct the OpenAI prompt
        prompt = f"Given the URL '{url}', with the title '{title}', extract and format the website name, article title, and publication date in the following format: URL, Title, Website Name, Publication Date."
        
        # Send the prompt to the OpenAI API using the new client method
        completion = client.completions.create(
            model="text-davinci-003",  # Use an appropriate model
            prompt=prompt,
            temperature=0.5,
            max_tokens=150,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        # Handling the response with the new API
        # Extracting the first choice's text
        parsed_response = completion.choices[0].text.strip()
        
        return parsed_response

    except requests.RequestException as e:
        return f"Error fetching the page: {e}"
    except Exception as e:
        return f"Error processing the request: {e}"