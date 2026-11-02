import socket
import struct
import time
import sys
import os

TARGET = os.environ.get("MARTIAN_MAC", "60:0F:77:03:DB:00")

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

def connect():
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
    s.settimeout(4.0)
    s.connect((TARGET, 1))
    return s

def send(s, pkt_bytes):
    s.send(pkt_bytes)
    time.sleep(0.1)
    try:
        resp = s.recv(1024)
        print(f"TX: {pkt_bytes.hex()} -> RX: {resp.hex()} (ASCII: {resp})")
        return resp
    except socket.timeout:
        print(f"TX: {pkt_bytes.hex()} -> Timeout")
        return None

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

def main():
    s = connect_with_retry(20.0)
    if not s:
        print("\n[-] Connection timed out.")
        sys.exit(1)

    s.settimeout(0.5)

    print("\n--- 1. Querying Firmware Build (Opcode 0x36) ---")
    send(s, bytes([0x3C, 0x36, 0x00, 0x00, 0x3E]))

    print("\n--- 2. Checking Feature Flags Register 0x2B (Read -> Write 0x01 -> Read) ---")
    send(s, bytes([0x3C, 0x2B, 0x00, 0x00, 0x3E]))  # Read
    send(s, bytes([0x3C, 0x2B, 0x00, 0x01, 0x01, 0x3E]))  # Write 0x01
    send(s, bytes([0x3C, 0x2B, 0x00, 0x00, 0x3E]))  # Read back

    print("\n--- 3. Testing Time and RTC on Opcode 0x29 and 0x2A ---")
    now = int(time.time())
    ts = struct.pack(">I", now)
    print(f"Current Epoch timestamp: {now} (hex: {ts.hex()})")
    send(s, bytes([0x3C, 0x29, 0x00, 0x04]) + ts + b">")
    send(s, bytes([0x3C, 0x2A, 0x00, 0x04]) + ts + b">")

    # BCD time: YY MM DD HH MM SS
    bcd = bytes([26, 11, 2, 10, 5, 0])
    send(s, bytes([0x3C, 0x29, 0x00, 0x06]) + bcd + b">")
    send(s, bytes([0x3C, 0x2A, 0x00, 0x06]) + bcd + b">")

    print("\n--- 4. Testing String Push on Opcode 0x29 and 0x2A ---")
    msg = b"HELLO MARTIAN"
    send(s, bytes([0x3C, 0x29, 0x00, len(msg)]) + msg + b">")
    send(s, bytes([0x3C, 0x2A, 0x00, len(msg)]) + msg + b">")

    print("\n[*] Holding connection for 3s...")
    time.sleep(3)
    s.close()
    print("[+] Test complete.")

if __name__ == "__main__":
    main()
