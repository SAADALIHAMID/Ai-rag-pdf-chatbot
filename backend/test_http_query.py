import urllib.request
import urllib.error
import json

url = "http://127.0.0.1:8000/api/query"
payload = json.dumps({"query": "What is Quantum Aegis?"}).encode("utf-8")
headers = {"Content-Type": "application/json"}

req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

try:
    with urllib.request.urlopen(req) as resp:
        print("HTTP Status:", resp.status)
        for i in range(10):
            line = resp.readline()
            if not line:
                break
            print("Line:", line.decode("utf-8", errors="ignore").strip())
except urllib.error.HTTPError as e:
    print("HTTPError Status:", e.code)
    print("HTTPError Reason:", e.reason)
    print("HTTPError Body:", e.read().decode("utf-8", errors="ignore"))
except Exception as ex:
    print("Exception:", type(ex), ex)
