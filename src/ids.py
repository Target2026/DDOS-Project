import pandas as pd
import os
import subprocess
import time
import random
from river.stream import iter_pandas
from river.ensemble import SRPClassifier
from plyer import notification
import threading
from collections import defaultdict

# ✅ SETTINGS
ALERT_COOLDOWN = 600  # ✅ Increase cooldown to 10 min (Reduce spam)
LIVE_MONITOR_INTERVAL = 30  # ✅ Capture live traffic every 30 sec
ALERT_THRESHOLD = 6  # ✅ Reduce false positives (Increase threshold)
LOG_CLEANUP_INTERVAL = 600  # ✅ Clear logs every 10 min
MAX_RUNTIME = 300  # ✅ Stop IDS after 5 minutes (300 seconds)

last_alert_time = {}  
attack_counts = defaultdict(int)  
attack_log = []  

class IDS:
    def __init__(self, dataset_path):
        if not os.path.exists(dataset_path) or os.stat(dataset_path).st_size == 0:
            print("❌ ERROR: dataset.csv is missing or empty! Please add training data.")
            exit(1)

        df = pd.read_csv(dataset_path)

        if len(df) < 10:
            print(f"⚠️ WARNING: dataset.csv has only {len(df)} samples. Model may not learn properly.")

        features = ['flow_duration', 'byte_count', 'packet_count', 'syn_flag', 'ip_proto']
        self.X = df[features]
        self.y = df['label']
        self.stream = iter_pandas(self.X, self.y)
        self.model = SRPClassifier(n_models=10, seed=42)

        for _ in range(min(50, len(df))):  
            try:
                X_sample, y_sample = next(self.stream)
                self.model.learn_one(X_sample, y_sample)
            except StopIteration:
                print("⚠️ WARNING: Not enough data to train properly.")
                break

    def predict(self, X_new):
        return self.model.predict_one(X_new)

    def update(self, X_new, y_new):
        y_new = int(y_new)
        self.model.learn_one(X_new, y_new)

def capture_live_network():
    """Captures live network traffic and writes it to live_traffic.csv"""
    live_traffic_path = "data/live_traffic.csv"

    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        lines = result.stdout.split("\n")

        connections = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 5 and "ESTABLISHED" in parts:
                src_ip, dst_ip = parts[1], parts[2]
                
                connections.append({
                    "source_ip": src_ip,
                    "destination_ip": dst_ip,
                    "flow_duration": random.randint(500, 5000),
                    "byte_count": random.randint(1000, 100000),
                    "packet_count": random.randint(10, 500),
                    "syn_flag": random.choice([0, 1]),
                    "ip_proto": 6
                })

        if len(connections) > 0:
            df = pd.DataFrame(connections)
            df.to_csv(live_traffic_path, index=False)
            print(f"📡 Captured {len(connections)} Live Network Connections!")

        return True if len(connections) > 0 else False

    except Exception as e:
        print(f"❌ Error capturing live traffic: {e}")
        return False

def show_alert(ip):
    """✅ Threaded Function to Prevent Duplicate Alerts"""
    global last_alert_time
    current_time = time.time()
    
    if ip in last_alert_time and current_time - last_alert_time[ip] < 300:  
        return  

    last_alert_time[ip] = current_time  
    attack_counts[ip] = 0  

    try:
        notification.notify(
            title="🚨 DDoS Attack Detected!",
            message=f"Suspicious traffic detected from {ip}.",
            timeout=5
        )
    except Exception as e:
        print(f"❌ Notification Error: {e}")

def start_live_monitoring():
    ids = IDS("data/dataset.csv")
    print("✅ IDS Initialized (Running in Background)")

    start_time = time.time()

    while True:
        try:
            if capture_live_network():
                print("📡 Live Network Traffic Detected - Analyzing for Attacks...")
                df = pd.read_csv("data/live_traffic.csv")

                for _, row in df.iterrows():
                    test_data = row.to_dict()
                    source_ip = test_data.get("source_ip", "Unknown")
                    prediction = ids.predict(test_data)
                    print(f"🛡️ Live Traffic - Predicted: {prediction}, Data: {test_data}")

                    if prediction == 1:
                        attack_counts[source_ip] += 1  

                        if attack_counts[source_ip] >= ALERT_THRESHOLD:
                            print(f"🚨 ALERT: DDoS Attack Detected from {source_ip}!")
                            threading.Thread(target=show_alert, args=(source_ip,)).start()
                            attack_log.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {source_ip}")

                open("data/live_traffic.csv", "w").close()  

            if time.time() - start_time >= MAX_RUNTIME:
                print("⏹️  Auto-Stopping IDS After Reaching Max Runtime.")
                break

            if time.time() - start_time > LOG_CLEANUP_INTERVAL:
                print("🧹 Cleaning old logs to free memory...")
                attack_log.clear()
                start_time = time.time()

            print(f"⏳ Waiting {LIVE_MONITOR_INTERVAL} seconds before next capture...")
            time.sleep(LIVE_MONITOR_INTERVAL)  

        except KeyboardInterrupt:
            print("\n🛑 IDS Stopped by User.")
            break

def simulate_fake_attack():
    """✅ Simulates a fake attack and tests detection."""
    fake_attack_data = {
        "source_ip": "192.168.1.100",
        "destination_ip": "203.0.113.5",
        "flow_duration": 4000,
        "byte_count": 90000,
        "packet_count": 500,
        "syn_flag": 1,
        "ip_proto": 6
    }
    print(f"⚠️ Simulating Fake Attack: {fake_attack_data}")

    # ✅ Save to live_traffic.csv so IDS processes it
    df_fake = pd.DataFrame([fake_attack_data])
    df_fake.to_csv("data/live_traffic.csv", mode='a', header=False, index=False)
    print("📡 Fake Attack Injected into Live Traffic!")

def upload_and_test_csv():
    """✅ Allows the user to upload a CSV and test detection."""
    csv_path = input("📂 Enter path to CSV file: ")
    if not os.path.exists(csv_path):
        print("❌ ERROR: File not found.")
        return

    df = pd.read_csv(csv_path)
    print(f"📊 Loaded {len(df)} samples from {csv_path}")

     # ✅ Predict attacks on the uploaded CSV
    ids = IDS("data/dataset.csv")
    for _, row in df.iterrows():
        test_data = row.to_dict()
        prediction = ids.predict(test_data)
        print(f"🔍 Predicted: {prediction}, Data: {test_data}")

def main_menu():
    while True:
        print("\n📌 Main Menu:")
        print("1️⃣ Start Live Monitoring")
        print("2️⃣ Simulate Fake Attack")
        print("3️⃣ Upload & Test CSV")
        print("4️⃣ Exit")
        choice = input("👉 Enter your choice: ")

        if choice == "1":
            start_live_monitoring()
        elif choice == "2":
            simulate_fake_attack()
        elif choice == "3":
            upload_and_test_csv()
        elif choice == "4":
            print("👋 Exiting IDS...")
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    main_menu()
