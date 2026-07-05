#!/usr/bin/env python3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TYPE_FORMATS = {
    'string': 'string',
    'float': '!d',
    'int': '!i',
    'bool': '!?',
}

TYPE_DEFAULTS = {
    'string': '""',
    'float': '0.0',
    'int': '0',
    'bool': 'False',
}


def generate_handler(schema, default_sender, default_receiver):
    lines = [
        '# Generated message handler with binary serialization',
        'import struct',
        '',
        'class MessageHandler:',
        '    def __init__(self, name):',
        '        self.name = name',
        '',
        f'    def make_message(self, receiver="{default_receiver}", **fields):',
        '        msg = {"sender": self.name, "receiver": receiver}',
    ]

    for field in schema:
        lines.append(f'        msg["{field["name"]}"] = fields.get("{field["name"]}", "")')
    lines.extend([
        '        return msg',
        '',
        '    def serialize(self, message):',
        '        parts = []',
        '        # sender + receiver first',
        '        for key in ("sender", "receiver"):',
        '            b = str(message.get(key, "")).encode("utf-8")',
        '            parts.append(struct.pack("!I", len(b)))',
        '            parts.append(b)',
        '',
        '        # schema fields',
    ])

    for field in schema:
        name = field['name']
        ftype = field['type']
        if ftype == 'string':
            lines.extend([
                f'        # field: {name} (string)',
                f'        if "{name}" in message:',
                f'            val = message.get("{name}")',
                '            b = str(val).encode("utf-8")',
                '            parts.append(struct.pack("!I", len(b)))',
                '            parts.append(b)',
                '        else:',
                '            parts.append(struct.pack("!I", 0))',
                '',
            ])
        else:
            fmt = TYPE_FORMATS.get(ftype, 'string')
            default = TYPE_DEFAULTS.get(ftype, '""')
            lines.extend([
                f'        # field: {name} ({ftype})',
                f'        if "{name}" in message:',
                f'            val = message.get("{name}")',
                f'            parts.append(struct.pack("{fmt}", {"bool" == ftype and "bool(val)" or f"float(val)" if ftype == "float" else f"int(val)" if ftype == "int" else f"str(val).encode(\"utf-8\")"}))',
            ])
            if ftype in ('float', 'int', 'bool'):
                lines.extend(['        else:', f'            parts.append(struct.pack("{fmt}", {default}))', ''])
            else:
                lines.extend(['        else:', '            parts.append(struct.pack("!I", 0))', ''])

    lines.extend([
        '        return b"".join(parts)',
        '',
        '    def deserialize(self, data: bytes):',
        '        import io',
        '        buf = io.BytesIO(data)',
        '',
        '        def read_len_prefixed():',
        '            ln = buf.read(4)',
        '            if len(ln) < 4:',
        '                return ""',
        '            (l,) = struct.unpack("!I", ln)',
        '            return buf.read(l).decode("utf-8")',
        '',
        '        sender = read_len_prefixed()',
        '        receiver = read_len_prefixed()',
        '        msg = {"sender": sender, "receiver": receiver}',
        '',
    ])

    for field in schema:
        name = field['name']
        ftype = field['type']
        if ftype == 'string':
            lines.extend([
                f'        # read field {name} (string)',
                f'        msg["{name}"] = read_len_prefixed()',
                '',
            ])
        elif ftype == 'float':
            lines.extend([
                f'        # read field {name} (float)',
                '        raw = buf.read(8)',
                f'        msg["{name}"] = struct.unpack("!d", raw)[0] if len(raw) == 8 else 0.0',
                '',
            ])
        elif ftype == 'int':
            lines.extend([
                f'        # read field {name} (int)',
                '        raw = buf.read(4)',
                f'        msg["{name}"] = struct.unpack("!i", raw)[0] if len(raw) == 4 else 0',
                '',
            ])
        elif ftype == 'bool':
            lines.extend([
                f'        # read field {name} (bool)',
                '        raw = buf.read(1)',
                f'        msg["{name}"] = struct.unpack("!?", raw)[0] if len(raw) == 1 else False',
                '',
            ])
        else:
            lines.extend([
                f'        # read field {name} ({ftype})',
                f'        msg["{name}"] = read_len_prefixed()',
                '',
            ])

    lines.extend([
        '        return msg',
        '',
        '    def receive(self, message):',
        '        parts = []',
    ])

    for field in schema:
        name = field['name']
        lines.append(f'        parts.append(f\'{{message["{name}"]}}\')')
    lines.extend([
        '        return f"{self.name} received: " + ", ".join(parts)',
    ])

    return "\n".join(lines) + "\n"


def main():
    interface_path = BASE_DIR / 'interface.json'
    interface = json.loads(interface_path.read_text(encoding='utf-8'))
    schema = interface.get('schema', [])
    output = generate_handler(schema, interface.get('defaultSender', 'sender'), interface.get('defaultReceiver', 'receiver'))
    output_path = BASE_DIR / 'generated_message_handler.py'
    output_path.write_text(output, encoding='utf-8')
    print(f'Generated {output_path.name}')


if __name__ == '__main__':
    main()
