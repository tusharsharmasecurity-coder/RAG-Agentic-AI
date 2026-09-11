import requests
import time

API_URL = "http://127.0.0.1:8000/ask"

# Mix of SQL, RAG, Chat, and explicit duplicates to test the Cache
TEST_QUESTIONS = [
    "hello",
    "Show me total shipments",            # Run 1: Cold start (Slow)
    "Show me total shipments",            # Run 2: CACHE HIT (Fast)
    "damage sop",                         # Run 1: Cold start (Slow)
    "damage sop",                         # Run 2: CACHE HIT (Fast)
    "count of awb by warehouse",
    "explain closure process",
    "top 10 delayed shipments",
    "how many shipments were delivered?",
    "what is the policy for wrong product?",
]

def run_test():
    print(f"{'Question':<40} | {'Intent':<10} | {'Time (s)':<10}")
    print("-" * 65)
    
    for q in TEST_QUESTIONS:
        try:
            start = time.time()
            response = requests.post(
                API_URL, 
                json={"question": q, "thread_id": "stress_test"}, 
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                intent = data.get("intent", "UNKNOWN")
                exec_time = data.get("execution_time", 0.0)
                print(f"{q:<40} | {intent:<10} | {exec_time:<10.3f}")
            else:
                print(f"{q:<40} | {'ERROR':<10} | {response.status_code}")
                
        except Exception as e:
            print(f"{q:<40} | {'CRASH':<10} | {str(e)}")

if __name__ == "__main__":
    run_test()