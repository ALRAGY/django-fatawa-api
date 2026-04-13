import os
import sys
import requests
import concurrent.futures
import time
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatawa_api.settings')
django.setup()

URL = "http://localhost:8000/api/auth/roles/"

def fetch_url(token):
    headers = {'Authorization': f'Bearer {token}'}
    start = time.time()
    try:
        res = requests.get(URL, headers=headers)
        return res.status_code, time.time() - start
    except Exception as e:
        return str(e), time.time() - start

def get_token():
    try:
        from accounts.models import User
        # Ensure a robust user exists for load testing
        user, created = User.objects.get_or_create(username='load_tester', defaults={'email': 'load@local.com'})
        user.set_password('LoadTest2026!')
        user.save()

        res = requests.post("http://localhost:8000/api/auth/users/login/", json={
            "username": "load_tester",
            "password": "LoadTest2026!"
        })
        return res.json().get('access')
    except Exception as e:
        print(f"Failed to get token: {e}")
        return None

def run_load_test():
    print("--- 🚀 STARTING LOAD TEST ---")
    token = get_token()
    if not token:
        print("Could not obtain auth token. Exiting.")
        return

    n_requests = 100
    print(f"Sending {n_requests} concurrent requests to {URL}...")
    
    start_time = time.time()
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch_url, token) for _ in range(n_requests)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r[0] == 200)
    failed_count = n_requests - success_count
    times = [r[1] for r in results]
    avg_time = sum(times) / len(times) if times else 0

    print("\n--- 🏁 LOAD TEST RESULTS ---")
    print(f"Total Requests: {n_requests}")
    print(f"Total Time Taken: {total_time:.2f} seconds")
    print(f"Successful Requests (200 OK): {success_count}")
    print(f"Failed Requests: {failed_count}")
    print(f"Average Latency: {avg_time:.4f} seconds/req")
    print(f"Requests per Second: {n_requests/total_time:.2f} req/s")

if __name__ == "__main__":
    run_load_test()
