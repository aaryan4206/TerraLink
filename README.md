# TerraLink

TerraLink is a modular LoRa-based environmental monitoring system designed for long-range sensing in remote or hard-to-access environments. The project focuses on collecting environmental telemetry from a field sensor node, transmitting it wirelessly through LoRa, and visualizing the data in a desktop dashboard.

The current V1 prototype demonstrates the full sensing pipeline:

- ESP32-based sensor node with BME680 environmental sensor
- Ra-02 LoRa transmitter operating at 433 MHz
- ESP32-based gateway receiver
- Serial relay from gateway to a Python dashboard
- Real-time data visualization and SQLite storage

---

## Project Goals

TerraLink was created to explore a practical, low-cost system for distributed environmental monitoring and future early-warning applications, especially in contexts such as:

- forest fire risk monitoring
- agricultural sensing
- remote weather data collection
- environmental anomaly detection

The V1 system is intentionally simple and modular so that it can serve as a foundation for more advanced monitoring networks in later versions.

---

## System Overview

### Sensor Node

The sensor node is built around an ESP32 and a BME680 sensor. It:

- reads temperature, humidity, pressure, and gas resistance
- formats the values into a telemetry packet
- transmits the packet over LoRa using the Ra-02 module

### Gateway

The gateway uses a second ESP32 and a matching Ra-02 module to:

- receive LoRa packets from the field node
- validate the packet structure
- forward the data over USB serial to a PC

### Dashboard

The Python dashboard receives the serial stream, parses the incoming packets, visualizes live sensor values, and stores telemetry in SQLite for historical analysis.

---

## Hardware Architecture

```text
          Sensor Node                  LoRa Network                   Gateway
-------------------------------------------------------------------------------------------
BME680 -> ESP32 -> Ra-02 (433 MHz) --------------------> Ra-02 -> ESP32 -> USB -> Dashboard
```

The implemented firmware uses the following connections:

- BME680 SDA -> GPIO 21
- BME680 SCL -> GPIO 22
- LoRa SS -> GPIO 5
- LoRa RST -> GPIO 14
- LoRa DIO0 -> GPIO 26
- LoRa SCK -> GPIO 18
- LoRa MISO -> GPIO 19
- LoRa MOSI -> GPIO 23

---

## Repository Structure

```text
TerraLink/
├── README.md
├── LICENSE
├── terralink_dashboard/
│   ├── app.py
│   ├── README.md
│   └── requirements.txt
├── terralink_docs/
│   ├── architecture.md
│   ├── development_log.md
│   ├── hardware.md
│   └── README.md
├── terralink_firmware/
│   ├── gateway/
│   │   └── gateway.ino
│   └── node/
│       └── node.ino
└── terralink_photos/
```

---

## Current Prototype Features

- BME680 environmental sensing
- LoRa telemetry at 433 MHz
- ESP32-based sensor and gateway nodes
- Real-time dashboard monitoring
- SQLite historical storage
- Modular architecture suitable for future expansion

---

## Getting Started

### 1. Flash the firmware

Use the Arduino IDE or platform-compatible ESP32 toolchain to upload:

- `terralink_firmware/node/node.ino` to the sensor node
- `terralink_firmware/gateway/gateway.ino` to the gateway

### 2. Install dashboard dependencies

From the root directory or the dashboard folder:

```bash
cd terralink_dashboard
pip install -r requirements.txt
```

### 3. Run the dashboard

```bash
python app.py
```

The app connects to the gateway serial port, parses valid TerraLink packets, and displays live environmental data.

---

## Data Flow

1. Sensor node reads environmental values from BME680
2. ESP32 packages data into a LoRa packet
3. Gateway receives packet via Ra-02
4. Gateway prints telemetry to USB serial
5. Dashboard reads serial data and stores it locally

---

## Documentation

Additional project documentation is available in the docs folder:

- [terralink_docs/hardware.md](terralink_docs/hardware.md)
- [terralink_docs/architecture.md](terralink_docs/architecture.md)
- [terralink_docs/development_log.md](terralink_docs/development_log.md)

---

## Project Status

This is a V1 prototype focused on validating the complete hardware and software pipeline. It is a working foundation for further development, including improved field durability, broader network scale, and more advanced environmental warning functionality.

---

## License

This project is distributed under the MIT license. See [LICENSE](LICENSE) for details.