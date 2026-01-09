import requests
import time
import schedule

def ping_backend():
    try:
        response = requests.get('https://your-backend.onrender.com/ping')
        print(f"Backend pinged: {response.status_code}")
    except:
        print("Backend ping failed")

# Ping every 14 minutes to prevent sleep
schedule.every(14).minutes.do(ping_backend)

while True:
    schedule.run_pending()
    time.sleep(60)