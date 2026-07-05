#!/usr/bin/env python3
import argparse
import json
import socket
from pathlib import Path


def send_message(payload, receiver, sender, host, port):
    # Prefer generated binary handler if available
    base_dir = Path(__file__).resolve().parent
    gen_path = base_dir / "generated_message_handler.py"
    if gen_path.exists():
        from generated_message_handler import MessageHandler
        handler = MessageHandler(sender)
        import time
        message = handler.make_message(
            receiver=receiver,
            team=payload,
            probability=0.0,
            source="client",
            timestamp=str(int(time.time())),
        )
        data = handler.serialize(message)
        with socket.create_connection((host, port), timeout=5) as sock:
            sock.sendall(data)
        print(f"Sender sent (binary): {payload} -> {receiver}")
    else:
        message = {"sender": sender, "receiver": receiver, "payload": payload}
        with socket.create_connection((host, port), timeout=5) as sock:
            sock.sendall(json.dumps(message).encode("utf-8"))
        print(f"Sender sent (json): {payload} -> {receiver}")


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
