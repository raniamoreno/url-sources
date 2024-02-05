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
        # Display the form with AJAX for asynchronous submission and input clearing
        html_form = """
        <html>
<head>
    <title>Web Parser</title>
    <script>
    function fetchContent() {
        var xhr = new XMLHttpRequest();
        var urlField = document.getElementById('url');
        xhr.open("POST", "/", true);
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var resultContent = document.getElementById('resultContent');
                resultContent.textContent = this.responseText; // Sets the response text
                urlField.value = ''; // Clears the input field

                var copyBtn = document.getElementById('copyButton') || createCopyButton();
                copyBtn.onclick = function() {
                    navigator.clipboard.writeText(resultContent.textContent).then(function() {
                        console.log('Result copied to clipboard!');
                    }, function(err) {
                        console.error('Could not copy text:', err);
                    });
                };
            }
        };
        var data = "url=" + encodeURIComponent(urlField.value);
        xhr.send(data);
        return false; // Prevents default form submission
    }

    function createCopyButton() {
        var copyBtn = document.createElement('button');
        copyBtn.textContent = 'Copy Result';
        copyBtn.id = 'copyButton';
        document.getElementById('result').appendChild(copyBtn);
        return copyBtn;
    }
    </script>
</head>
<body>
    <form onsubmit="return fetchContent();">
        URL: <input type="text" id="url" name="url">
        <input type="submit" value="Fetch and Parse">
    </form>
    <div id="result">
        <pre id="resultContent"></pre>
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
            response_message = f"<pre>{parsed_content}</pre>"
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
