import socket
import time
import json
import random
import threading
import argparse
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", default=20005, type=int)
parser.add_argument("--name", default="Machine-A")
parser.add_argument("--interval", default=1.0, type=float)
args = parser.parse_args()

HOST = args.host
PORT = args.port

state = {
    "machine": args.name,
    "interval": args.interval,
    "running": True,
}

LEVELS = ["INFO", "DEBUG", "WARN", "ERROR"]

def make_log():
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "machine": state["machine"],
        "level": random.choice(LEVELS),
        "message": f"Value {random.randint(1,100)}",
    }


def send_loop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)

    while True:
        if not state["running"]:
            time.sleep(0.5)
            continue

        sock.sendto(json.dumps(make_log()).encode(), (HOST, PORT))

        try:
            data, _ = sock.recvfrom(64)
            signal = data.decode()

            if signal == "STOP":
                print("[STOP] Pausing...")
                time.sleep(5)

            elif signal == "SLOW_DOWN":
                state["interval"] *= 2
                print(f"[SLOW DOWN] Interval = {state['interval']}")
        except:
            pass

        time.sleep(state["interval"])


def input_loop():
    while True:
        cmd = input("Enter (start/stop/exit): ").strip().lower()

        if cmd == "start":
            state["running"] = True
        elif cmd == "stop":
            state["running"] = False
        elif cmd == "exit":
            break


threading.Thread(target=send_loop, daemon=True).start()
input_loop()