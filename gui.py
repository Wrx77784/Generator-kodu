#!/usr/bin/env python3
import threading
import socket
import json
import subprocess
import sys
import importlib
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import scrolledtext
    from tkinter import ttk
except Exception:
    print("Tkinter is required for GUI")
    raise

BASE_DIR = Path(__file__).resolve().parent


class ServerThread(threading.Thread):
    def __init__(self, host, port, log_fn):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.log = log_fn
        self._stop = threading.Event()
        self._sock = None

    def stop(self):
        self._stop.set()
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass

    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                self._sock = server
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((self.host, self.port))
                server.listen(5)
                self.log(f"Server listening on {self.host}:{self.port}")
                server.settimeout(1.0)
                while not self._stop.is_set():
                    try:
                        conn, addr = server.accept()
                    except socket.timeout:
                        continue
                    with conn:
                        data = b""
                        while True:
                            chunk = conn.recv(4096)
                            if not chunk:
                                break
                            data += chunk
                        if not data:
                            continue
                        # try generated deserialization
                        gen = BASE_DIR / "generated_message_handler.py"
                        if gen.exists():
                            try:
                                from generated_message_handler import MessageHandler
                                message = MessageHandler("").deserialize(data)
                                self.log(f"[binary] {message['payload']} from {message['sender']} ({addr[0]}:{addr[1]})")
                                continue
                            except Exception as e:
                                self.log(f"Binary deserialization failed: {e}")
                        try:
                            message = json.loads(data.decode("utf-8"))
                            self.log(f"[json] {message['payload']} from {message['sender']} ({addr[0]}:{addr[1]})")
                        except Exception as e:
                            self.log(f"Unknown data from {addr}: {e}")
        except Exception as e:
            self.log(f"Server error: {e}")


