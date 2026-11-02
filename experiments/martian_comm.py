import socket
import struct
import time
import sys
import os

TARGET = os.environ.get("MARTIAN_MAC", "60:0F:77:03:DB:00")

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

def connect_rfcomm():
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
    s.settimeout(5.0)

    print(f"[*] Attempting to connect to Martian RFCOMM Channel 1 ({TARGET})...")
    s.connect((TARGET, 1))
    print("[+] CONNECTED TO WATCH RFCOMM CHANNEL 1!")
    return s

def send_and_recv(s, cmd_bytes, wait_sec=0.2):
    print(f"\n[TX] Sent: {cmd_bytes} (hex: {cmd_bytes.hex()})")
    s.send(cmd_bytes)
    time.sleep(wait_sec)
    try:
        data = s.recv(1024)
        print(f"[RX] Recv: {data} (hex: {data.hex()})")
        return data
    except socket.timeout:
        print("[RX] Timeout: no response.")
        return None

def main():
    try:
        s = connect_rfcomm()
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        print("[-] Ensure the watch is in 'Pair from app' mode to enable radio.")
        sys.exit(1)

    s.settimeout(2.0)

    # 1. Read greeting packet if present
    try:
        init_data = s.recv(1024)
        print(f"[RX-INIT] Watch greeting: {init_data} ({init_data.hex()})")
    except socket.timeout:
        pass

    # 2. Probe baseline commands
    probes = [
        b"<?>",
        b"<I>",
        b"<B>",
        b"<S>",
        b"<V>",
        b"<T>",
        b"<M:Hello Martian>",
        b"<T:20261102094500>",
    ]

    for p in probes:
        send_and_recv(s, p)

    print("\n[*] Holding connection for 3s...")
    time.sleep(3)
    s.close()
    print("[+] Connection closed safely.")

if __name__ == "__main__":
    main()
