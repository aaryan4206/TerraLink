# TerraLink Hardware Design

## 1. Overview

TerraLink is a modular, low-power environmental monitoring system built around two core hardware units:

- A remote sensor node that measures local environmental conditions
- A central gateway that receives sensor data over LoRa and forwards it to a computer

The current V1 prototype is intentionally simple and robust. It uses off-the-shelf development boards and commercially available modules, which keeps the system easy to assemble, debug, and expand for future applications such as forest fire monitoring, agricultural sensing, and remote site surveillance.

---

## 2. System Hardware Architecture

The hardware architecture follows a simple sensing-to-communication pipeline:

1. A BME680 environmental sensor measures temperature, humidity, pressure, and gas resistance.
2. An ESP32 microcontroller reads the sensor data and packages it into telemetry.
3. A Ra-02 LoRa module transmits the data wirelessly at 433 MHz.
4. A second ESP32 + Ra-02 combination receives the packet at the gateway.
5. The gateway relays the data over USB serial to a Python-based dashboard for visualization and storage.

```text
       Sensor Node                    Radio Link                    Gateway
--------------------------------------------------------------------------------------
BME680 --> ESP32 --> Ra-02 (LoRa) --------------------> Ra-02 --> ESP32 --> USB --> PC
```

---

## 3. Primary Hardware Components

### 3.1 ESP32 Microcontroller

The ESP32 is used as the main controller on both the node and the gateway because it provides:

- Built-in Wi-Fi and Bluetooth for future expansion
- Dual-core processing capability
- Multiple GPIO pins for sensor and radio interfacing
- USB serial support for debugging and data output
- Good power efficiency for battery-powered field use

The current implementation uses standard ESP32 development boards with GPIO-based peripheral connections.

### 3.2 BME680 Environmental Sensor

The BME680 is a combined temperature, humidity, pressure, and gas sensor. It is well suited to environmental monitoring because it provides:

- Temperature measurement
- Relative humidity measurement
- Atmospheric pressure measurement
- Air quality / gas resistance measurement

This makes it useful not only for climate tracking but also for basic environmental anomaly detection.

### 3.3 Ra-02 LoRa Module

The Ra-02 module is a low-cost SX1278-based LoRa transceiver operating in the 433 MHz band. It provides:

- Long-range wireless communication
- Low power consumption
- Good performance for remote monitoring applications
- Reliability in outdoor and sparse deployment areas

In the current prototype, both the sensor node and the gateway use a Ra-02 module and are configured for the same frequency and LoRa settings to communicate with each other.

---

## 4. Node Hardware Design

### 4.1 Sensor Node Functional Blocks

The node consists of:

- ESP32 development board
- BME680 sensor module
- Ra-02 LoRa module
- Power source (prototype power supply / battery support)
- Wiring for SDA/SCL, SPI, and power rails

### 4.2 Node Wiring Overview

The implemented firmware shows the following pin mapping:

| Component | Signal | ESP32 GPIO |
| --- | --- | --- |
| BME680 | SDA | 21 |
| BME680 | SCL | 22 |
| Ra-02 | SS | 5 |
| Ra-02 | RST | 14 |
| Ra-02 | DIO0 | 26 |
| Ra-02 | SCK | 18 |
| Ra-02 | MISO | 19 |
| Ra-02 | MOSI | 23 |

This design uses the ESP32's hardware SPI peripheral for the LoRa module and the I2C bus for the BME680 sensor.

### 4.3 Node Power Considerations

For field deployment, the node should be powered by a stable DC source, typically:

- USB power during development
- Li-ion battery or regulated DC source for outdoor operation
- Appropriate power filtering and voltage regulation for the ESP32 and sensor module

The ESP32 and sensor can operate from a 3.3 V logic domain, while the Ra-02 module also uses 3.3 V logic and should not be connected directly to 5 V signals without proper level handling.

### 4.4 Node Packaging Considerations

The node is intended for environmental deployment and should be mounted with attention to:

- Sensor exposure to ambient air
- Protection from direct rain and dust
- Adequate ventilation around the BME680
- Antenna placement away from metal surfaces
- Stable mounting in a weather-resistant enclosure

