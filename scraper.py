from flask import Flask, request, render_template_string
import requests
import openai
from bs4 import BeautifulSoup

openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)

HTML_FORM = """
<form action="/" method="post">
  URL: <input type="text" name="url">
  <input type="submit" value="Fetch and Parse">
</form>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        parsed_content = fetch_and_parse_content(url)
        return f"{HTML_FORM}<br><pre>{parsed_content}</pre>"
    return HTML_FORM

def fetch_and_parse_content(url):
    try:
        # Fetch the HTML content
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP request errors
        html_content = response.text

        # Extract the title using BeautifulSoup for accuracy
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "Title Not Found"
        
        # Construct a more specific prompt for OpenAI
        prompt = f"Given the URL '{url}', with the title '{title}', extract and format the website name, article title, and publication date in the following format: URL, Title, Website Name, Publication Date."
        
        # Send the prompt to the OpenAI API
        response = openai.Completion.create(
            engine="text-davinci-003",  # Replace with the latest model if necessary
            prompt=prompt,
            temperature=0.5,
            max_tokens=150,  # Adjusted to allow for a potentially longer response
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        # Process the API response to match your desired output format
        # This step assumes the model's response will be in a structured format that you need to parse
        parsed_response = response.choices[0].text.strip()
        # Additional processing can be done here to format the response as desired
        
        return parsed_response

    except requests.RequestException as e:
        return f"Error fetching the page: {e}"
    except Exception as e:
        return f"Error processing the request: {e}"


if __name__ == '__main__':
    app.run(debug=True)
