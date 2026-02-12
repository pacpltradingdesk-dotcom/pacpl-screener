
import requests
import json
import time

def test_sse():
    url = "http://127.0.0.1:5000/api/test/stream"
    print(f"Connecting to {url}...")
    
    try:
        with requests.get(url, stream=True) as response:
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                return

            print("Connected! Listening for numbers...")
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        print(f"Received: {decoded_line}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_sse()
