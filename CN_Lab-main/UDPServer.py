import socket
import time
import json
from datetime import datetime
from collections import deque

HOST = "0.0.0.0"   # IMPORTANT: allow all connections
PORT = 20005
MAX_PACKET_SIZE = 4096

n = 5
FLUSH_DELAY = 0.3

stats = {"received": 0, "flushed": 0, "dropped": 0}

logfile = open("logs.txt", "a", buffering=1)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
sock.setblocking(False)

log_buffer = []
flush_queue = deque()
next_flush_at = 0.0

throughput_last_time = time.time()
throughput_last_flushed = 0

SLOW_THRESHOLD = int(2 * n * 0.9)
STOP_THRESHOLD = 2 * n


def parse_ts(ts_str):
    try:
        dt = datetime.strptime(ts_str, "%H:%M:%S.%f")
        return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
    except:
        return time.time()


def handle(data, addr):
    raw = data.decode(errors="replace").strip()
    depth = len(log_buffer) + len(flush_queue)

    if depth >= STOP_THRESHOLD:
        sock.sendto(b"STOP", addr)
        stats["dropped"] += 1
        return

    if depth >= SLOW_THRESHOLD:
        sock.sendto(b"SLOW_DOWN", addr)
        return

    try:
        entry = json.loads(raw)
        ts_f = parse_ts(entry.get("timestamp", ""))
    except:
        ts_f = time.time()

    log_buffer.append((ts_f, raw, addr))
    stats["received"] += 1

    if len(log_buffer) >= n:
        log_buffer.sort(key=lambda x: x[0])
        flush_queue.extend(log_buffer[:n])
        del log_buffer[:n]


def maybe_flush_one():
    global next_flush_at

    if not flush_queue or time.time() < next_flush_at:
        return

    _, line, _ = flush_queue.popleft()

    try:
        e = json.loads(line)
        log_str = f"{e['timestamp']}  {e['level']}  [{e['machine']}]  {e['message']}"
    except:
        log_str = line

    print(log_str)
    logfile.write(log_str + "\n")

    stats["flushed"] += 1
    next_flush_at = time.time() + FLUSH_DELAY


print(f"Server running on {HOST}:{PORT}")

while True:
    try:
        while True:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)
            handle(data, addr)
    except BlockingIOError:
        pass

    maybe_flush_one()
    time.sleep(0.005)