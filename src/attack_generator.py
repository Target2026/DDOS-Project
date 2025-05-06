import os
import pandas as pd
from scapy.config import conf

# Check if Npcap is installed
npcap_installed = os.system("where npcap") == 0  # Windows command to check for Npcap

print("🔄 Generating Fake Attack Data...")

attack_data = [
    {
        "source_ip": "10.0.0.2",
        "destination_ip": "10.0.0.23",
        "flow_duration": 5000,      # Long duration = suspicious
        "byte_count": 50000,        # High byte count = attack
        "packet_count": 500,        # Many packets = attack
        "syn_flag": 1,              # SYN flag is often used in DDoS
        "ip_proto": 6,              # Protocol 6 = TCP
        "attack": 1                 # Label as attack
    }
]


if npcap_installed:
    from scapy.all import IP, UDP, send
    print("✅ Npcap detected! Sending real network attack packets...")
    conf.use_pcap = True  # Force Scapy to use WinPcap
    send(IP(src="10.0.0.2", dst="10.0.0.23")/UDP(dport=53))  # Send fake UDP attack
else:
    print("⚠️ Npcap NOT detected! Only logging attack, no real network packets sent.")

# Save attack to CSV
df = pd.DataFrame(attack_data)
df["attack"] = df["attack"].astype(int)
df.to_csv("data/generated_attacks.csv", index=False)
print("✅ Fake attack data saved to data/generated_attacks.csv")
