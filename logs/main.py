from src.traffic_collector import TrafficCollector
from src.ids import IDS
from src.ips import block_attacker

def main():
    collector = TrafficCollector()
    ids = IDS("data/dataset.csv")

    while True:
        traffic_sample = collector.collect_traffic()
        prediction = ids.predict(traffic_sample)

        if prediction == 1:  # Attack detected
            block_attacker(collector.datapaths, traffic_sample['ip_src'])

if _name_ == "_main_":
    main()