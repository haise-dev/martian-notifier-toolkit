# Martian Notifier Smartwatch - Reverse Engineering & Restoration Toolkit

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20BlueZ-lightgrey.svg)]()
[![Status](https://img.shields.io/badge/status-Protocol%20Decoded-success.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An open-source reverse-engineering specification and Linux control toolkit for the **Martian Notifier Smartwatch** (FCC ID: `X4LT200`).

Following the shutdown of Martian Watches in 2018 and the removal of their companion apps from modern app stores, this repository documents the watch's binary communication protocols, silicon teardown, and hardware workarounds, allowing users to restore, configure, and communicate with the device on modern operating systems without proprietary cloud services or abandoned companion apps.

---

## Technical Documentation

- **[PROTOCOL.md](PROTOCOL.md)**: Full binary protocol specification, packet framing (`< OP SEQ LEN PAYLOAD >`), complete opcode register table, and flash configuration block (`0x2F`) analysis.
- **[HARDWARE.md](HARDWARE.md)**: Silicon component breakdown (Qualcomm CSR8670, Macronix MX25U1635E, MEMSIC MXC6226XU), dual-battery architecture, step-by-step analog coin cell (`377/SR626SW`) replacement guide, and the 9mm recessed Micro-USB cable requirement.

---

## Key Reverse-Engineering Findings

1. **Dual-Architecture System:**
   - **Mechanical Movement:** Independent analog quartz movement powered by an isolated `SR626SW / 377` (1.55V) coin cell (~2 year lifespan). Time is set physically via the manual crown.
   - **Smart Motherboard:** Qualcomm/CSR `CSR8670CG` SoC + Macronix `MX25U1635E` SPI flash powered by a rechargeable 3.7V 0.44Wh (~118mAh) Li-Po battery charged via Micro-USB.
2. **Dual-Bluetooth Stack:**
   - **Bluetooth Classic RFCOMM (Channel 1):** Main bidirectional binary control link (`BT_SECURITY_MEDIUM`). Handles date syncing, battery telemetry, and firmware queries.
   - **Bluetooth Low Energy (BLE):** Custom GATT service (`dd721820-53a8-11e3-b3d3-0002a5d5c51b`) and characteristic (`dd721821-...`) for low-power notification forwarding and haptic triggers.
3. **Firmware Decoded Features:**
   - Opcode **`0x0A`**: Real-time battery percentage and firmware query (returns `0x05.0x10` internal version + battery `%`).
   - Opcode **`0x36`**: Returns official firmware build revision string (`10.54`).
   - Opcode **`0x29`**: Big-endian Unix Epoch timestamp (microcontroller internally computes and renders the day of the week, e.g., `Mon`).
   - Opcode **`0x2E`**: Injects Month and Day (`[MM, DD]`), successfully rendering the native OLED date display (`Mon 2/11`).
   - Opcode **`0x0C`**: Buffer flush and keepalive ping (responds with ACK `0x03`).

---

## Linux Setup & Pairing Guide

### 1. Requirements
- Linux with BlueZ 5.50+
- Python 3.10+ with `dbus-python` and `pexpect`

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-dbus python3-gi bluez
pip install --break-system-packages pexpect bleak
```

### 2. Resolving the BlueZ HID Driver Conflict
Under the watch's default `Android` mode, the CSR8670 firmware exposes a classic Bluetooth Human Interface Device (HID) descriptor (`0x1124`). When pairing on modern Linux, the BlueZ input plugin erroneously binds to the watch as a remote mouse/keyboard, resulting in:
```
bluetoothd: profiles/input/device.c:control_connect_cb() connect: Permission denied (13)
```

**Fix:** Start `bluetoothd` with `-P input` to disable the input plugin:
```bash
sudo mkdir -p /etc/systemd/system/bluetooth.service.d
sudo tee /etc/systemd/system/bluetooth.service.d/no-input.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/libexec/bluetooth/bluetoothd -P input
EOF

sudo systemctl daemon-reload
sudo systemctl restart bluetooth
```

### 3. Pairing
1. On the watch: Double-click the **Bottom-Left button** to enter Menu $\to$ navigate to **`Setup`** $\to$ select **`Android`** $\to$ select **`Pair from app`** (LED will flash blue).
2. Run the pairing helper:
```bash
python3 pairing/pair_agent.py
```
3. When prompted on the watch screen, press the **Top-Left button** to confirm pairing. The device link key will be permanently stored by BlueZ.

---

## Repository Structure

```text
├── martianctl.py            # Primary CLI tool (telemetry, ping, console, notify)
├── martian_lab.py           # Persistent multi-threaded interactive developer console
├── PROTOCOL.md              # Full binary protocol framing & opcode specification
├── HARDWARE.md              # Silicon teardown, dual-battery guide, 9mm micro-USB quirk
├── README.md                # Project documentation and quickstart guide
├── LICENSE                  # MIT License
├── pairing/                 # BlueZ D-Bus authentication agents & pairing automation
│   ├── martian_agent.py     # Custom BlueZ D-Bus Agent (handles PIN/passkey requests)
│   ├── pair_agent.py        # Automated pairing runner with KeyboardDisplay agent
│   ├── pair.py              # Interactive PIN pairing script
│   └── interactive_pair.py  # User-prompted passkey verification
└── experiments/             # Reverse-engineering fuzzers, probes, and test scripts
    ├── probe_opcodes.py     # 256-byte serial opcode sweeper
    ├── probe_full_range.py  # 0x10-0xFF register probe
    ├── set_clock.py         # Time, date, and layout injector
    ├── auto_probe_time.py   # Safe-delay sequence analyzer
    └── test_*.py            # Subsystem test scripts (vibe, layout, settings)
```

---

## CLI & Tooling Reference

The primary tool is **`martianctl.py`**. You can specify your watch's MAC address via the `--mac` flag or by setting the `MARTIAN_MAC` environment variable:

```bash
# Query hardware telemetry and battery
./martianctl.py info --mac 60:0F:77:03:DB:00

# Ping watch (checks for ACK 0x03)
./martianctl.py ping

# Enter persistent interactive session (prevents connection timeout)
./martianctl.py console
```

### Persistent Live Lab (`martian_lab.py`):
For developers exploring new opcodes without being dropped by the watch's 20-second idle timeout, `martian_lab.py` maintains an active background keep-alive thread:

```bash
./martian_lab.py [OPTIONAL_MAC]
```
Inside the lab prompt:
- `time`: Injects system time, timestamp, and calendar date.
- `date <MM> <DD>`: Injects custom month and day.
- `probe <opcode_hex>`: Sweeps payload lengths (1–16 bytes) against an opcode to discover input acceptance.
- `send <opcode_hex> [data_hex]`: Sends arbitrary framed binary packets.

---

## Project Status & Community Roadmap

- [x] Silicon teardown and dual-power identification.
- [x] BlueZ pairing and authentication bypass.
- [x] RFCOMM Channel 1 serial protocol framing decoding.
- [x] Battery telemetry, firmware version query, and date injection (`Mon 2/11`).
- [ ] Pull-request to **[Gadgetbridge](https://github.com/Freeyourgadget/Gadgetbridge)** to provide an out-of-the-box open-source Android driver.
- [ ] Lightweight Web Bluetooth (PWA) client for modern iOS (iPhone) and desktop Chrome.

---

## License

This project is released under the [MIT License](LICENSE).  
Hardware and brand names are trademarks of their respective owners and are referenced strictly for interoperability, preservation, and educational purposes.
