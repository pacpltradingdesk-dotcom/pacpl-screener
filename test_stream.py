
import requests
import json
import time

def test_stream():
    url = "http://127.0.0.1:5000/api/scan/stream"
    print(f"Connecting to {url}...")
    
    try:
        with requests.get(url, stream=True) as response:
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                return

            print("Connected! Listening for events...")
            
            count = 0
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        json_str = decoded_line[6:]
                        try:
                            data = json.loads(json_str)
                            if data.get('type') == 'progress':
                                count += 1
                                if count % 10 == 0:
                                    print(f"Progress: {data.get('scanned')}/{data.get('total')}")
                            elif data.get('type') == 'signal':
                                print(f"SIGNAL FOUND: {data.get('data', {}).get('name')}")
                            elif data.get('type') == 'done':
                                print("Scan Complete!")
                                break
                        except json.JSONDecodeError:
                            print(f"Invalid JSON: {json_str}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_stream()
