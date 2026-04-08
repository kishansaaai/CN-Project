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


def parse_ts(ts):
    try:
        dt = datetime.strptime(ts, "%H:%M:%S.%f")
        return dt.timestamp()
    except:
        return time.time()


def handle(data, addr):
    raw = data.decode()
    try:
        entry = json.loads(raw)
        ts_val = parse_ts(entry["timestamp"])
    except:
        ts_val = time.time()

    log_buffer.append((ts_val, raw))

    # When buffer fills → sort
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

    next_flush_at = time.time() + FLUSH_DELAY


print(f"Server running on {HOST}:{PORT}")

while True:
    try:
        while True:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)
            handle(data, addr)
    except BlockingIOError:
        pass

    flush_logs()
    time.sleep(0.01)
