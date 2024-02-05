import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

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
        response.raise_for_status()  # Checks for HTTP request errors
        html_content = response.text
        
        # Extract the title using BeautifulSoup for accuracy
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "Title Not Found"
        
        # Construct the prompt for the Chat Completion API
        prompt = f"Given the URL '{url}', with the title '{title}', extract and format the website name, article title, and publication date in the following format: URL, Title, Website Name, Publication Date."

        # Use the instantiated client to send the prompt
        completion = client.completions.create(
            model="gpt-3.5-turbo",  # Adjust the model as needed
            prompt=prompt,
            temperature=0.5,
            max_tokens=150
        )
        
        # Extract the assistant's response from the completion
        parsed_response = completion.choices[0].message['content'].strip()
        
        return parsed_response

    except requests.RequestException as e:
        return f"Error fetching the page: {e}"
    except Exception as e:
        return f"Error processing the request: {e}"