---

## 5. Gateway Hardware Design

### 5.1 Gateway Functional Blocks

The gateway includes:

- ESP32 development board
- Ra-02 LoRa module
- USB serial connection to host PC
- Optional external power source

### 5.2 Gateway Wiring Overview

The gateway uses the same LoRa SPI connection mapping as the node:

| Component | Signal | ESP32 GPIO |
| --- | --- | --- |
| Ra-02 | SS | 5 |
| Ra-02 | RST | 14 |
| Ra-02 | DIO0 | 26 |
| Ra-02 | SCK | 18 |
| Ra-02 | MISO | 19 |
| Ra-02 | MOSI | 23 |

The gateway does not require the BME680 sensor because its role is to receive telemetry and pass it along to the computer.

### 5.3 Gateway Role in the System

The gateway is the bridge between field-deployed LoRa devices and the software stack. It receives packets, parses the payload, and exposes the information over serial so a desktop dashboard can process and visualize the data.

---

## 6. RF and Communication Hardware Details

### 6.1 LoRa Configuration

The current prototype uses:

- Frequency: 433 MHz
- Spreading Factor: 7
- Bandwidth: 125 kHz
- Coding Rate: 4/5
- CRC: Enabled
- TX power: 17 dBm

These settings are suitable for early-stage development and testing. They provide a practical balance between range, reliability, and simplicity.

### 6.2 Antenna Considerations

For reliable long-range operation, the antenna and placement matter significantly. Recommended practices include:

- Use a proper 433 MHz antenna matched to the Ra-02 module
- Keep the antenna away from the ESP32 and sensor wiring
- Minimize unnecessary cable length in the RF path
- Place the antenna vertically for best field performance
- Test with a range evaluation in the intended deployment environment

---

## 7. Enclosure and Physical Layout

The V1 prototype is intended to be modular and easy to service. A practical enclosure design should include:

- A sealed or semi-sealed body for outdoor use
- Ventilation for the BME680 sensor
- Weatherproof entry for the antenna and power leads
- Mounting points for wall or pole installation
- Cable strain relief and stable connectors

The node should be installed in a way that keeps the sensor exposed to open air while protecting the electronics from direct weather exposure.

---

## 8. BOM (Prototype Level)

The current V1 system is built from the following key components:

- ESP32 development board (x2)
- RA-02 LoRa module (x2)
- BME680 environmental sensor module (x1)
- Breadboard or perfboard for prototyping
- Jumper wires / header pins
- 3.3 V power supply or battery regulator
- USB cable for gateway connection
- Optional enclosure, antenna, and mounting hardware

---

## 9. Design Notes and Limitations

The current prototype is a functional proof of concept, and several hardware improvements are possible in later versions:

- Add regulated power protection and battery charging circuitry
- Use a dedicated PCB instead of breadboard wiring
- Add weatherproof enclosure and cable seal design
- Improve antenna placement and RF shielding
- Add watchdog/reset circuitry for field reliability
- Add fail-safe power switching and low-battery detection
- Introduce additional sensors for future environmental warning applications

---

## 10. Future Hardware Expansion

The TerraLink hardware platform is designed to support future network growth. Potential expansion paths include:

- Multiple sensor nodes connected to one gateway
- Mesh or multi-hop communication patterns
- More robust outdoor packaging
- Solar-powered node deployments
- Additional environmental sensors for fire-risk monitoring
- Remote data uplink through cellular or Wi-Fi in later versions

This makes the current V1 hardware a solid foundation for a broader environmental sensing network.

---

## 11. Summary

The TerraLink hardware design is intentionally simple but effective: an ESP32 node with a BME680 sensor and Ra-02 LoRa radio, paired with an ESP32 gateway that receives LoRa packets and forwards them over USB serial. This architecture is low-cost, modular, and well suited for remote environmental monitoring and future early-warning applications.

The prototype demonstrates the complete hardware path needed for the TerraLink system and establishes a clear foundation for version 2 improvements in robustness, deployment readiness, and network scalability.
