#!/usr/bin/env python3
import argparse
import json
import socket
import threading
from pathlib import Path


def handle_client(conn, addr):
    with conn:
        data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        if not data:
            return

        # Try binary deserialization using generated handler, otherwise fallback to JSON
        base_dir = Path(__file__).resolve().parent
        gen_path = base_dir / "generated_message_handler.py"
        if gen_path.exists():
            from generated_message_handler import MessageHandler
            # Use default receiver name from interface when creating handler in main
            message = MessageHandler("").deserialize(data)
            print(f"Receiver got (binary): {message} ({addr[0]}:{addr[1]})")
        else:
            message = json.loads(data.decode("utf-8"))
            print(f"Receiver got (json): {message} ({addr[0]}:{addr[1]})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    interface_path = base_dir / "interface.json"
    interface = json.loads(interface_path.read_text(encoding="utf-8")) if interface_path.exists() else {}

    host = args.host or interface.get("host", "127.0.0.1")
    port = args.port or interface.get("port", 5001)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(10)
        print(f"Receiver listening on {host}:{port}")

        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()


if __name__ == "__main__":
    main()
