# TerraLink System Architecture

## 1. Overview

TerraLink is a modular environmental monitoring platform built around a distributed sensing model. The system is designed to measure environmental conditions at a remote node, transmit those conditions over a long-range wireless link, and present the data through a central software dashboard.

The current V1 implementation is a proof-of-concept focused on validating the full chain:

- sensing at the node
- wireless transmission using LoRa
- reception at the gateway
- serial relay to a desktop dashboard
- display, storage, and signal analysis in software

The architecture intentionally separates the system into independent layers so that each part can be improved or replaced without redefining the whole design.

---

## 2. Architectural Goals

The architecture supports the following goals:

- low-power environmental monitoring in remote locations
- robust long-range communication using LoRa
- simple modular hardware design
- easy firmware debugging and testing
- reliable data visualization and local storage
- extensibility for future forest-fire monitoring and similar deployments

---

## 3. High-Level System Layout

```text
┌──────────────────────────────┐        LoRa 433 MHz          ┌──────────────────────────────┐
│          Sensor Node         │ --------------------------→  │           Gateway            │
│                              │                              │                              │
│  BME680 Sensor               │                              │  Ra-02 LoRa Receiver         │
│  ESP32 Controller            │                              │  ESP32 Controller            │
│  Ra-02 LoRa Transmitter      │                              │                              │
└──────────────────────────────┘                              └──────────────┬───────────────┘
                                                                             │
                                                                             │ USB Serial
                                                                             ▼
                                                                      ┌──────────────────────────────┐
                                                                      │      Dashboard / Software    │
                                                                      │  Serial parser + UI + SQLite │
                                                                      └──────────────────────────────┘
```

---

## 4. System Layers

### 4.1 Sensing Layer

The sensing layer is the remote telemetry source. It is implemented on the node using:

- ESP32 microcontroller
- BME680 environmental sensor
- 3.3 V-compatible power and logic connections

This layer collects:

- temperature
- humidity
- pressure
- gas resistance

The node converts physical measurements into a structured data packet before transmission.

### 4.2 Communication Layer

The communication layer uses a Ra-02 LoRa module operating at 433 MHz. It provides the wireless link between the sensor node and the gateway.

Key parameters currently used in the firmware:

- Frequency: 433 MHz
- Spreading Factor: 7
- Bandwidth: 125 kHz
- Coding Rate: 4/5
- CRC: enabled
- TX power: 17 dBm

This layer is responsible for packet transmission, reception, and radio quality reporting such as RSSI and SNR.

### 4.3 Gateway Layer

The gateway layer receives LoRa packets and passes them to the host system. It contains:

- ESP32 microcontroller
- Ra-02 LoRa receiver
- USB serial output to a desktop computer

The gateway acts as a bridge between the field network and the monitoring software.

### 4.4 Application Layer

The application layer is implemented in Python as a desktop dashboard. It:

- reads the serial stream from the gateway
- parses valid TerraLink packets
- extracts sensor values and radio metrics
- updates the live UI
- stores readings in SQLite

---

## 5. Hardware Interface Architecture

### 5.1 Node Hardware Connections

The node uses a combination of I2C and SPI:

- BME680 communicates over I2C on GPIO 21 and GPIO 22
- LoRa module communicates over SPI using GPIO 18, 19, 23, and SS on GPIO 5
- RST and DIO0 are connected on GPIO 14 and GPIO 26

This is consistent with the current firmware implementation.

### 5.2 Gateway Hardware Connections

The gateway uses the same LoRa SPI configuration as the node:

- SCK: GPIO 18
- MISO: GPIO 19
- MOSI: GPIO 23
- SS: GPIO 5
- RST: GPIO 14
- DIO0: GPIO 26

The gateway does not need the BME680 sensor because its task is to receive packets and forward them.

---

## 6. Data Flow Architecture

The system data flow is linear and easy to trace:

1. The node reads BME680 values.
2. The ESP32 builds a telemetry packet.
3. The Ra-02 module transmits the packet over LoRa.
4. The gateway receives the packet and validates it.
5. The gateway sends the payload to the computer over serial.
6. The dashboard parses the serial line.
7. The dashboard updates live readings and stores them in SQLite.

A typical packet from the current firmware follows this pattern:

```text
NODE=<id>,PKT=<packet_number>,T=<temperature>,H=<humidity>,P=<pressure>,G=<gas>
```

The dashboard then receives separate radio-quality lines such as RSSI and SNR before final validation.

---

## 7. Software Architecture

### 7.1 Node Firmware

The node firmware is responsible for:

- I2C initialization of the BME680
- sensor configuration and calibration
- data acquisition
- packet formatting
- LoRa transmission scheduling
- radio configuration and reliability checks

It is the producer of telemetry in the system.

### 7.2 Gateway Firmware

The gateway firmware is responsible for:

- LoRa receiver initialization
- listening for incoming packets
- reading payloads from the radio
- printing readable telemetry and radio diagnostics to serial
- acting as a bridge to the host machine

It is the mediator between the field device and the monitoring software.

### 7.3 Dashboard Software

The dashboard software is responsible for:

- serial communication
- packet parsing and validation
- live metric rendering
- chart plotting
- database writes
- user interaction and connection management

The dashboard is effectively the control and visualization layer of the architecture.

---

## 8. Functional Responsibilities

| Layer | Responsibility | Primary Components |
| --- | --- | --- |
| Sensing | Measure environmental variables | BME680, ESP32 |
| Communication | Send and receive LoRa packets | Ra-02, ESP32, SPI bus |
| Gateway | Receive + forward user data | ESP32, USB serial |
| Presentation | Display and store telemetry | Python dashboard, SQLite |
| Monitoring | Validate operation | RSSI, SNR, packet counters |

---

## 9. Design Constraints and Trade-offs

### 9.1 Low Cost

The prototype uses affordable, widely available modules and simple wiring. This keeps the system easy to reproduce and test.

### 9.2 Energy Awareness

LoRa is selected because it offers lower power consumption than higher-bandwidth wireless communication methods, which makes it well suited to remote sensing nodes.

### 9.3 Simplicity over Robustness

The V1 architecture favors a clear and testable setup instead of field-hardened industrial packaging. This is intentional for early development and evaluation.

### 9.4 Future Expandability

The current design is modular enough to support additional nodes, multiple gateways, enhanced sensor arrays, and more advanced monitoring logic in later versions.

---

## 10. Risks and Engineering Considerations

The architecture must account for several practical issues:

- stable antenna placement for the Ra-02 module
- sensor exposure to open air without damaging electronics
- sufficient power regulation and battery support
- serial communication reliability between gateway and dashboard
- packet validation to reject corrupted or incomplete telemetry
- weatherproofing for real deployment environments

---

## 11. Future Architecture Expansion

The current architecture supports extension in several directions:

- additional sensor nodes on the same LoRa frequency
- multi-node star topology with one central gateway
- solar-powered remote stations
- encrypted or authenticated packet exchange
- cloud or web-based monitoring dashboards
- integration of fire-risk parameters such as temperature spikes, humidity drops, and environmental thresholds

These future improvements build naturally on the current layered design.

---

## 12. Summary

TerraLink follows a clean, modular architecture built around a remote sensing node, a LoRa communications layer, a central gateway, and a Python-based dashboard. Each layer has a clear responsibility, and the current implementation successfully demonstrates the full telemetry chain from field sensor to user-facing monitoring system.

This architecture is intentionally simple enough for a working prototype but scalable enough to evolve into a more complete environmental monitoring and early-warning network.
