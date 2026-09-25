import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, threading, queue, re
from datetime import datetime
import serial
from serial.tools import list_ports
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import ScalarFormatter


DB = "terralink.db"
BAUD = 115200
MAX_POINTS = 60


class TerraLinkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TerraLink • Environmental Monitoring")
        self.root.geometry("1450x900")
        self.root.minsize(1100, 720)
        self.root.configure(bg="#080d18")

        self.db = sqlite3.connect(DB, check_same_thread=False)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS readings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                node_id INTEGER,
                packet_number INTEGER,
                temperature REAL,
                humidity REAL,
                pressure REAL,
                gas REAL,
                battery REAL,
                battery_percent REAL,
                rssi REAL,
                snr REAL
            )
        """)
        self.db.commit()

        self.ser = None
        self.stop = threading.Event()
        self.q = queue.Queue()
        self.pending = None
        self.online = False
        self.last_data_time = None
        self.last_packet_number = None
        self.packets_lost = 0
        self.total_received = 0
        self.status_phase = False
        self.pulse_phase = 0

        self.hist = {k: [] for k in ["time", "temperature", "humidity", "pressure", "gas"]}

        self.c = {
            "bg": "#080d18",
            "panel": "#0f1726",
            "panel2": "#111c2d",
            "panel_hover": "#152338",
            "border": "#1e2d43",
            "text": "#edf3fb",
            "muted": "#91a2b9",
            "accent": "#43b8ff",
            "accent2": "#6c7cff",
            "green": "#32d583",
            "red": "#ff647c",
            "gold": "#f6c85f",
            "grid": "#223249",
        }

        self.setup_style()
        self.build()
        self.load_history()
        self.refresh_ports()
        self.update_clock()
        self.process_queue()
        self.animate_status()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    # ---------- Styling ----------
    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=self.c["bg"], foreground=self.c["text"])
        style.configure("TFrame", background=self.c["bg"])
        style.configure("Panel.TFrame", background=self.c["panel"])
        style.configure(
            "TCombobox",
            fieldbackground=self.c["panel2"],
            background=self.c["panel2"],
            foreground=self.c["text"],
            bordercolor=self.c["border"],
            arrowcolor=self.c["muted"],
            padding=8,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.c["panel2"])],
            foreground=[("readonly", self.c["text"])],
        )
        style.configure(
            "TButton",
            background=self.c["panel2"],
            foreground=self.c["text"],
            bordercolor=self.c["border"],
            lightcolor=self.c["panel2"],
            darkcolor=self.c["panel2"],
            padding=(16, 9),
            font=("Helvetica", 10, "bold"),
        )
        style.map(
            "TButton",
            background=[("active", self.c["panel_hover"])],
            foreground=[("active", self.c["text"])],
        )

    # ---------- UI ----------
    def build(self):
        # Header
        header = tk.Frame(self.root, bg=self.c["bg"])
        header.pack(fill="x", padx=28, pady=(22, 12))

        left = tk.Frame(header, bg=self.c["bg"])
        left.pack(side="left")

        tk.Label(
            left, text="TerraLink", bg=self.c["bg"], fg=self.c["text"],
            font=("Helvetica", 29, "bold")
        ).pack(anchor="w")

        tk.Label(
            left, text="ENVIRONMENTAL MONITORING  •  V1",
            bg=self.c["bg"], fg=self.c["muted"],
            font=("Helvetica", 10, "bold")
        ).pack(anchor="w", pady=(2, 0))

        right = tk.Frame(header, bg=self.c["bg"])
        right.pack(side="right", anchor="e")

        self.clock = tk.StringVar()
        tk.Label(
            right, textvariable=self.clock, bg=self.c["bg"], fg=self.c["muted"],
            font=("Helvetica", 10)
        ).pack(anchor="e")

        status_row = tk.Frame(right, bg=self.c["bg"])
        status_row.pack(anchor="e", pady=(7, 0))

        self.status_dot = tk.Label(
            status_row, text="●", bg=self.c["bg"], fg=self.c["red"],
            font=("Helvetica", 11, "bold")
        )
        self.status_dot.pack(side="left", padx=(0, 5))

        self.status_text = tk.StringVar(value="OFFLINE")
        self.status_label = tk.Label(
            status_row, textvariable=self.status_text,
            bg=self.c["bg"], fg=self.c["red"],
            font=("Helvetica", 10, "bold")
        )
        self.status_label.pack(side="left")

        # Accent line
        tk.Frame(self.root, bg=self.c["accent"], height=2).pack(
            fill="x", padx=28, pady=(0, 14)
        )

        # Connection bar
        bar = tk.Frame(
            self.root, bg=self.c["panel"],
            highlightbackground=self.c["border"], highlightthickness=1
        )
        bar.pack(fill="x", padx=28, pady=(0, 14))
        bar.grid_columnconfigure(1, weight=1)

        tk.Label(
            bar, text="GATEWAY PORT", bg=self.c["panel"], fg=self.c["muted"],
            font=("Helvetica", 9, "bold")
        ).grid(row=0, column=0, padx=(16, 10), pady=15)

        self.port = tk.StringVar()
        self.combo = ttk.Combobox(
            bar, textvariable=self.port, width=30,
            state="readonly", style="TCombobox"
        )
        self.combo.grid(row=0, column=1, sticky="w", pady=9)

        self.refresh_btn = ttk.Button(
            bar, text="↻  Refresh", command=self.refresh_ports, style="TButton"
        )
        self.refresh_btn.grid(row=0, column=2, padx=(12, 6))

        self.connect_btn = ttk.Button(
            bar, text="Connect", command=self.toggle, style="TButton"
        )
        self.connect_btn.grid(row=0, column=3, padx=6)

        tk.Label(
            bar, text="115200 BAUD", bg=self.c["panel"], fg=self.c["muted"],
            font=("Helvetica", 9, "bold")
        ).grid(row=0, column=4, padx=(15, 8))

        self.count = tk.StringVar(value="0 packets")
        tk.Label(
            bar, textvariable=self.count, bg=self.c["panel"],
            fg=self.c["accent"], font=("Helvetica", 10, "bold")
        ).grid(row=0, column=5, padx=(15, 18))

        # Metric cards
        cards = tk.Frame(self.root, bg=self.c["bg"])
        cards.pack(fill="x", padx=28, pady=(0, 12))

        specs = [
            ("TEMPERATURE", "temperature", "°C"),
            ("HUMIDITY", "humidity", "%"),
            ("PRESSURE", "pressure", "hPa"),
            ("GAS RESISTANCE", "gas", "kΩ"),
            ("BATTERY", "battery", "V"),
            ("RSSI", "rssi", "dBm"),
            ("SNR", "snr", "dB"),
        ]

        self.cv = {}
        self.card_frames = {}

        for i, (title, key, unit) in enumerate(specs):
            cards.grid_columnconfigure(i, weight=1)
            card = tk.Frame(
                cards, bg=self.c["panel"],
                highlightbackground=self.c["border"], highlightthickness=1
            )
            card.grid(row=0, column=i, sticky="nsew", padx=3)

            tk.Frame(card, bg=self.c["accent"], height=2).pack(fill="x")

            inner = tk.Frame(card, bg=self.c["panel"])
            inner.pack(fill="both", expand=True, padx=14, pady=12)

            tk.Label(
                inner, text=title, bg=self.c["panel"], fg=self.c["muted"],
                font=("Helvetica", 9, "bold")
            ).pack(anchor="w")

            value = tk.StringVar(value="—")
            self.cv[key] = value

            tk.Label(
                inner, textvariable=value, bg=self.c["panel"],
                fg=self.c["text"], font=("Helvetica", 23, "bold")
            ).pack(anchor="w", pady=(5, 0))

            tk.Label(
                inner, text=unit, bg=self.c["panel"], fg=self.c["muted"],
                font=("Helvetica", 9)
            ).pack(anchor="w")

            self.card_frames[key] = card
            self.bind_hover(card, inner, key)

        # Fire Risk Panel
#########################################################################################
        risk_frame = tk.Frame(
            self.root,
            bg=self.c["panel"],
            highlightbackground=self.c["border"],
            highlightthickness=1
        )

        risk_frame.pack(
            fill="x",
            padx=28,
            pady=(0, 12)
        )

        tk.Label(
            risk_frame,
            text="FIRE RISK ASSESSMENT",
            bg=self.c["panel"],
            fg=self.c["muted"],
            font=("Helvetica", 10, "bold")
        ).pack(anchor="w", padx=15, pady=(12, 0))

        self.risk_text = tk.StringVar(
            value="LOW"
        )

        self.risk_label = tk.Label(
            risk_frame,
            textvariable=self.risk_text,
            bg=self.c["panel"],
            fg=self.c["green"],
            font=("Helvetica", 28, "bold")
        )

        self.risk_label.pack(
            anchor="w",
            padx=15,
            pady=(5, 12)
        )
#########################################################################################

        battery_panel = tk.Frame(
            self.root,
            bg=self.c["panel"],
            highlightbackground=self.c["border"],
            highlightthickness=1
        )

        battery_panel.pack(
            fill="x",
            padx=28,
            pady=(0,12)
        )

        tk.Label(
            battery_panel,
            text="BATTERY STATUS",
            bg=self.c["panel"],
            fg=self.c["muted"],
            font=("Helvetica",10,"bold")
        ).pack(anchor="w", padx=15, pady=(10,0))

        self.battery_text = tk.StringVar(
            value="Waiting for data..."
        )

        self.battery_label = tk.Label(
            battery_panel,
            textvariable=self.battery_text,
            bg=self.c["panel"],
            fg=self.c["green"],
            font=("Helvetica",22,"bold")
        )

        self.battery_label.pack(
            anchor="w",
            padx=15,
            pady=(3,5)
        )

        self.battery_canvas = tk.Canvas(
            battery_panel,
            bg=self.c["panel"],
            height=18,
            highlightthickness=0
        )

        self.battery_canvas.pack(
            fill="x",
            padx=15,
            pady=(0,12)
        )

        self.battery_bg = self.battery_canvas.create_rectangle(
            0,0,500,18,
            fill="#243447",
            outline=""
        )

        self.battery_fill = self.battery_canvas.create_rectangle(
            0,0,0,18,
            fill=self.c["green"],
            outline=""
        )
######################################################################################
        # Metadata strip
        meta = tk.Frame(
            self.root, bg=self.c["panel"],
            highlightbackground=self.c["border"], highlightthickness=1
        )
        meta.pack(fill="x", padx=28, pady=(0, 12))

        self.node = tk.StringVar(value="Node  —")
        self.pkt = tk.StringVar(value="Packet  —")
        self.last = tk.StringVar(value="Last received  —")
        self.loss = tk.StringVar(value="Lost  0")

        for var in (self.node, self.pkt, self.loss):
            tk.Label(
                meta, textvariable=var, bg=self.c["panel"], fg=self.c["muted"],
                font=("Helvetica", 10, "bold")
            ).pack(side="left", padx=(14, 14), pady=8)

        tk.Frame(meta, bg=self.c["border"], width=1, height=16).pack(
            side="left", pady=8
        )

        self.stream_state = tk.StringVar(value="Waiting for telemetry")
        tk.Label(
            meta, textvariable=self.stream_state, bg=self.c["panel"],
            fg=self.c["muted"], font=("Helvetica", 9)
        ).pack(side="left", padx=14)

        tk.Label(
            meta, textvariable=self.last, bg=self.c["panel"], fg=self.c["muted"],
            font=("Helvetica", 9)
        ).pack(side="right", padx=14, pady=8)

        # Charts
        charts = tk.Frame(self.root, bg=self.c["bg"])
        charts.pack(fill="both", expand=True, padx=28, pady=(0, 22))

        charts.grid_columnconfigure(0, weight=1)
        charts.grid_columnconfigure(1, weight=1)
        charts.grid_rowconfigure(0, weight=1)
        charts.grid_rowconfigure(1, weight=1)

        defs = [
            ("temperature", "Temperature", "°C", 0, 0),
            ("humidity", "Humidity", "%", 0, 1),
            ("pressure", "Pressure", "hPa", 1, 0),
            ("gas", "Gas Resistance", "kΩ", 1, 1),
        ]

        self.fig = {}
        self.ax = {}
        self.line = {}

        for key, title, unit, r, c in defs:
            p = tk.Frame(
                charts, bg=self.c["panel"],
                highlightbackground=self.c["border"], highlightthickness=1
            )
            p.grid(
                row=r, column=c, sticky="nsew",
                padx=(0, 5) if c == 0 else (5, 0),
                pady=(0, 5) if r == 0 else (5, 0)
            )

            title_row = tk.Frame(p, bg=self.c["panel"])
            title_row.pack(fill="x", padx=14, pady=(10, 0))

            tk.Label(
                title_row, text=title, bg=self.c["panel"],
                fg=self.c["text"], font=("Helvetica", 11, "bold")
            ).pack(side="left")

            self.chart_state = tk.StringVar(value="LIVE")
            tk.Label(
                title_row, text="●  LIVE", bg=self.c["panel"],
                fg=self.c["green"], font=("Helvetica", 8, "bold")
            ).pack(side="right")

            fig = Figure(figsize=(5.5, 2.35), dpi=100, facecolor=self.c["panel"])
            ax = fig.add_subplot(111)
            ax.set_facecolor(self.c["panel"])

            ax.tick_params(
                colors=self.c["muted"], labelsize=8,
                length=0, pad=6
            )
            ax.grid(
                True, color=self.c["grid"], alpha=0.65,
                linewidth=0.6, linestyle="-"
            )

            for spine in ax.spines.values():
                spine.set_visible(False)

            ax.set_ylabel(
                unit, color=self.c["muted"], fontsize=8,
                rotation=90, labelpad=8
            )
            ax.set_xticks([])

            # Prevent pressure from using +9.86e2 offset notation.
            formatter = ScalarFormatter(useOffset=False)
            formatter.set_scientific(False)
            ax.yaxis.set_major_formatter(formatter)

            line, = ax.plot([], [], linewidth=2.2)
            fig.tight_layout(pad=1.0)

            canvas = FigureCanvasTkAgg(fig, master=p)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=7, pady=(0, 7))

            self.fig[key] = fig
            self.ax[key] = ax
            self.line[key] = line

    def bind_hover(self, card, inner, key):
        def enter(_):
            card.configure(highlightbackground=self.c["accent"])
            inner.configure(bg=self.c["panel_hover"])
            for child in inner.winfo_children():
                try:
                    child.configure(bg=self.c["panel_hover"])
                except tk.TclError:
                    pass

        def leave(_):
            card.configure(highlightbackground=self.c["border"])
            inner.configure(bg=self.c["panel"])
            for child in inner.winfo_children():
                try:
                    child.configure(bg=self.c["panel"])
                except tk.TclError:
                    pass

        card.bind("<Enter>", enter)
        card.bind("<Leave>", leave)

    # ---------- Serial ----------
    def refresh_ports(self):
        ports = sorted([p.device for p in list_ports.comports()])
        self.combo["values"] = ports

        if ports:
            if self.port.get() not in ports:
                # Prefer a non-Bluetooth serial device.
                preferred = next(
                    (p for p in ports if "Bluetooth" not in p),
                    ports[0]
                )
                self.port.set(preferred)
        else:
            self.port.set("No serial ports found")

    def toggle(self):
        self.disconnect() if self.online else self.connect()

    def connect(self):
        selected = self.port.get()
        if not selected or selected.startswith("No "):
            messagebox.showwarning(
                "Serial port",
                "Select the Gateway ESP32 serial port first."
            )
            return

        try:
            self.ser = serial.Serial(selected, BAUD, timeout=0.5)
            self.stop.clear()
            self.online = True
            self.connect_btn.config(text="Disconnect")
            self.status_text.set("ONLINE")
            self.status_label.configure(fg=self.c["green"])
            self.status_dot.configure(fg=self.c["green"])
            self.stream_state.set("Live telemetry stream active")
            threading.Thread(target=self.reader, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Connection failed", str(e))

    def disconnect(self):
        self.online = False
        self.stop.set()

        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass

        self.ser = None
        self.connect_btn.config(text="Connect")
        self.status_text.set("OFFLINE")
        self.status_label.configure(fg=self.c["red"])
        self.status_dot.configure(fg=self.c["red"])
        self.stream_state.set("Telemetry stream paused")

    def reader(self):
        while not self.stop.is_set():
            try:
                data = self.ser.readline()
                if data:
                    self.parse(data.decode("utf-8", "ignore").strip())
            except Exception as e:
                if not self.stop.is_set():
                    self.q.put(("error", str(e)))
                break

    # ---------- Parsing ----------
    def parse(self, line):
        if line.startswith("Raw packet :"):
            packet = line.split(":", 1)[1].strip()

            pattern = (
                r"NODE=(\d+),PKT=(\d+),"
                r"T=(-?\d+(?:\.\d+)?),"
                r"H=(-?\d+(?:\.\d+)?),"
                r"P=(-?\d+(?:\.\d+)?),"
                r"G=(-?\d+(?:\.\d+)?),"
                r"B=(-?\d+(?:\.\d+)?),"
                r"BP=(-?\d+(?:\.\d+)?)"
            )

            match = re.fullmatch(pattern, packet)

            if match:
                self.pending = {
                    "node_id": int(match[1]),
                    "packet_number": int(match[2]),
                    "temperature": float(match[3]),
                    "humidity": float(match[4]),
                    "pressure": float(match[5]),
                    "gas": float(match[6]),
                    "battery": float(match[7]),
                    "battery_percent": float(match[8]),
                    "rssi": None,
                    "snr": None,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

        elif self.pending:
            if line.startswith("RSSI :"):
                try:
                    self.pending["rssi"] = float(
                        line.split(":", 1)[1].replace("dBm", "").strip()
                    )
                except ValueError:
                    pass

            elif line.startswith("SNR"):
                try:
                    self.pending["snr"] = float(
                        line.split(":", 1)[1].replace("dB", "").strip()
                    )
                except ValueError:
                    pass

            elif line == "Sensor packet : VALID":
                data = self.pending.copy()

                with self.db:
                    self.db.execute(
                        """
                        INSERT INTO readings(
                            timestamp,node_id,packet_number,
                            temperature,humidity,pressure,gas,
                            battery,battery_percent,
                            rssi,snr
                        )
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            data["timestamp"],
                            data["node_id"],
                            data["packet_number"],
                            data["temperature"],
                            data["humidity"],
                            data["pressure"],
                            data["gas"],
                            data["battery"],
                            data["battery_percent"],
                            data["rssi"],
                            data["snr"]
                        )
                    )

                self.q.put(("reading", data))
                self.pending = None

    # ---------- Data ----------
    def load_history(self):
        rows = self.db.execute(
            """
            SELECT timestamp,temperature,humidity,pressure,gas
            FROM readings
            ORDER BY id DESC LIMIT ?
            """,
            (MAX_POINTS,)
        ).fetchall()

        rows.reverse()

        for row in rows:
            self.hist["time"].append(row[0])
            self.hist["temperature"].append(row[1])
            self.hist["humidity"].append(row[2])
            self.hist["pressure"].append(row[3])
            self.hist["gas"].append(row[4])

        self.update_charts()

