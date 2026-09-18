# TerraLink Dashboard

This dashboard is the software interface for the TerraLink environmental monitoring system. It listens to the gateway's USB serial stream, parses valid TerraLink packets, displays live sensor readings, and stores historical data in SQLite.

---

## Purpose

The dashboard provides a real-time view of data received from the field sensor node. It is designed to help with:

- live environmental monitoring
- packet validation and debugging
- signal quality monitoring (RSSI/SNR)
- historical data review
- system verification during prototype testing

---

## Features

- automatic serial port detection
- connection/disconnection toggle
- live telemetry cards for temperature, humidity, pressure, gas, RSSI, and SNR
- plotting of recent sensor trends
- SQLite database logging
- status indicators for connectivity and packet activity

---

## Project Files

```text
terralink_dashboard/
├── app.py
├── README.md
├── requirements.txt
└── terralink.db   (generated when the app runs)
```

---

## Requirements

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Dependencies include:

- pyserial
- matplotlib

---

## Running the Dashboard

From the dashboard directory:

```bash
cd terralink_dashboard
python app.py
```

Once launched:

1. choose the gateway COM/serial port from the dropdown
2. click Connect
3. monitor the live environmental metrics
4. view recent history and packet statistics in the interface

---

## Serial Data Flow

The dashboard expects the gateway to send structured TerraLink telemetry over serial. The app:

- reads the incoming stream
- matches valid telemetry packets using a regular expression parser
- extracts node, packet, sensor, and radio values
- stores readings in SQLite
- updates the UI in real time

---

## Database

The application creates a SQLite table named `readings` automatically when it starts. Data includes:

- timestamp
- node ID
- packet number
- temperature
- humidity
- pressure
- gas resistance
- RSSI
- SNR

---

## Troubleshooting

### No serial port appears

- make sure the gateway is connected via USB
- check that the ESP32 is recognized by the OS
- refresh the port list in the app

### Data is not updating

- confirm the gateway is receiving LoRa packets
- verify the serial baud rate is set to `115200`
- check the gateway firmware and node firmware are running correctly

### App fails to start

- make sure Python dependencies are installed
- verify you are using a compatible Python version
- check whether a port is busy or blocked by another process

---

## Notes

This dashboard is intended for the V1 TerraLink prototype. It is a practical monitoring interface for validating the full system before later iterations add more robust deployment features, extended analysis, and remote/cloud connectivity.
