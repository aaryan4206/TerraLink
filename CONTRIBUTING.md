# Contributing to TerraLink

Thanks for your interest in improving TerraLink.

## Project overview

TerraLink is a modular LoRa-based environmental monitoring system built around:

- ESP32 sensor node
- BME680 environmental sensor
- Ra-02 LoRa radio
- ESP32 gateway
- Python dashboard and SQLite logging

## Development workflow

1. Fork the repository and create a feature branch.
2. Keep changes focused and clearly scoped.
3. Update relevant documentation when changing architecture, hardware, or usage.
4. Validate Python syntax before submitting changes.
5. Submit a pull request with a clear summary of the change.

## Local setup

```bash
cd TerraLink
python3 -m venv .venv
source .venv/bin/activate
pip install -r terralink_dashboard/requirements.txt
```

## Dashboard run

```bash
cd terralink_dashboard
python app.py
```

## Firmware development

The Arduino firmware is stored in:

- `terralink_firmware/node/node.ino`
- `terralink_firmware/gateway/gateway.ino`

Use the Arduino IDE or ESP32 toolchain to flash the devices.

## Notes

- Keep hardware and software documentation in sync with code changes.
- Log significant changes in `terralink_docs/development_log.md`.
- Avoid committing generated local databases or OS-specific metadata.
