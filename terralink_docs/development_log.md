# TerraLink Development Log

This file records the technical decisions, prototype milestones, testing observations, and implementation changes made during the TerraLink project.

Use this log as a project diary for engineering decisions, hardware changes, firmware updates, and software debugging notes.

---

## 1. Purpose of the Log

The development log should store:

- what was built
- what changed over time
- why design decisions were made
- what tests were performed
- what issues were found
- what needs to be improved next

A good project log makes it easier to debug issues, explain design choices, and continue development after time away from the project.

---

## 2. Recommended Entry Format

Each entry should follow this structure:

### Date

### Version / Build

### Objective

### Hardware Changes

### Firmware / Software Changes

### Test Results

### Issues / Bugs Found

### Decisions and Notes

### Next Step

---

## 3. Initial Project Log

### 2026-09-18

### Version / Build

V1 prototype baseline

### Objective

Establish a working TerraLink environmental monitoring system using ESP32, BME680, Ra-02 LoRa, and a Python dashboard.

### Hardware Changes

- Sensor node built around ESP32
- BME680 connected via I2C on GPIO 21 and GPIO 22
- Ra-02 LoRa module connected using SPI with GPIO 18, 19, 23, 5, 14, and 26
- Gateway built with a second ESP32 and matching LoRa module
- Gateway connected to PC through USB serial

### Firmware / Software Changes

- Node firmware configured to read BME680 values and transmit telemetry via LoRa
- Gateway firmware configured to receive LoRa packets and print structured data over serial
- Dashboard implemented to parse serial input, render live metrics, and store data in SQLite

### Test Results

- System architecture verified conceptually and through code structure
- Sensor and radio setup confirmed by firmware configuration and packet flow design
- Dashboard expected to parse packet strings and update live telemetry cards

### Issues / Bugs Found

- No field deployment yet, so environmental durability and antenna optimization remain untested
- Serial parsing depends on stable payload formatting from the gateway firmware
- Node and gateway must remain on the same LoRa channel configuration for communication to succeed

### Decisions and Notes

- Use 433 MHz LoRa in the prototype because it matches the implemented hardware configuration and simplifies early testing
- Keep the system modular and easy to debug before improving hardware robustness
- Use SQLite locally to avoid adding external backend dependencies in V1

### Next Step

- validate node-to-gateway communication in a live test
- verify packet parsing in the dashboard with real serial data
- document hardware pin mapping and enclosure requirements

---

## 4. What to Add Later

As the project evolves, record entries for:

- hardware revisions and PCB changes
- enclosure improvements
- battery or power management updates
- antenna tuning and range testing
- packet structure changes
- firmware issues and fixes
- dashboard UI changes
- calibration procedures
- reliability or field deployment observations
- future feature ideas and design refinements

---

## 5. Example Future Entry

### Date

YYYY-MM-DD

### Version / Build

V1.1 or V2 prototype

### Objective

Describe the goal of the iteration.

### Hardware Changes

- component modifications
- wiring changes
- enclosure or mounting updates

### Firmware / Software Changes

- new features
- bug fixes
- library updates
- configuration changes

### Test Results

- what was measured
- what passed
- what failed

### Issues / Bugs Found

- error descriptions
- root cause
- temporary workaround

### Decisions and Notes

- why it was implemented this way
- what was learned

### Next Step

- the next action item to continue development

---

## 6. Summary

The development log should be a living engineering record. This project is best served by recording not only what was implemented, but also why it was implemented the way it was and what testing or debugging revealed along the way.
