import requests

# 测试API
url = "http://localhost:8000/api/v1/calculate/range"
data = {
    "route_id": "test",
    "start": 0,
    "end": 500,
    "interval": 100
}

try:
    r = requests.post(url, json=data, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Error: {e}")
