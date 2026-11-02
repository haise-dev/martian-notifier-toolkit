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
    time.sleep(0.12)
    try:
        resp = s.recv(1024)
        print(f"TX [0x{op:02X}]: len={len(payload)} -> RX: {resp.hex() if resp else 'None'}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}]: Timeout")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.5)

    # 1. Read current 48-byte configuration block 0x2F
    print("\n--- 1. Reading configuration block 0x2F ---")
    resp_2f = send(s, 0x2F)
    if not resp_2f or len(resp_2f) < 50:
        print("[-] Failed to read 0x2F")
        s.close()
        sys.exit(1)

    cfg_data = bytearray(resp_2f[4:-1])
    print(f"Current 0x2F block ({len(cfg_data)} bytes): {cfg_data.hex()}")

    # Modify Byte 44
    orig_b44 = cfg_data[44]
    cfg_data[44] = 0xFF  # Attempt to toggle all display feature flags
    print(f"Modified Byte 44 from 0x{orig_b44:02X} to 0x{cfg_data[44]:02X}")

    # Write back 0x2F
    print("\n--- 2. Transmitting updated 0x2F block ---")
    send(s, 0x2F, bytes(cfg_data))

    # Read back to verify
    print("\n--- 3. Reading back 0x2F to check persistence ---")
    read_back = send(s, 0x2F)
    if read_back and len(read_back) >= 50:
        new_b44 = read_back[4:-1][44]
        print(f"[*] Byte 44 after write: 0x{new_b44:02X}")
        if new_b44 == 0xFF:
            print("[SUCCESS] Feature flags successfully stored in flash!")
        else:
            print(f"[*] Byte unchanged: 0x{new_b44:02X}")

    time.sleep(2)
    s.close()
    print("[+] Test complete.")

if __name__ == "__main__":
    main()
