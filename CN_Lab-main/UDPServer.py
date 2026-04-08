import socket
import time
import json
from datetime import datetime
from collections import deque

HOST = "0.0.0.0"
PORT = 20005
MAX_PACKET_SIZE = 4096

n = 5
FLUSH_DELAY = 0.2

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
sock.setblocking(False)

log_buffer = []
flush_queue = deque()
next_flush_at = 0

# 📊 STATS
stats = {
    "received": 0,
    "flushed": 0,
    "dropped": 0
}

last_time = time.time()
last_flushed = 0
last_received = 0


def parse_ts(ts):
    try:
        dt = datetime.strptime(ts, "%H:%M:%S.%f")
        return dt.timestamp()
    except:
        return time.time()


def handle(data, addr):
    raw = data.decode()

    # total system load
    depth = len(log_buffer) + len(flush_queue)

    # DROP condition
    if depth >= 2 * n:
        stats["dropped"] += 1
        return

    try:
        entry = json.loads(raw)
        ts_val = parse_ts(entry["timestamp"])
    except:
        ts_val = time.time()

    log_buffer.append((ts_val, raw))
    stats["received"] += 1

    # sorting batch
    if len(log_buffer) >= n:
        log_buffer.sort(key=lambda x: x[0])
        flush_queue.extend(log_buffer)
        log_buffer.clear()


def flush_logs():
    global next_flush_at

    if not flush_queue:
        return

    if time.time() < next_flush_at:
        return

    _, raw = flush_queue.popleft()

    try:
        e = json.loads(raw)
        print(f"{e['timestamp']}  {e['level']}  [{e['machine']}]  {e['message']}")
    except:
        print(raw)

    stats["flushed"] += 1
    next_flush_at = time.time() + FLUSH_DELAY


def print_stats():
    global last_time, last_flushed, last_received

    now = time.time()

    if now - last_time >= 1.0:
        flushed_per_sec = stats["flushed"] - last_flushed
        recv_per_sec = stats["received"] - last_received

        print("\n--- STATS ---")
        print(f"Throughput (processed): {flushed_per_sec} logs/sec")
        print(f"Incoming rate:          {recv_per_sec} logs/sec")
        print(f"Total received:         {stats['received']}")
        print(f"Total flushed:          {stats['flushed']}")
        print(f"Dropped logs:           {stats['dropped']}")
        print(f"Buffer size:            {len(log_buffer) + len(flush_queue)}")
        print("----------------\n")

        last_time = now
        last_flushed = stats["flushed"]
        last_received = stats["received"]


print(f"Server running on {HOST}:{PORT}")

while True:
    try:
        while True:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)
            handle(data, addr)
    except BlockingIOError:
        pass

    flush_logs()
    print_stats()

    time.sleep(0.01)
