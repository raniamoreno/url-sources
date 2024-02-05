from openai.openai_object import OpenAIObject
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
        # Fetch the HTML content of the URL
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        html_content = response.text
        
        # Use BeautifulSoup to extract the page title for accuracy
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "Title Not Found"
        
        # Construct the prompt for the Chat Completion API
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Given the URL '{url}', with the title '{title}', extract and format the website name, article title, and publication date in the following format: URL, Title, Website Name, Publication Date."}
        ]
        
        # Use the Chat Completions API to process the prompt
        completion = client.chat_completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=150
        )
        
        # Extract the assistant's response from the completion
        if isinstance(completion, OpenAIObject):
            completion = completion.get('choices', [{}])[0].get('message', {'content': ''}).get('content', '').strip()
        else:  # Fallback in case the response structure is not as expected
            completion = "Failed to parse the response correctly."
        
        return completion

    except requests.RequestException as e:
        return f"Error fetching the page: {e}"
    except Exception as e:
        return f"Error processing the request: {e}"