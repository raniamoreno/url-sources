import os
import openai

# Setup your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Use the `Completion` class for making a request
response = openai.Completion.create(
  engine="text-davinci-003",  # Make sure to use an engine compatible with your SDK version
  prompt="This is a test prompt.",
  max_tokens=50
)

print(response.choices[0].text)
