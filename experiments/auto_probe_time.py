#!/usr/bin/env python3
import socket
import struct
import subprocess
import time
import sys
import os

TARGET = os.environ.get("MARTIAN_MAC", "60:0F:77:03:DB:00")

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

def connect_watch(timeout=30.0):
    start = time.time()
    print(f"[*] Connecting to {TARGET}... Press any button on watch to wake radio.")
    while time.time() - start < timeout:
        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
            s.settimeout(2.5)
            s.connect((TARGET, 1))
            print("\n[+] CONNECTED TO WATCH!")
            # Flush initial buffer
            s.settimeout(0.3)
            try:
                s.recv(1024)
            except Exception:
                pass
            return s
        except Exception:
            s.close()
            time.sleep(0.4)
            print(".", end="", flush=True)
    print("\n[-] Connection timed out.")
    return None

def send_packet(s, opcode, payload=b""):
    pkt = bytes([0x3C, opcode, 0x00, len(payload)]) + payload + b">"
    s.send(pkt)
    time.sleep(0.35)  # Safe delay to prevent buffer overflow
    try:
        s.settimeout(0.8)
        resp = s.recv(1024)
        return pkt, resp, resp.hex() if resp else None
    except socket.timeout:
        return pkt, None, "(Timeout)"

def main():
    s = connect_watch(30.0)
    if not s:
        sys.exit(1)

    now = int(time.time())
    lt = time.localtime(now)
    h, m, sec = lt.tm_hour, lt.tm_min, lt.tm_sec
    mon, day, yr = lt.tm_mon, lt.tm_mday, lt.tm_year % 100

    print("\n" + "=" * 60)
    print(f"STARTING STANDARD TIME CONFIGURATION: {h:02d}:{m:02d}:{sec:02d} Date {day:02d}/{mon:02d}/20{yr:02d}")
    print("=" * 60)

    # 1. UTC Timestamp into 0x29 (MCU calculates day of week)
    print("\n[Step 1/6] Injecting Timestamp into 0x29...")
    _, _, h29 = send_packet(s, 0x29, struct.pack(">I", now))
    print(f"-> RX: {h29}")

    # 2. RTC Time [YY, MM, DD, HH, MM, SS] into 0x2A
    print("\n[Step 2/6] Injecting RTC Time [YY, MM, DD, HH, MM, SS] into 0x2A...")
    rtc_data = bytes([yr, mon, day, h, m, sec])
    _, _, h2a = send_packet(s, 0x2A, rtc_data)
    print(f"-> RX: {h2a}")

    # 3. Date [MM, DD] into 0x2E (Triggers OLED date rendering)
    print("\n[Step 3/6] Injecting Date into 0x2E...")
    _, _, h2e = send_packet(s, 0x2E, bytes([mon, day]))
    print(f"-> RX: {h2e}")

    # 4. World Clock on 0x28 (3 bytes: Enable=1, Timezone=+7, DST=0)
    print("\n[Step 4/6] Injecting World Clock into 0x28...")
    _, _, h28 = send_packet(s, 0x28, bytes([0x01, 0x07, 0x00]))
    print(f"-> RX: {h28}")

    # 5. Display flags on 0x2B
    print("\n[Step 5/6] Probing display flag options on 0x2B...")
    for flag_val in [bytes([0x01]), bytes([0x01, 0x01]), bytes([0x00, 0x01])]:
        _, _, h2b = send_packet(s, 0x2B, flag_val)
        print(f"   0x2B {flag_val.hex()} -> RX: {h2b}")

    # 6. Display configuration on 0x32
    print("\n[Step 6/6] Probing display configuration on 0x32...")
    for wc_val in [bytes([0x01, 0x07, 0x00]), bytes([0x01, 0x00, 0x07])]:
        _, _, h32 = send_packet(s, 0x32, wc_val)
        print(f"   0x32 {wc_val.hex()} -> RX: {h32}")

    print("\n" + "=" * 60)
    print("[COMPLETE] Injected 6-step time configuration sequence.")
    print("=" * 60)

    time.sleep(2)
    s.close()

if __name__ == "__main__":
    main()
