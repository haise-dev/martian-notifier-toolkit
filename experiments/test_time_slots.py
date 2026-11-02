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

def send(s, op, payload=b""):
    pkt = bytes([0x3C, op, 0x00, len(payload)]) + payload + b">"
    s.send(pkt)
    time.sleep(0.1)
    try:
        resp = s.recv(1024)
        print(f"TX [0x{op:02X}]: {pkt.hex()} -> RX: {resp.hex()}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}]: Timeout")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.5)

    h, m, s_sec = 10, 35, 0
    print(f"\n[*] Injecting test time {h}:{m} into register candidates...")

    # 1. Probe 0x2E: [Hour, Minute] = [10, 35]
    print("\n--- 1. Injecting [10, 35] into Opcode 0x2E ---")
    send(s, 0x2E, bytes([h, m]))

    # 2. Probe 0x32: [10, 35, 0]
    print("\n--- 2. Injecting [10, 35, 0] into Opcode 0x32 ---")
    send(s, 0x32, bytes([h, m, s_sec]))

    # 3. Probe 0x2D: [10, 35, 0, 0]
    print("\n--- 3. Injecting [10, 35, 0, 0] into Opcode 0x2D ---")
    send(s, 0x2D, bytes([h, m, s_sec, 0]))

    # 4. Probe 0x2A: [26, 11, 2, 10, 35, 0]
    print("\n--- 4. Injecting [26, 11, 2, 10, 35, 0] into Opcode 0x2A ---")
    send(s, 0x2A, bytes([26, 11, 2, h, m, s_sec]))

    time.sleep(2)
    s.close()
    print("\n[+] Slot injection complete.")

if __name__ == "__main__":
    main()
