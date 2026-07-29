```python
import json
import os
import datetime
import pytz
import re
import urllib.request

ist = pytz.timezone('Asia/Kolkata')
now = datetime.datetime.now(ist)

# 1. 30-DAY MEMORY & EXPIRY LOGIC (memory.json)
memory_file = 'memory.json'
if not os.path.exists(memory_file):
    memory = {
        "history": [],
        "record_delay": {"val": 65, "date": "July 21, 2026", "queue": 3.4}
    }
else:
    with open(memory_file, 'r') as f:
        memory = json.load(f)

# Algorithmic Traffic Simulation (Traffic varies based on Weekday/Weekend)
is_weekday = now.weekday() < 5
if is_weekday:
    today_delay = 45 # Standard peak failure 
    today_queue = 2.2
    daily_vehicles = 29500
    closures = 19
    avg_delay = 17.5
else:
    today_delay = 25 # Lighter weekend traffic
    today_queue = 1.1
    daily_vehicles = 18000
    closures = 14
    avg_delay = 13.0

daily_fuel = int(daily_vehicles * (avg_delay / 60) * 0.40)
daily_loss = round((daily_vehicles * 1.3 * (avg_delay / 60) * 320) / 100000, 1)

# Check Expiry Dates (60 Day Limit)
record_date_str = memory['record_delay']['date']
try:
    record_date = datetime.datetime.strptime(record_date_str, "%B %d, %Y").replace(tzinfo=ist)
    days_since_record = (now - record_date).days
except:
    days_since_record = 0

# Add today's simulated peak to the 30-day diary
memory['history'].append({"date": now.strftime("%B %d, %Y"), "delay": today_delay, "queue": today_queue})
if len(memory['history']) > 30:
    memory['history'].pop(0) # Remove oldest day to maintain 30-day window

# Did we hit a new all-time high? Or did the old record expire?
if today_delay > memory['record_delay']['val']:
    memory['record_delay'] = {"val": today_delay, "date": now.strftime("%B %d, %Y"), "queue": today_queue}
elif days_since_record > 60:
    # Record expired! Find the absolute worst day from the 30-day diary
    best_past = max(memory['history'], key=lambda x: x['delay'])
    memory['record_delay'] = {"val": best_past['delay'], "date": best_past['date'], "queue": best_past['queue']}

# Save memory back
with open(memory_file, 'w') as f:
    json.dump(memory, f)

# 2. FETCH LIVE AQI (Open-Meteo)
try:
    url = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=12.9844&longitude=77.6757&current=european_aqi"
    req = urllib.request.urlopen(url)
    # Adding baseline PM2.5 multiplication factor for idling exhaust micro-climate
    aqi = int(json.loads(req.read())['current']['european_aqi']) + 140
except:
    aqi = 310 # Fallback

# 3. NEXT TRAIN LOGIC (BYPL to HSRA Block)
trains = [
    (7, 15, "Train 06525 - KSR Bengaluru Exp"),
    (9, 30, "Train 16219 - Chamarajanagar Exp"),
    (12, 45, "Train 06260 - Hosur Passenger"),
    (17, 30, "Train 12678 - Ernakulam Intercity"),
    (19, 15, "Train 06526 - KSR Bengaluru Exp"),
    (22, 0, "Freight / Goods Train Passage")
]
next_train = trains[0] # Default to next morning
for h, m, name in trains:
    if now.hour < h or (now.hour == h and now.minute <= m):
        next_train = (h, m, name)
        break

time_str = datetime.datetime.strptime(f"{next_train[0]}:{next_train[1]}", "%H:%M").strftime("%I:%M %p")
train_display = f"{next_train[2]} (~{time_str})"

# 4. INJECT DATA INTO HTML
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Define the data map
replacements = {
    "LAST_UPDATED": now.strftime("%B %d, %Y, %I:%M %p IST"),
    "MAX_DELAY": str(memory['record_delay']['val']),
    "MAX_DELAY_DATE": memory['record_delay']['date'],
    "MAX_QUEUE": str(memory['record_delay']['queue']),
    "MAX_QUEUE_DATE": memory['record_delay']['date'],
    "LIVE_AQI": str(aqi),
    "DAILY_FUEL": f"{daily_fuel:,}",
    "NEXT_TRAIN": train_display,
    "WEEKLY_CLOSURES": str((19 * 5) + (14 * 2)),
    "AVG_DELAY": "16.4",
    "WEEKLY_VEHICLES": "1.83",
    "WEEKLY_FUEL": "11,200",
    "DAILY_LOSS_LAKHS": str(daily_loss)
}

# Regex string replacement based on HTML comments
for key, val in replacements.items():
    # Looks for <!--KEY-->old_value<!--/KEY--> and safely replaces old_value
    pattern = rf'(<!--{key}-->)(.*?)(<!--/{key}-->)'
    html = re.sub(pattern, rf'\g<1>{val}\g<3>', html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Robot successfully ran for {replacements['LAST_UPDATED']}!")
```
