import requests

try:
    response = requests.post("http://127.0.0.1:5000/chat", json={"message": "test", "context": {}})
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Response Body: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