class App:
    def __init__(self, root):
        self.root = root
        root.title("Generator Kodu - GUI")

        style = ttk.Style(root)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        interface = {}
        try:
            interface_path = BASE_DIR / 'interface.json'
            if interface_path.exists():
                interface = json.loads(interface_path.read_text(encoding='utf-8'))
        except Exception:
            interface = {}

        default_host = interface.get('host', '127.0.0.1')
        default_port = interface.get('port', 5001)
        default_sender = interface.get('defaultSender', 'sender')
        default_receiver = interface.get('defaultReceiver', 'receiver')

        # Hidden host/port/sender/receiver defaults used for auto-send
        self.host = tk.StringVar(value=str(default_host))
        self.port = tk.StringVar(value=str(default_port))
        self.sender = tk.StringVar(value=str(default_sender))
        self.receiver = tk.StringVar(value=str(default_receiver))

        self.payload = tk.StringVar(value='Argentina 2026 probability')

        controls = ttk.Frame(root, padding=8)
        controls.pack(fill=tk.X)

        self.start_btn = ttk.Button(controls, text="Start", command=self.toggle_auto_send)
        self.start_btn.pack(side=tk.LEFT, padx=8)

        self.percent_label = ttk.Label(controls, text="Argentina 2026 win chance: --%", font=(None, 14))
        self.percent_label.pack(side=tk.RIGHT, padx=8)

        # Automatic live update status
        factors = ttk.Frame(root, padding=6)
        factors.pack(fill=tk.X)

        ttk.Label(factors, text="Live 2026 tournament probability updates every 2 seconds.").pack(side=tk.LEFT, padx=4)
        self.status_label = ttk.Label(factors, text="Status: waiting")
        self.status_label.pack(side=tk.RIGHT, padx=8)

        self.top_teams_label = ttk.Label(root, text="Top teams: loading...", wraplength=760, justify=tk.LEFT)
        self.top_teams_label.pack(fill=tk.X, padx=8, pady=(0, 8))
        # Matplotlib figure for live chart
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except Exception:
            Figure = None
            FigureCanvasTkAgg = None

        self.history = {}
        self.max_points = 200
        if Figure is not None:
            fig = Figure(figsize=(6, 3), dpi=100)
            self.ax = fig.add_subplot(111)
            self.ax.set_ylim(0, 1)
            self.ax.set_ylabel('Probability (%)')
            self.ax.set_title('Top 5 win chances over time')
            self.ax.grid(True, linestyle='--', alpha=0.25)
            try:
                import matplotlib.ticker as mtick
                self.ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0))
            except Exception:
                pass
            canvas = FigureCanvasTkAgg(fig, master=root)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            self.canvas = canvas
        else:
            self.ax = None
            self.canvas = None

        # hide previous controls by not creating them; keep generate/open available via menu
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Generate Handler", command=self.generate)
        filemenu.add_command(label="Open Handler", command=self.open_handler)
        menubar.add_cascade(label="File", menu=filemenu)
        root.config(menu=menubar)

        self.server_thread = None
        self.auto_send_thread = None
        self.auto_send_running = False
        self.send_interval = 2
        self.recent_map = {}

    def append_log(self, text):
        pass

    def generate(self):
        try:
            res = subprocess.run([sys.executable, str(BASE_DIR / "generator.py")], capture_output=True, text=True)
            self.append_log(res.stdout.strip())
            if res.stderr:
                self.append_log(res.stderr.strip())
            # reload module if exists
            gen = BASE_DIR / "generated_message_handler.py"
            if gen.exists():
                if 'generated_message_handler' in sys.modules:
                    importlib.reload(sys.modules['generated_message_handler'])
                else:
                    importlib.import_module('generated_message_handler')
                self.append_log("Generated handler loaded")
        except Exception as e:
            self.append_log(f"Generate failed: {e}")

    def start_server(self):
        host = self.host.get()
        port = int(self.port.get())
        if self.server_thread and self.server_thread.is_alive():
            self.append_log("Server already running")
            return
        self.server_thread = ServerThread(host, port, self.append_log)
        self.server_thread.start()

    def stop_server(self):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread = None
            self.append_log("Server stopped")

    def send(self):
        host = self.host.get()
        port = int(self.port.get())
        sender = self.sender.get()
        receiver = self.receiver.get()
        gen = BASE_DIR / "generated_message_handler.py"
        try:
            if gen.exists():
                from generated_message_handler import MessageHandler
                import time, random
                handler = MessageHandler(sender)
                team = "Argentina"
                base = 0.25
                prob = round(base + random.uniform(-0.05, 0.15), 4)
                fields = {"team": team, "probability": prob, "source": "gui-sim", "timestamp": str(int(time.time()))}
                message = handler.make_message(receiver=receiver, **fields)
                data = handler.serialize(message)
                with socket.create_connection((host, port), timeout=5) as sock:
                    sock.sendall(data)
                self.append_log(f"Sent (binary): {team} -> {prob} to {receiver}")
            else:
                payload = f"Argentina {round(0.25, 4)}"
                message = {"sender": sender, "receiver": receiver, "payload": payload}
                with socket.create_connection((host, port), timeout=5) as sock:
                    sock.sendall(json.dumps(message).encode('utf-8'))
                self.append_log(f"Sent (json): {payload} -> {receiver}")
        except Exception as e:
            self.append_log(f"Send failed: {e}")

    def open_handler(self):
        gen = BASE_DIR / "generated_message_handler.py"
        if not gen.exists():
            self.append_log("No generated handler found. Click Generate first.")
            return
        try:
            content = gen.read_text(encoding='utf-8')
        except Exception as e:
            self.append_log(f"Failed to read handler: {e}")
            return

        win = tk.Toplevel(self.root)
        win.title("generated_message_handler.py")
        txt = scrolledtext.ScrolledText(win, width=100, height=40)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert(tk.END, content)
        txt.configure(state=tk.DISABLED)

        def open_in_editor():
            try:
                import os
                os.startfile(str(gen))
            except Exception as e:
                self.append_log(f"Open in editor failed: {e}")

        btn = tk.Button(win, text="Open in Editor", command=open_in_editor)
        btn.pack(pady=4)

    def start_auto_send(self):
        if self.auto_send_running:
            return
        import threading, time
        from model import DEFAULT_RATINGS, adjusted_ratings_map, world_cup_win_probability, top_teams

        self.auto_send_running = True
        self.start_btn.config(text="Stop")
        self.status_label.config(text='Status: running')

        def loop():
            while self.auto_send_running:
                try:
                    host = self.host.get() or '127.0.0.1'
                    port = int(self.port.get() or 5001)
                    sender = self.sender.get() or 'sender'
                    receiver = self.receiver.get() or 'receiver'

                    field = list(DEFAULT_RATINGS.keys())
                    recent_map = {}
                    adjusted_map = None
                    try:
                        from data_source import get_recent_map
                        recent_map = get_recent_map('Argentina')
                        self.status_label.config(text='Status: live data')
                    except Exception as e:
                        self.append_log(f'Live fetch failed: {e}')
                        self.status_label.config(text='Status: fallback data')

                    try:
                        adjusted_map = adjusted_ratings_map(DEFAULT_RATINGS, recent_map=recent_map)
                    except Exception:
                        adjusted_map = None

                    if adjusted_map is not None:
                        prob = world_cup_win_probability('Argentina', field, ratings=adjusted_map)
                        best = top_teams(field, ratings=adjusted_map, count=5)
                    else:
                        prob = world_cup_win_probability('Argentina', field, ratings=DEFAULT_RATINGS)
                        best = top_teams(field, ratings=DEFAULT_RATINGS, count=5)

                    best_text = ', '.join(f"{item['team']} ({item['prob']*100:.1f}%)" for item in best)
                    self.root.after(0, self.top_teams_label.config, {'text': f"Top 5 teams: {best_text}"})

                    gen = BASE_DIR / 'generated_message_handler.py'
                    if gen.exists():
                        from generated_message_handler import MessageHandler
                        import time
                        handler = MessageHandler(sender)
                        fields = {"team": "Argentina", "probability": round(prob, 4), "source": "auto-gui", "timestamp": str(int(time.time()))}
                        message = handler.make_message(receiver=receiver, **fields)
                        data = handler.serialize(message)
                        with socket.create_connection((host, port), timeout=5) as sock:
                            sock.sendall(data)
                    else:
                        msg = {"sender": sender, "receiver": receiver, "payload": f"Argentina {round(prob,4)}"}
                        import json
                        with socket.create_connection((host, port), timeout=5) as sock:
                            sock.sendall(json.dumps(msg).encode('utf-8'))

                    self.root.after(0, self.record_prob, best)
                except Exception as e:
                    self.append_log(f"Auto-send failed: {e}")
                time.sleep(self.send_interval)

        t = threading.Thread(target=loop, daemon=True)
        t.start()
        self.auto_send_thread = t

    def toggle_auto_send(self):
        if self.auto_send_running:
            self.stop_auto_send()
        else:
            self.start_auto_send()

    def stop_auto_send(self):
        self.auto_send_running = False
        self.start_btn.config(text="Start")
        self.status_label.config(text='Status: stopped')

    def record_prob(self, best=None):
        if best is None:
            return

        self.top_teams_label.config(text=', '.join(f"{item['team']} ({item['prob']*100:.1f}%)" for item in best))
        argentina_item = next((item for item in best if item['team'] == 'Argentina'), None)
        pct = round((argentina_item['prob'] if argentina_item else 0.0) * 100, 2)
        self.percent_label.config(text=f"Argentina 2026 win chance: {pct}%")

        for item in best:
            team = item['team']
            self.history.setdefault(team, []).append(item['prob'])
            if len(self.history[team]) > self.max_points:
                self.history[team].pop(0)

        for team in list(self.history):
            if team not in [item['team'] for item in best]:
                del self.history[team]

        if self.ax is not None:
            self.ax.clear()
            self.ax.set_ylim(0, 1)
            self.ax.set_ylabel('Probability')
            self.ax.set_xlabel('Updates')
            self.ax.set_title('Top 5 win chances over time')
            self.ax.grid(True, linestyle='--', alpha=0.25)

            max_len = max((len(history) for history in self.history.values()), default=0)
            xs = list(range(-max_len + 1, 1))
            for item in best:
                team = item['team']
                ys = self.history.get(team, [])
                ys_plot = [float(v) for v in ys]
                self.ax.plot(xs[-len(ys_plot):], ys_plot, '-o', markersize=3, label=team)

            self.ax.legend(loc='upper left', fontsize='small')
            if self.canvas:
                try:
                    self.canvas.draw_idle()
                except Exception:
                    pass



def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
