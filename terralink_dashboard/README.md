# TerraLink Dashboard

A first-version Python dashboard for the TerraLink solar-powered LoRa environmental monitoring project.

## Current architecture

ESP32 sensor node
-> LoRa
-> Python receiver (to be added)
-> SQLite database
-> Streamlit dashboard
-> historical graphs / node status / network diagnostics

## Features in this version

- SQLite database for historical readings
- Multiple-node support
- Node online/offline status
- Temperature and humidity graphs
- Battery voltage graph
- LoRa RSSI graph
- SNR display
- Raw database table
- Demo data generator

## Run it

1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Install dependencies:

   pip install -r requirements.txt

4. Start the dashboard:

   streamlit run app.py

5. Open the address shown by Streamlit in your browser.

Click "Load demo data" in the sidebar to see the dashboard before connecting the real TerraLink receiver.

## Next development step

Replace the demo-data path with a serial receiver that reads packets from the ESP32/LoRa gateway and calls:

add_reading(
    node_id,
    temperature,
    humidity,
    pressure,
    gas,
    battery_voltage,
    rssi,
    snr
)

That will make the same dashboard display real TerraLink data.
