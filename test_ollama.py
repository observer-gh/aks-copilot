import requests
import json

# --- Configuration ---
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "phi3"  # Change this to a model you have downloaded, e.g., "llama3"
PROMPT = "Why is the sky blue?"
# -------------------

payload = {
    "model": MODEL_NAME,
    "prompt": PROMPT,
    "stream": False  # Set to False to get the full response at once
}

print(f"▶️  Sending request to Ollama at {OLLAMA_URL}...")
print(f"▶️  Model: {MODEL_NAME}")
print(f"▶️  Prompt: {PROMPT}")

try:
    # Send the POST request
    response = requests.post(OLLAMA_URL, json=payload, timeout=60)

    # Check if the request was successful
    if response.status_code == 200:
        print("\n✅ Success! Ollama responded.")

        # Parse the JSON response
        response_data = response.json()

        print("\n--- Full Response ---")
        print(json.dumps(response_data, indent=2))

        print("\n--- Generated Answer ---")
        print(response_data.get("response",
              "No 'response' key found in the JSON output."))

    else:
        print(f"\n❌ Error: Received status code {response.status_code}")
        print("--- Error Details ---")
        print(response.text)

except requests.exceptions.ConnectionError as e:
    print(f"\n❌ Connection Error: Could not connect to {OLLAMA_URL}.")
    print("   Please ensure the Ollama server is running and accessible at that address.")
    print(f"   Details: {e}")

except requests.exceptions.RequestException as e:
    print(f"\n❌ An unexpected error occurred: {e}")
