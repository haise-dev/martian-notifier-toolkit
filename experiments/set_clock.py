import socket
import struct
import time
import sys
import os

TARGET = os.environ.get("MARTIAN_MAC", "60:0F:77:03:DB:00")

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

def connect_with_retry(timeout_sec=20.0):
    start = time.time()
    print("[*] Waiting for connection... (Put watch into 'Pair from app' mode)")
    while time.time() - start < timeout_sec:
        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
            s.settimeout(2.0)
            s.connect((TARGET, 1))
            print("\n[+] CONNECTED SUCCESSFULLY!")
            return s
        except Exception:
            s.close()
            time.sleep(0.4)
            print(".", end="", flush=True)
    return None

def send_pkt(s, op, data=b""):
    seq = 0x00
    pkt = bytes([0x3C, op, seq, len(data)]) + data + b">"
    s.send(pkt)
    time.sleep(0.08)
    try:
        resp = s.recv(1024)
        print(f"TX [0x{op:02X}]: {pkt.hex()} -> RX: {resp.hex()}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}]: {pkt.hex()} -> Timeout")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.4)
    now = time.localtime()
    hour = now.tm_hour
    minute = now.tm_min
    sec = now.tm_sec
    month = now.tm_mon
    day = now.tm_mday
    year = now.tm_year % 100

    print(f"\n[*] Configuring: Time {hour:02d}:{minute:02d}:{sec:02d} | Date {day:02d}/{month:02d}/20{year:02d}")

    # 1. Write to Time Register 0x32 (3 bytes: HH MM SS)
    print("\n--- Injecting Time into Opcode 0x32 (3 bytes: HH MM SS) ---")
    send_pkt(s, 0x32, bytes([hour, minute, sec]))

    # 2. Write to Date Register 0x2E (2 bytes: MM DD)
    print("\n--- Injecting Date into Opcode 0x2E (2 bytes: MM DD) ---")
    send_pkt(s, 0x2E, bytes([month, day]))

    # 3. Write to 0x2D (4 bytes: Year, Timezone, flags)
    print("\n--- Injecting into Opcode 0x2D (4 bytes: YYYY / Offset) ---")
    send_pkt(s, 0x2D, bytes([20, year, month, day]))

    # 4. Enable display flag 0x2B
    print("\n--- Setting feature flag 0x2B ---")
    send_pkt(s, 0x2B, bytes([0x01]))
    send_pkt(s, 0x2B, bytes([0x01, 0x01]))

    # 5. Read back registers to verify
    print("\n--- Reading back registers after configuration ---")
    send_pkt(s, 0x32)  # Time
    send_pkt(s, 0x2E)  # Date
    send_pkt(s, 0x2D)  # 0x2D
    send_pkt(s, 0x2B)  # Flag 0x2B

    time.sleep(2)
    s.close()
    print("\n[+] Time and date data successfully transmitted!")

if __name__ == "__main__":
    main()
