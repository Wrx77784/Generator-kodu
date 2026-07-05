#!/usr/bin/env python3
import argparse
import json
import socket
from pathlib import Path


def send_message(payload, receiver, sender, host, port):
    message = {"sender": sender, "receiver": receiver, "payload": payload}
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(json.dumps(message).encode("utf-8"))
    print(f"Sender sent: {payload} -> {receiver}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", nargs="?", default="hello")
    parser.add_argument("--receiver", default=None)
    parser.add_argument("--sender", default=None)
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    interface_path = base_dir / "interface.json"
    interface = json.loads(interface_path.read_text(encoding="utf-8")) if interface_path.exists() else {}

    sender = args.sender or interface.get("defaultSender", "sender")
    receiver = args.receiver or interface.get("defaultReceiver", "receiver")
    host = args.host or interface.get("host", "127.0.0.1")
    port = args.port or interface.get("port", 5001)
    send_message(args.payload, receiver, sender, host, port)


if __name__ == "__main__":
    main()
