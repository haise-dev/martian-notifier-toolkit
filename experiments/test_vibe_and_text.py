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
    s.settimeout(3.0)
    s.connect((TARGET, 1))
    return s

def send(s, op, payload):
    pkt = bytes([0x3C, op, 0x00, len(payload)]) + payload + b">"
    s.send(pkt)
    time.sleep(0.12)
    try:
        resp = s.recv(1024)
        print(f"TX [0x{op:02X}] len={len(payload)}: {pkt[:15].hex()}... -> RX: {resp.hex()}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}]: Timeout")
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
        sys.exit(1)

    s.settimeout(0.4)

    # Candidate notification payload structures
    text = b"TEST NOTIFIER"
    patterns = [
        # 1. [AppID=0x01, VibeID=0x01, Text]
        bytes([0x01, 0x01]) + text,
        # 2. [AppID=0x00, VibeID=0x01, Text]
        bytes([0x00, 0x01]) + text,
        # 3. [VibeID=0x01, Text]
        bytes([0x01]) + text,
        # 4. [AppID=0x01, Title_len=4, "TEST", Msg_len=8, "NOTIFIER"]
        bytes([0x01, 0x04]) + b"TEST" + bytes([0x08]) + b"NOTIFIER",
        # 5. [Null-terminated title, message]
        b"TEST\x00NOTIFIER\x00",
    ]

    print("\n--- Testing push notifications and vibration across opcodes ---")
    for op in [0x01, 0x02, 0x06, 0x07, 0x0B, 0x0D, 0x0E]:
        for i, p in enumerate(patterns):
            r = send(s, op, p)
            if r and r[1] != 0x04:
                print(f"\n[!!! ACCEPTED !!!] Opcode 0x{op:02X} accepted pattern {i+1}!")
                print(f"Response: {r.hex()}")
                time.sleep(2)
                s.close()
                return

    s.close()
    print("\n[+] Pattern sweep complete.")

if __name__ == "__main__":
    main()
