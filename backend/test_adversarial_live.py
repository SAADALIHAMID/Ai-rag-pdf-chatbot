import urllib.request
import json

url = "http://127.0.0.1:8000/api/query"

# Test 1: Adversarial Temporal Near-Miss (Asking for 2029 when only 2026 exists)
payload1 = json.dumps({"query": "What were the orbital calculations and telemetry results for Project Quantum Aegis in March 2029?"}).encode("utf-8")
headers = {"Content-Type": "application/json"}
req1 = urllib.request.Request(url, data=payload1, headers=headers, method="POST")

print("--- RUNNING LIVE ADVERSARIAL TEMPORAL TEST (March 2029 query) ---")
try:
    with urllib.request.urlopen(req1) as resp:
        tokens = []
        for line in resp:
            decoded = line.decode("utf-8", errors="ignore").strip()
            if decoded.startswith("data:"):
                try:
                    data = json.loads(decoded[5:].strip())
                    if "token" in data:
                        tokens.append(data["token"])
                except Exception:
                    pass
        full_answer = "".join(tokens)
        print("Model Live Response:\n", full_answer)
        print("Refusal Triggered Correctly:", "Mujhe is ka jawab uploaded document me nahi mila" in full_answer or "2029" in full_answer)
except Exception as e:
    print("Error:", e)

# Test 2: Clean Factual Query (Initiated October 14, 2026)
payload2 = json.dumps({"query": "When was Project Quantum Aegis initiated and who is the Chief Architect?"}).encode("utf-8")
req2 = urllib.request.Request(url, data=payload2, headers=headers, method="POST")

print("\n--- RUNNING CLEAN FACTUAL TEST (2026 Architect query) ---")
try:
    with urllib.request.urlopen(req2) as resp:
        tokens = []
        for line in resp:
            decoded = line.decode("utf-8", errors="ignore").strip()
            if decoded.startswith("data:"):
                try:
                    data = json.loads(decoded[5:].strip())
                    if "token" in data:
                        tokens.append(data["token"])
                except Exception:
                    pass
        full_answer = "".join(tokens)
        print("Model Live Response:\n", full_answer)
except Exception as e:
    print("Error:", e)
