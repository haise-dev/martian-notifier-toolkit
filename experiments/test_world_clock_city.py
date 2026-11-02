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
        print(f"TX [0x{op:02X}] len={len(payload)}: {pkt.hex()} -> RX: {resp.hex()}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}]: Timeout")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.5)
    now = time.localtime()

    print("\n--- 1. Injecting UTC Timestamp into Opcode 0x29 ---")
    send(s, 0x29, struct.pack(">I", int(time.time())))

    print("\n--- 2. Injecting RTC Time [YY, MM, DD, HH, MM, SS] into Opcode 0x2A ---")
    send(s, 0x2A, bytes([now.tm_year % 100, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec]))

    print("\n--- 3. Testing Opcode 0x2C (City Name / Timezone identifier) ---")
    send(s, 0x2C, b"HANOI")
    send(s, 0x2C, b"LOCAL\x00")
    send(s, 0x2C, bytes([0x01]) + b"HANOI")

    print("\n--- 4. Testing Opcode 0x2D with City / Timezone parameters ---")
    send(s, 0x2D, b"HANOI")
    send(s, 0x2D, bytes([0x01, 0x07]) + b"HANOI")

    print("\n--- 5. Testing Opcodes 0x30, 0x31, 0x33, 0x34 with city strings ---")
    for op in [0x30, 0x31, 0x33, 0x34]:
        send(s, op, b"HANOI")

    print("\n--- 6. Testing World Clock activation on 0x32 ---")
    send(s, 0x32, bytes([0x01, 0x07, 0x00]))
    send(s, 0x32, bytes([0x01, 0x00, 0x07]))
    send(s, 0x32, b"HANOI\x00")

    time.sleep(2)
    s.close()
    print("\n[+] City string and time register probing complete.")

if __name__ == "__main__":
    main()
