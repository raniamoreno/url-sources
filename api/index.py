import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
import random  # For user-agent rotation

# Instantiate the OpenAI client with your API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Define a list of user-agents to rotate through
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    # Add more user-agents as needed
]

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
    # Display the form with AJAX for asynchronous submission, input clearing, centered styling, and text wrapping
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
                font-family: Arial, sans-serif; /* Improves readability */
            }
            form, #result {
                text-align: center;
                margin: 10px;
                width: 80%; /* Adjusts form width, ensuring it's not too wide */
                max-width: 600px; /* Ensures elements don't become too wide on larger screens */
            }
            input[type="text"] {
                width: 100%; /* Makes input field take full width of its parent */
                padding: 10px;
                margin: 10px 0; /* Spacing around the input field */
            }
            #result {
                text-align: left; /* Aligns result text to the left for readability */
                word-wrap: break-word; /* Ensures long words can break and wrap to the next line */
            }
            pre {
                white-space: pre-wrap; /* Allows pre-formatted text to wrap */
                word-break: break-word; /* Ensures words break and wrap correctly */
                max-width: 100%; /* Prevents the pre element from overflowing its container */
            }
            #copyButton {
                margin-top: 10px; /* Spacing above the button */
                cursor: pointer; /* Changes cursor to pointer to indicate button */
            }
        </style>
        <script>
            function fetchContent() {
                var xhr = new XMLHttpRequest();
                var urlField = document.getElementById('url');
                var url = urlField.value;
                xhr.open("POST", "/", true);
                xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4 && xhr.status === 200) {
                        updateResult(this.responseText);
                        urlField.value = ''; // Clear the input field after displaying the result
                    }
                };
                xhr.send("url=" + encodeURIComponent(url));
                return false; // Prevent default form submission
            }

            function updateResult(text) {
                var resultDiv = document.getElementById('result');
                resultDiv.innerHTML = ''; // Clear previous content
                var pre = document.createElement('pre');
                pre.textContent = text; // Insert text content, preserving formatting
                resultDiv.appendChild(pre); // Add the pre element to the result div

                var copyBtn = document.getElementById('copyButton') || document.createElement('button');
                copyBtn.textContent = 'Copy Result';
                copyBtn.id = 'copyButton';
                copyBtn.onclick = function() {
                    navigator.clipboard.writeText(pre.textContent); // Copy text content to clipboard
                };
                resultDiv.appendChild(copyBtn); // Add the copy button to the result div
            }
        </script>
    </head>
    <body>
        <form onsubmit="return fetchContent();">
            URL: <input type="text" id="url" name="url">
            <input type="submit" value="Fetch and Parse">
        </form>
        <div id="result">
            <!-- The result and "Copy Result" button will be dynamically inserted here -->
        </div>
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
            response_message = f"{parsed_content}"
        else:
            response_message = "URL not provided."
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(response_message.encode())


def fetch_and_parse_content(url):
    # Rotate user-agent for each request
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    
    # Use session for maintaining cookies and state across requests
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        response = session.get(url)
        response.raise_for_status()  # Checks for HTTP request errors
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
