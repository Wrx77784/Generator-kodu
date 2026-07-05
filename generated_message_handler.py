# Generated message handler with binary serialization
import struct

class MessageHandler:
    def __init__(self, name):
        self.name = name

    def make_message(self, receiver="receiver", **fields):
        msg = {"sender": self.name, "receiver": receiver}
        msg["team"] = fields.get("team", "")
        msg["probability"] = fields.get("probability", "")
        msg["source"] = fields.get("source", "")
        msg["timestamp"] = fields.get("timestamp", "")
        return msg

    def serialize(self, message):
        parts = []
        # sender + receiver first
        for key in ("sender", "receiver"):
            b = str(message.get(key, "")).encode("utf-8")
            parts.append(struct.pack("!I", len(b)))
            parts.append(b)

        # schema fields
        # field: team (string)
        if "team" in message:
            val = message.get("team")
            b = str(val).encode("utf-8")
            parts.append(struct.pack("!I", len(b)))
            parts.append(b)
        else:
            parts.append(struct.pack("!I", 0))

        # field: probability (float)
        if "probability" in message:
            val = message.get("probability")
            parts.append(struct.pack("!d", float(val)))
        else:
            parts.append(struct.pack("!d", 0.0))

        # field: source (string)
        if "source" in message:
            val = message.get("source")
            b = str(val).encode("utf-8")
            parts.append(struct.pack("!I", len(b)))
            parts.append(b)
        else:
            parts.append(struct.pack("!I", 0))

        # field: timestamp (string)
        if "timestamp" in message:
            val = message.get("timestamp")
            b = str(val).encode("utf-8")
            parts.append(struct.pack("!I", len(b)))
            parts.append(b)
        else:
            parts.append(struct.pack("!I", 0))

        return b"".join(parts)

    def deserialize(self, data: bytes):
        import io
        buf = io.BytesIO(data)

        def read_len_prefixed():
            ln = buf.read(4)
            if len(ln) < 4:
                return ""
            (l,) = struct.unpack("!I", ln)
            return buf.read(l).decode("utf-8")

        sender = read_len_prefixed()
        receiver = read_len_prefixed()
        msg = {"sender": sender, "receiver": receiver}

        # read field team (string)
        msg["team"] = read_len_prefixed()

        # read field probability (float)
        raw = buf.read(8)
        msg["probability"] = struct.unpack("!d", raw)[0] if len(raw) == 8 else 0.0

        # read field source (string)
        msg["source"] = read_len_prefixed()

        # read field timestamp (string)
        msg["timestamp"] = read_len_prefixed()

        return msg

    def receive(self, message):
        parts = []
        parts.append(f'{message["team"]}')
        parts.append(f'{message["probability"]}')
        parts.append(f'{message["source"]}')
        parts.append(f'{message["timestamp"]}')
        return f"{self.name} received: " + ", ".join(parts)
