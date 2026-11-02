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
        print(f"TX [0x{op:02X}] {payload.hex()} -> RX: {resp.hex()}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}] -> Timeout")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.5)

    # 1. Inject timestamp into 0x29
    now_utc = int(time.time())
    ts_bytes = struct.pack(">I", now_utc)
    print(f"\n--- 1. Inject UTC Timestamp ({now_utc}) into Opcode 0x29 ---")
    send(s, 0x29, ts_bytes)

    # 2. Inject Date (Month 11, Day 02) into 0x2E
    print("\n--- 2. Inject Date (Month 11, Day 02) into Opcode 0x2E ---")
    send(s, 0x2E, bytes([11, 2]))

    # 3. Configure World Clock on 0x32
    print("\n--- 3. Inject World Clock configuration into Opcode 0x32 ---")
    send(s, 0x32, bytes([0x01, 0x07, 0x00]))

    # 4. Read back state
    print("\n--- 4. Reading back register states ---")
    send(s, 0x32)  # Read 0x32
    send(s, 0x2E)  # Read 0x2E

    time.sleep(2)
    s.close()
    print("\n[+] Sync sequence completed successfully!")

if __name__ == "__main__":
    main()