###################################################################################
    def calculate_risk(self, t, h, gas):

        score = 0

        if t > 45:
            score += 45
        elif t > 35:
            score += 25

        if h < 25:
            score += 35
        elif h < 40:
            score += 15

        if gas < 10:
            score += 20

        if score < 25:
            return "LOW", self.c["green"]

        elif score < 50:
            return "MEDIUM", self.c["gold"]

        elif score < 75:
            return "HIGH", "#ff8c42"

        else:
            return "CRITICAL", self.c["red"]
 ###############################################################################
        
    def reading(self, data):
        current_pkt = data["packet_number"]

        if self.last_packet_number is not None:
            expected = self.last_packet_number + 1

            if current_pkt > expected:
                self.packets_lost += current_pkt - expected

        self.last_packet_number = current_pkt
        self.total_received += 1

        self.loss.set(f"Lost  {self.packets_lost}")
        

        for key in ["temperature", "humidity", "pressure", "gas","battery", "rssi", "snr"]:
            value = data[key]
            self.cv[key].set("—" if value is None else f"{value:.2f}")

        self.node.set(f"Node  {data['node_id']}")
        self.pkt.set(f"Packet  #{data['packet_number']}")
        self.last.set(f"Last received  {data['timestamp']}")
        self.count.set(f"Packet #{data['packet_number']}")

        self.last_data_time = datetime.now()

        battery_voltage = data["battery"]
        battery_percent = data["battery_percent"]

        self.battery_text.set(
            f"{battery_percent:.0f}%   ({battery_voltage:.2f} V)"
        )

        bar_width = min(
            max(battery_percent * 5, 0),
            500
        )

        self.battery_canvas.coords(
            self.battery_fill,
            0,
            0,
            bar_width,
            18
        )

        if battery_percent > 60:

            color = self.c["green"]

        elif battery_percent > 25:

            color = self.c["gold"]

        else:

            color = self.c["red"]

        self.battery_canvas.itemconfig(
            self.battery_fill,
            fill=color
        )

        self.battery_label.configure(
            fg=color
        )


        self.stream_state.set("Live telemetry stream active")

        risk, color = self.calculate_risk(
            data["temperature"],
            data["humidity"],
            data["gas"]
        )

        self.risk_text.set(risk)

        self.risk_label.configure(
            fg=color
        )

        self.hist["time"].append(data["timestamp"])
        for key in ["temperature", "humidity", "pressure", "gas"]:
            self.hist[key].append(data[key])

        for key in self.hist:
            if len(self.hist[key]) > MAX_POINTS:
                self.hist[key].pop(0)

        self.flash_cards()
        self.update_charts()

    def flash_cards(self):
        # Small, subtle highlight animation on incoming data.
        for card in self.card_frames.values():
            card.configure(highlightbackground=self.c["accent"])

        self.root.after(
            180,
            lambda: [
                card.configure(highlightbackground=self.c["border"])
                for card in self.card_frames.values()
            ]
        )

    def update_charts(self):
        x = list(range(len(self.hist["time"])))

        for key in ["temperature", "humidity", "pressure", "gas"]:
            self.line[key].set_data(x, self.hist[key])
            ax = self.ax[key]

            ax.relim()
            ax.autoscale_view()

            # Keep a little breathing room around the line.
            if self.hist[key]:
                values = self.hist[key]
                lo, hi = min(values), max(values)
                if lo == hi:
                    pad = max(abs(lo) * 0.015, 0.5)
                else:
                    pad = (hi - lo) * 0.12
                ax.set_ylim(lo - pad, hi + pad)

            ax.set_xlim(
                max(0, len(x) - MAX_POINTS),
                max(MAX_POINTS - 1, len(x) - 1)
            )
            ax.set_xticks([])

            self.fig[key].canvas.draw_idle()

    # ---------- Animation / Clock ----------
    def update_clock(self):
        self.clock.set(
            datetime.now().strftime("%d %b %Y  •  %I:%M:%S %p")
        )
        self.root.after(1000, self.update_clock)

    def animate_status(self):
        if self.online:
            self.pulse_phase = (self.pulse_phase + 1) % 2
            self.status_dot.configure(
                fg=self.c["green"] if self.pulse_phase else "#79e7b2"
            )
        else:
            self.status_dot.configure(fg=self.c["red"])

        self.root.after(700, self.animate_status)

    def process_queue(self):
        try:
            while True:
                typ, data = self.q.get_nowait()

                if typ == "reading":
                    self.reading(data)

                elif typ == "error":
                    self.disconnect()
                    messagebox.showerror("Serial error", data)

        except queue.Empty:
            pass

        self.root.after(80, self.process_queue)

    # ---------- Shutdown ----------
    def close(self):
        self.disconnect()
        try:
            self.db.close()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    TerraLinkApp(root)
    root.mainloop()
