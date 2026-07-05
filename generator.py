#!/usr/bin/env python3
import json
import re
from pathlib import Path


def render_template(template_text, context):
    try:
        from jinja2 import Template
        return Template(template_text).render(**context)
    except ImportError:
        pattern = re.compile(r"\{\{\s*([A-Za-z0-9_\.]+)\s*\}\}")

        def repl(match):
            key = match.group(1)
            return str(context.get(key, ""))

        return pattern.sub(repl, template_text)


def main():
    base_dir = Path(__file__).resolve().parent
    interface = json.loads((base_dir / "interface.json").read_text(encoding="utf-8"))
    template_text = (base_dir / "template.py.jinja2").read_text(encoding="utf-8")

    context = {
        "class_name": "MessageHandler",
        "default_sender": interface.get("defaultSender", "sender"),
        "default_receiver": interface.get("defaultReceiver", "receiver"),
    }

    output = render_template(template_text, context)
    output_path = base_dir / "generated_message_handler.py"
    output_path.write_text(output, encoding="utf-8")
    print(f"Generated {output_path.name}")


if __name__ == "__main__":
    main()
