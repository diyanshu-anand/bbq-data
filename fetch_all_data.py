import requests
import json
import time
from datetime import datetime, timedelta

# --- API Config ---
URL = "https://www.barbequenation.com/api/v1/menu-buffet-price"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# --- Branches Config ---
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
    # TODO: add other branches here up to 48 total
}


# --- Safe POST with exponential backoff ---
def safe_post(payload, retries=3, backoff=2):
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(URL, json=payload, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.json()
            else:
                print(f"[{attempt}/{retries}] HTTP {r.status_code} for {payload['branch_id']} at {payload['reservation_time']}")
        except Exception as e:
            print(f"[{attempt}/{retries}] Exception: {e}")
        time.sleep(backoff * attempt)  # exponential backoff (2s, 4s, 6s)
    return None


# --- Main Fetch Function ---
def fetch_all():
    results = []
    total_calls = 0

    for branch_id, info in branches_config.items():
        branch_name = info["name"]
        print(f"\n🔹 Fetching data for: {branch_name} (ID: {branch_id})")

        for offset in range(1):  # Only today
            date_str = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")

            for time_str, slot_id in info["slots"].items():
                payload = {
                    "branch_id": branch_id,
                    "reservation_date": date_str,
                    "reservation_time": time_str,
                    "slot_id": slot_id
                }

                data = safe_post(payload)
                total_calls += 1

                if not data:
                    results.append({
                        "Branch": branch_name,
                        "Branch ID": branch_id,
                        "Date": date_str,
                        "Slot Time": time_str,
                        "Error": "Failed to fetch"
                    })
                    continue

                buffets = (
                    data.get("results", {})
                    .get("buffets", {})
                    .get("buffet_data", [])
                )

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

                time.sleep(1.2)  # gentle delay between slots

        print(f"✅ Completed {branch_name}")

        # Delay between branches to avoid overload
        time.sleep(4)

    print(f"\nTotal API Calls Made: {total_calls}")
    return results


# --- Run Script ---
if __name__ == "__main__":
    print(f"\n=== BBQ Nation Data Fetch Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    all_data = fetch_all()
    with open("buffet_data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(all_data)} records at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
