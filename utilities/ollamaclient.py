

# 🔧 Example Modular Code Split (Optional but GOOD)

## `utils/ollama_client.py`

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

def stream_ollama(prompt, model):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }

    res = requests.post(OLLAMA_URL, json=payload, stream=True)

    for line in res.iter_lines():
        if line:
            data = json.loads(line.decode())
            yield data.get("response", "")