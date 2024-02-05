from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
import os
import requests
from bs4 import BeautifulSoup
import openai

# Initialize OpenAI client with the API key
openai.api_key = os.getenv('OPENAI_API_KEY')

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
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
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
        
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "Title Not Found"
        
        prompt = f"Given the URL '{url}', with the title '{title}', extract and format the website name, article title, and publication date in the following format: URL, Title, Website Name, Publication Date."
        
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Adjust the model as needed
            messages=[{"role": "system", "content": "Extract information."},
                      {"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=150
        )
        
        # Assuming the first choice's text is the desired output
        parsed_response = completion.choices[0].message['content'].strip()
        
        return parsed_response

    except requests.RequestException as e:
        return f"Error fetching the page: {e}"
    except Exception as e:
        return f"Error processing the request: {e}"

