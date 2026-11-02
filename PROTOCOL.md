# Martian Notifier Smartwatch - Reverse-Engineered Communication Protocol Specification

**Status:** Reverse-Engineered / Functional  
**Target Hardware:** Martian Notifier Smartwatch (Model T200 / MN200)  
**FCC ID:** [X4LT200](https://fccid.io/X4LT200)  
**Main SoC:** Qualcomm / Cambridge Silicon Radio (CSR) `CSR8670CG` (Dual-Mode Bluetooth 4.0)  
**Author:** Community Reverse-Engineering Project  

---

## 1. Architectural Overview & Transport Layers

The Martian Notifier smartwatch features a hybrid dual-system design with a physical quartz movement and a digital sub-board driven by the Qualcomm/CSR8670 Bluetooth SoC. The device communicates across two Bluetooth layers:

1. **Bluetooth Classic (BR/EDR) - RFCOMM (Channel 1):**
   - **Primary Control Channel:** Used by the legacy firmware for device query, time synchronization, status bar configuration, battery reporting, and persistent flash parameters.
   - **Security:** Requires Bluetooth Security Level `BT_SECURITY_MEDIUM` (Authentication and Encryption enabled).
   - **Service UUIDs exposed:** 
     - Human Interface Device (`0x1124`)
     - PnP Information (`0x1200`)
     - Vendor Custom Profile (`0xFFF0`)

2. **Bluetooth Low Energy (BLE 4.0):**
   - **GATT Service:** `dd721820-53a8-11e3-b3d3-0002a5d5c51b`
   - **GATT Characteristic:** `dd721821-53a8-11e3-b3d3-0002a5d5c51b`
     - Properties: `[write-without-response, write, notify]`
     - Descriptors: Client Characteristic Configuration (`0x2902`, handle 4)
   - **Battery Service (Standard):** `0x180F` (Battery Level: `0x2A19`, handle 17)
   - **Device Information Service:** `0x180A` (Handles 25–33)

---

## 2. RFCOMM Serial Packet Framing

All communications across RFCOMM Channel 1 follow a strict binary framing protocol encapsulated between ASCII framing delimiters:

```
+------------+--------+--------+---------------+-----------------+------------+
| SOF (0x3C) | Opcode | SeqNum | Length (0xNN) | Payload (NN B)  | EOF (0x3E) |
+------------+--------+--------+---------------+-----------------+------------+
|   1 byte   | 1 byte | 1 byte |    1 byte     |    0-255 bytes  |   1 byte   |
+------------+--------+--------+---------------+-----------------+------------+
```

### Frame Fields:
- **SOF (Start of Frame):** ASCII `<` (`0x3C`).
- **Opcode:** 1-byte command identifier (`0x00` – `0xFF`).
- **SeqNum:** 1-byte packet sequence tracker (Default: `0x00`).
- **Length:** 1-byte unsigned integer indicating the length of the following payload (`0x00` if payload is empty).
- **Payload:** Raw binary parameters or payload data.
- **EOF (End of Frame):** ASCII `>` (`0x3E`).

---

## 3. Standard Response Opcodes & Status Codes

When the host transmits a command frame, the microcontroller synchronously returns a response frame:

| Response Opcode | Symbol | Meaning | Description |
| :---: | :---: | :---: | :--- |
| `0x03` | **ACK** | Success / Acknowledged | Operation accepted and processed. Packet format: `3c 03 00 00 3e` |
| `0x04` | **NAK** | Unsupported / Rejected | Opcode invalid, payload length mismatch, or command rejected. Packet: `3c 04 00 01 [OP] 3e` |
| `0x09` | **INFO** | Query Response | Response packet carrying requested status or register values |
| `0x45` | **ERR** | Error State | Communication error or buffer boundary fault. Format: `3c 45 00 01 ff 3e` |

---

## 4. Reverse-Engineered Opcode Reference Table

The following register opcodes have been confirmed through hardware probing:

| Opcode | Direction | Payload Length | Description / Payload Format | Verified Return Frame |
| :---: | :---: | :---: | :--- | :--- |
| **`0x0A`** | Host $\to$ Watch | 0 bytes | **Query Battery & Internal Firmware** | `3c 09 00 03 [Maj] [Min] [Bat%] 3e`<br>Example: `3c 09 00 03 05 10 50 3e` (FW 5.16, 80% Pin) |
| **`0x0C`** | Host $\to$ Watch | Variable | **Ping / Buffer Clear / Keep-Alive** | Responds with ACK `3c 03 00 00 3e` |
| **`0x28`** | Host $\to$ Watch | 3 bytes | **World Clock Activation Register**<br>Payload: `[Enable (0/1), Timezone Offset, DST]` | Responds with ACK `3c 03 00 00 3e` when payload is 3 bytes |
| **`0x29`** | Host $\to$ Watch | 4 bytes | **UTC Epoch Timestamp Register**<br>Payload: `uint32_t` Big-Endian (Seconds since Unix Epoch)<br>Internal MCU uses this to calculate weekday (`Mon`..`Sun`) | Responds with ACK `3c 03 00 00 3e` |
| **`0x2A`** | Host $\to$ Watch | 6 bytes | **RTC Calendar / Local Time Register**<br>Payload: `[YY, MM, DD, HH, MM, SS]` | Responds with ACK `3c 03 00 00 3e` |
| **`0x2B`** | Both | 1 byte | **Feature Flags Register**<br>Read: `3c 2b 00 00 3e` | Returns `3c 2b 00 01 00 3e` (`0x00` = default flags) |
| **`0x2D`** | Both | 4 bytes | **Display Typography & Layout Register** | Returns `3c 2d 00 04 00 20 3e 00 3e` |
| **`0x2E`** | Host $\to$ Watch | 2 bytes | **OLED Date Display Register**<br>Payload: `[Month (1-12), Day (1-31)]`<br>Activates OLED date view (e.g. `Mon 2/11`) | Returns `3c 2e 00 02 00 [Day] 3e` |
| **`0x2F`** | Host $\to$ Watch | 48 bytes | **Persistent Flash Configuration Block**<br>Holds vibration rhythm definitions and alert filters | Returns 48-byte NVRAM configuration block |
| **`0x32`** | Both | 3 bytes | **Status Sub-register** | Read/Write register for status items |
| **`0x36`** | Host $\to$ Watch | 0 bytes | **Official Firmware Build Query** | Returns `3c 36 00 02 10 54 3e` (Represents v10.54) |

---

## 5. Persistent Flash Configuration Block (`0x2F`)

Opcode `0x2F` retrieves a 48-byte configuration array stored in the onboard Macronix `MX25U1635E` SPI flash:

```hex
00 00 0A 00 00 0A 00 00 0A 00 00 0A 00 00 0A 00
00 0A 00 00 0A 00 00 10 00 00 10 00 00 10 00 00
10 00 00 10 00 00 10 01 00 10 01 02 C1 00 00 74
```

### Breakdown of Key Offsets:
- **Bytes `[00]` to `[41]`:** Vibration motor pulse rhythms and haptic pattern duty-cycles (repeating `0x0A` and `0x10` step intervals).
- **Byte `[44]` (`0xC1` = `11000001b`):** Display feature bitmask flags.
- **Byte `[47]` (`0x74`):** Checksum byte.

---

## 6. Pairing & Linux BlueZ Integration Pitfalls

### The HID Driver Conflict
When pairing with a modern Linux host under `Android` mode, the watch exposes a classic Bluetooth Human Interface Device (HID) descriptor (`0x1124`). Modern BlueZ installs an input profile handler (`input.c`) that attempts to bind to the watch as a remote mouse/keyboard. 

Because the watch firmware rejects standard HID handshake packets without companion app authorization, BlueZ triggers:
```
bluetoothd: profiles/input/device.c:control_connect_cb() connect to [MAC]: Permission denied (13)
```
This drops the baseband ACL link immediately.

### Permanent Resolution:
Start `bluetoothd` with `-P input` (or drop-in override in `/etc/systemd/system/bluetooth.service.d/no-input.conf`):
```ini
[Service]
ExecStart=
ExecStart=/usr/libexec/bluetooth/bluetoothd -P input
```
Once paired and bonded, the link key is permanently stored in `/var/lib/bluetooth/[ADAPTER]/[WATCH_MAC]/info`, enabling headless RFCOMM connection via standard Python sockets.
