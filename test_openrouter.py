import requests
import json

api_key = "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"
url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/cursor",
    "X-Title": "Word Guess Contest AI"
}

data = {
    "model": "mistralai/mistral-small-24b-instruct-2501:free",
    "messages": [
        {
            "role": "system",
            "content": "You are a word game assistant. Respond with exactly one 5-letter word related to the requested category. No explanations, no additional text, just the word in lowercase."
        },
        {
            "role": "user",
            "content": "I need a 5-letter word that is an animal."
        }
    ],
    "max_tokens": 10,  # Reducing token limit since we only need one word
    "temperature": 0.7,  # Adding some randomness
    "top_p": 0.9  # Focusing on more likely responses
}

response = requests.post(url, headers=headers, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
print(f"Response Body: {json.dumps(response.json(), indent=2)}") 