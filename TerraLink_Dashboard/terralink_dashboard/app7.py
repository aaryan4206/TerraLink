import sqlite3
from datetime import datetime, timedelta
import random

import pandas as pd
import plotly.express as px
import streamlit as st

DB = "terralink.db"

st.set_page_config(
    page_title="TerraLink Dashboard",
    page_icon="🌐",
    layout="wide",
)

def get_conn():
    return sqlite3.connect(DB)

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequence INTEGER,
            node_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            pressure REAL,
            gas REAL,
            battery_voltage REAL,
            rssi REAL,
            snr REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            node_id TEXT PRIMARY KEY,
            location TEXT,
            last_seen TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_reading(node_id, sequence, temperature, humidity, pressure, gas,
                battery_voltage, rssi, snr, timestamp=None):
    timestamp = timestamp or datetime.now().isoformat(timespec="seconds")
    conn = get_conn()
    conn.execute("""
        INSERT INTO readings
        (node_id, sequence, timestamp, temperature, humidity, pressure, gas,
         battery_voltage, rssi, snr)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (node_id, sequence, timestamp, temperature, humidity, pressure, gas,
          battery_voltage, rssi, snr))
    conn.execute("""
        INSERT INTO nodes(node_id, location, last_seen)
        VALUES (?, ?, ?)
        ON CONFLICT(node_id) DO UPDATE SET last_seen=excluded.last_seen
    """, (node_id, "Unknown", timestamp))
    conn.commit()
    conn.close()

def load_readings(node_id=None, hours=24):
    cutoff = datetime.now() - timedelta(hours=hours)
    conn = get_conn()

    if node_id and node_id != "All nodes":
        df = pd.read_sql_query(
            "SELECT * FROM readings WHERE node_id=? AND timestamp>=? "
            "ORDER BY timestamp",
            conn, params=(node_id, cutoff.isoformat())
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM readings WHERE timestamp>=? ORDER BY timestamp",
            conn, params=(cutoff.isoformat(),)
        )

    conn.close()
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def get_nodes():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM nodes ORDER BY node_id", conn)
    conn.close()
    return df

def seed_demo_data():
    # Only creates data if the database is empty.
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    conn.close()
    if count:
        return

    now = datetime.now()
    for node_num in range(1, 5):
        node = f"NODE-{node_num:02d}"
        for i in range(72):
            seq = i + 1
            if random.random() < 0.05:
                seq += 1
            t = now - timedelta(minutes=20 * (71 - i))
            temp = 29 + node_num * 0.7 + random.uniform(-1.2, 1.2)
            hum = 70 - node_num * 2 + random.uniform(-5, 5)
            pressure = 1008 + random.uniform(-2, 2)
            gas = 110 + random.uniform(-15, 15)
            battery = 3.95 - (i / 71) * 0.20 + random.uniform(-0.015, 0.015)
            rssi = -78 - node_num * 5 + random.uniform(-4, 4)
            snr = 9 - node_num * 0.8 + random.uniform(-1, 1)
            add_reading(node, seq, temp, hum, pressure, gas, battery, rssi, snr, t.isoformat(timespec="seconds"))

init_db()

st.sidebar.title("🌐 TerraLink")
st.sidebar.caption("Solar-powered LoRa environmental monitoring")

if st.sidebar.button("Load demo data"):
    seed_demo_data()
    st.rerun()

nodes_df = get_nodes()
node_options = ["All nodes"] + nodes_df["node_id"].tolist()
selected_node = st.sidebar.selectbox("Node", node_options)

hours = st.sidebar.selectbox(
    "History",
    [1, 6, 12, 24, 72],
    index=3,
    format_func=lambda x: f"Last {x} hours"
)

df = load_readings(selected_node, hours)

st.title("TerraLink Dashboard")
st.caption("Real-time environmental monitoring and LoRa network diagnostics")

# ---------- Overview ----------
if df.empty:
    st.info("No readings found. Click **Load demo data** to test the dashboard.")
    st.stop()

latest_by_node = (
    df.sort_values("timestamp")
      .groupby("node_id", as_index=False)
      .tail(1)
)

online_cutoff = datetime.now() - timedelta(minutes=5)
online_count = sum(
    pd.to_datetime(t) >= online_cutoff
    for t in latest_by_node["timestamp"]
)

latest = df.sort_values("timestamp").iloc[-1]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Nodes", len(latest_by_node))
c2.metric("Online", online_count)
c3.metric("Temperature", f"{latest['temperature']:.1f} °C")
c4.metric("Battery", f"{latest['battery_voltage']:.2f} V")

st.divider()

# ---------- Node cards ----------
st.subheader("Node Status")
cols = st.columns(min(max(len(latest_by_node), 1), 4))
#################################################################################

lost_packets = 0

# Ensure data is in sequence order
seq_df = df.sort_values("sequence")

# Get all sequence numbers
sequences = seq_df["sequence"].tolist()

# Count missing packets
for i in range(1, len(sequences)):
    gap = sequences[i] - sequences[i - 1]

    if gap > 1:
        lost_packets += gap - 1

received_packets = len(sequences)

total_packets = received_packets + lost_packets

if total_packets > 0:
    packet_loss_percent = (lost_packets / total_packets) * 100
else:
    packet_loss_percent = 0


#################################################################################
for col, (_, row) in zip(cols, latest_by_node.iterrows()):
    last_seen = pd.to_datetime(row["timestamp"])
    online = last_seen >= online_cutoff

    with col:
        st.markdown(f"### {row['node_id']}")
        st.write("🟢 **ONLINE**" if online else "🔴 **OFFLINE**")
        st.metric("Temperature", f"{row['temperature']:.1f} °C")
        st.metric("Humidity", f"{row['humidity']:.1f} %")
        st.write(f"🔋 Battery: **{row['battery_voltage']:.2f} V**")
        st.write(f"📡 RSSI: **{row['rssi']:.0f} dBm**")
        st.write(f"📶 SNR: **{row['snr']:.1f} dB**")
        st.write(f"📦 Packet Loss: **{packet_loss_percent:.2f}%**")
        st.caption(f"Last packet: {last_seen.strftime('%H:%M:%S')}")

st.divider()

# ---------- Graphs ----------
st.subheader("Environmental Data")

g1, g2 = st.columns(2)

with g1:
    temp_fig = px.line(
        df, x="timestamp", y="temperature", color="node_id",
        markers=True, title="Temperature vs Time"
    )
    temp_fig.update_layout(yaxis_title="Temperature (°C)", xaxis_title="")
    st.plotly_chart(temp_fig, use_container_width=True)

with g2:
    hum_fig = px.line(
        df, x="timestamp", y="humidity", color="node_id",
        markers=True, title="Humidity vs Time"
    )
    hum_fig.update_layout(yaxis_title="Humidity (%)", xaxis_title="")
    st.plotly_chart(hum_fig, use_container_width=True)

g3, g4 = st.columns(2)

with g3:
    batt_fig = px.line(
        df, x="timestamp", y="battery_voltage", color="node_id",
        markers=True, title="Battery Voltage"
    )
    batt_fig.update_layout(yaxis_title="Voltage (V)", xaxis_title="")
    st.plotly_chart(batt_fig, use_container_width=True)

with g4:
    rssi_fig = px.line(
        df, x="timestamp", y="rssi", color="node_id",
        markers=True, title="LoRa RSSI"
    )
    rssi_fig.update_layout(yaxis_title="RSSI (dBm)", xaxis_title="")
    st.plotly_chart(rssi_fig, use_container_width=True)

# ---------- Network ----------
st.subheader("Network Diagnostics")

n1, n2, n3, n4 = st.columns(4)

avg_rssi = df["rssi"].mean()
avg_snr = df["snr"].mean()

n1.metric("Average RSSI", f"{avg_rssi:.1f} dBm")
n2.metric("Average SNR", f"{avg_snr:.1f} dB")
n3.metric("Packet Loss", f"{packet_loss_percent:.2f}%")
n4.metric("Packets Stored", f"{len(df):,}")

# ---------- Raw data ----------
with st.expander("View stored readings"):
    st.dataframe(
        df.sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True
    )
