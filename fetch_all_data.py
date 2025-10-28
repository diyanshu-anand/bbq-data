import requests, json, time
from datetime import datetime, timedelta

URL = "https://www.barbequenation.com/api/v1/menu-buffet-price"
HEADERS = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

# --- Replace this with your actual branches_config ---
branches_config = {
    "14": {
        "name": "Koramangala",
        "slots": {
            "12:00:00": 1105, "12:30:00": 1105, "13:00:00": 1105,
            "13:30:00": 1105, "14:00:00": 1105
        },
    },
    "133": {
        "name": "Indiranagar",
        "slots": {
            "12:00:00": 2205, "12:30:00": 2205, "13:00:00": 2205,
            "13:30:00": 2205, "14:00:00": 2205
        },
    },
}

def safe_post(payload, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(URL, json=payload, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"Retry {attempt+1} failed: {e}")
        time.sleep(2)
    return None

def fetch_all():
    results = []
    for branch_id, info in branches_config.items():
        branch_name = info["name"]
        for offset in range(1):  # just today
            date_str = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
            for time_str, slot_id in info["slots"].items():
                payload = {
                    "branch_id": branch_id,
                    "reservation_date": date_str,
                    "reservation_time": time_str,
                    "slot_id": slot_id
                }
                data = safe_post(payload)
                if not data:
                    results.append({
                        "Branch": branch_name,
                        "Branch ID": branch_id,
                        "Date": date_str,
                        "Slot Time": time_str,
                        "Error": "Failed to fetch"
                    })
                    continue

                buffets = data.get("results", {}).get("buffets", {}).get("buffet_data", [])
                if not buffets:
                    results.append({
                        "Branch": branch_name,
                        "Branch ID": branch_id,
                        "Date": date_str,
                        "Slot Time": time_str,
                        "Error": "No buffet data"
                    })
                    continue

                for b in buffets:
                    results.append({
                        "Branch": branch_name,
                        "Branch ID": branch_id,
                        "Date": date_str,
                        "Slot Time": time_str,
                        "Period": b.get("period", {}).get("periodName", ""),
                        "Customer Type": b.get("customerType", ""),
                        "Food Type": b.get("foodType", ""),
                        "Plan": b.get("displayName", ""),
                        "Price": b.get("totalAmount", ""),
                        "Original Price": b.get("originalPrice", ""),
                    })

                time.sleep(0.2)  # gentle delay
    return results

if __name__ == "__main__":
    print("Fetching data...")
    all_data = fetch_all()
    with open("buffet_data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(all_data)} records at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
