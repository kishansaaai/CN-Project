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
    "rapid": False,
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

    while True:
        if not state["running"]:
            time.sleep(0.2)
            continue

        sock.sendto(json.dumps(make_log()).encode(), (HOST, PORT))

        delay = 0.05 if state["rapid"] else state["interval"]
        time.sleep(delay)


def input_loop():
    print("\nCommands:")
    print("s → start/pause")
    print("f → rapid fire")
    print("q → quit\n")

    while True:
        cmd = input(">> ").strip().lower()

        if cmd == "s":
            state["running"] = not state["running"]
            print("Running" if state["running"] else "Paused")

        elif cmd == "f":
            state["rapid"] = not state["rapid"]
            print("Rapid ON" if state["rapid"] else "Rapid OFF")

        elif cmd == "q":
            break


threading.Thread(target=send_loop, daemon=True).start()
input_loop()
