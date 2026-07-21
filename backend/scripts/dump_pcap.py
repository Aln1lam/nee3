from scapy.all import Raw, rdpcap
from pathlib import Path

p = Path(r"E:\neepu\captures\challenge_216_team_39_user_22\20260716_072919.pcap")
for i, pkt in enumerate(rdpcap(str(p))):
    if Raw not in pkt:
        continue
    t = bytes(pkt[Raw].load).decode("utf-8", "replace")
    if t.startswith("POST") or "UNION" in t or "username=" in t:
        print(f"=== packet {i} ===")
        print(t[:900])
        print()
