# Martian Notifier Smartwatch - Hardware Reference & Teardown Guide

**Model:** Martian Notifier (Series MN200 / T200)  
**FCC ID:** [X4LT200](https://fccid.io/X4LT200)  
**Manufacturer:** SilverPlus, Inc. / Martian Watches (Irvine, California, USA)  

---

## 1. Component Architecture & Teardown Analysis

The Martian Notifier uses a two-tier modular hardware design that physically isolates the mechanical analog watch from the digital smartwatch motherboard.

```
+-------------------------------------------------------------+
|                     WATCH CRYSTAL & CASE                    |
+-------------------------------------------------------------+
| [Physical Hands]     Hour / Minute / Second (Analog Quartz) |
| [Crown Knob]         Mechanical Stem (Hand Calibration)     |
| [96x16 OLED]         Monochrome Display Panel (Bottom Strip)|
+-------------------------------------------------------------+
|                     DIGITAL PCB ASSEMBLY                    |
|  - SoC:          Qualcomm / CSR CSR8670CG (BGA)             |
|  - Flash:        Macronix MX25U1635E (1.8V 16Mb SPI NOR)    |
|  - Accelerometer:MEMSIC MXC6226XU                           |
|  - Haptic:       Cylindrical ERM Vibration Motor            |
|  - Status LED:   Bicolor (Red / Blue / Green) LED Indicator |
+-------------------------------------------------------------+
|                      DUAL POWER TIER                        |
|  - Digital:      Li-Po Pouch 3.7V 0.44Wh (AE292025P)        |
|  - Analog:       Silver Oxide Coin Cell 1.55V (SR626SW/377) |
+-------------------------------------------------------------+
|                     BACK COVER & GASKET                     |
|  - Micro-USB:    9mm Recessed Charging Port                 |
+-------------------------------------------------------------+
```

### Integrated Circuits (IC) Breakdown:

1. **Main Processing & Bluetooth SoC:**
   - **Part:** Qualcomm / Cambridge Silicon Radio `CSR8670CG`
   - **Architecture:** 80 MHz 32-bit RISC core + 80 MIPS Kalimba 24-bit DSP
   - **Radio:** Dual-Mode Bluetooth 4.0 (BR/EDR + BLE), embedded balun, transmit power up to +10 dBm
   - **Package:** 0.5mm pitch VFBGA

2. **Non-Volatile Storage (SPI NOR Flash):**
   - **Part:** Macronix `MX25U1635E`
   - **Capacity:** 16 Megabits (2 Megabytes)
   - **Operating Voltage:** **1.8V logic level** *(Important: Cannot be dumped with standard 3.3V / 5V programmers without a 1.8V level shifter adapter)*

3. **Motion / Gesture Sensor:**
   - **Part:** MEMSIC `MXC6226XU`
   - **Function:** $\pm 2g$ dual-axis I2C accelerometer used for wrist-turn detection, tap-to-dismiss alerts, and step monitoring.

4. **Display Panel:**
   - **Part:** WiseChip / RitDisplay `PG-9616TSWD`
   - **Resolution:** $96 \times 16$ pixels, monochrome white/blue OLED with embedded display driver.

---

## 2. Dual-Battery Architecture

The Martian Notifier does **not** share battery power between the smart display board and the quartz hands:

| Battery Tier | Chemistry | Model Number | Voltage | Capacity | Function / Power Domain | Life Expectancy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Analog Movement** | Silver Oxide | **`SR626SW`** / **`377`** | 1.55V | ~28 mAh | Dedicated solely to the physical quartz gear train. Completely isolated from USB charging. | **~2 years** continuous |
| **Digital Smartboard** | Lithium-Polymer (Li-Po) | **`AE292025P`** | 3.7V | 0.44 Wh (~118 mAh) | Powers the CSR8670 SoC, OLED panel, vibration motor, and Bluetooth radio. Charged via Micro-USB. | **4–6 days** per charge |

> **Critical Safety Note:** The Micro-USB port charges **only** the 3.7V Li-Po battery. It does **not** charge or power the analog movement battery. If the watch hands stop moving, the `SR626SW` coin cell must be physically replaced.

---

## 3. Step-by-Step Analog Battery (`377 / SR626SW`) Replacement

Replacing the coin cell can be performed at home using basic household tools:

### Required Tools:
- 1x **`SR626SW`** (or **`377`**) 1.55V silver oxide coin cell (Maxell, Murata/Sony, or Renata recommended).
- 1x Thin flat-head jeweler screwdriver or watch case pry tool.
- 1x Wooden toothpick or plastic tweezers *(Do NOT use bare metal tweezers across the battery terminals to prevent short-circuiting)*.

### Procedure:
1. **Open the Snap-On Case Back:**
   - Locate the small indentation notch along the perimeter of the metal case back.
   - Insert the flat blade of the case pry tool and twist gently upward until the back pops loose.
2. **Handle the Li-Po Pouch Safely:**
   - The rectangular Li-Po battery is adhered to the metal back cover with yellow tape.
   - It is connected to the PCB via two delicate wires (**Red = Positive**, **Black = Ground**).
   - Tilt the back cover aside gently. **Do NOT pull or strain these two wires.**
3. **Extract the Depleted Coin Cell:**
   - Locate the circular quartz movement housing embedded under the plastic carrier frame.
   - Use the wooden toothpick to gently slide the small circular `377` coin cell out from under the holding clip.
4. **Insert the New Battery:**
   - Insert the new `SR626SW` coin cell with the **positive side (`+` engraving) facing UP**.
   - Press down gently until it seats snugly into the battery compartment.
5. **Verify Movement Function:**
   - Check the front dial: ensure the crown (right side) is pushed completely in.
   - Verify that the analog second hand has resumed ticking.
6. **Re-seal the Case Back:**
   - Align the circular rubber gasket.
   - Ensure the notch on the case back lines up precisely with the Micro-USB port cutout.
   - Press firmly around the edges until the case snaps completely shut.

---

## 4. Micro-USB Port Hardware Constraint (The 9mm Neck Quirk)

Users frequently report that their Martian Notifier charges but fails to establish a data connection to computers. This is caused by an intentional mechanical design constraint:

- **Recessed Port Depth:** The Micro-USB jack on the watch is recessed inside the plastic housing by approximately **8.5 mm to 9 mm**.
- **Standard USB Cable Flaw:** Standard consumer Micro-USB cable plugs have an exposed metal neck length of only **5.0 mm to 6.0 mm**.
- **Consequence:** A standard short-neck cable will partially insert and make contact with the longer power pins (`VBUS` and `GND`), lighting the charging LED, but will **fail to reach the data pins (`D+` and `D-`)**.
- **Requirement:** For USB enumeration or DFU firmware recovery, you must use an **extended-neck (9mm) Micro-USB cable** or carefully trim 2mm of the rubber collar off a standard Micro-USB cable head.
