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

def connect_with_retry(timeout_sec=20.0):
    start = time.time()
    print("[*] Waiting for watch to wake... Press Bottom-Left button on watch!")
    while time.time() - start < timeout_sec:
        subprocess.run(["bluetoothctl", "connect", TARGET], capture_output=True, timeout=2)
        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
            s.settimeout(2.0)
            s.connect((TARGET, 1))
            print("\n[+] CONNECTED TO WATCH ON RFCOMM CH 1!")
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

    s.settimeout(0.06)
    valid_responses = {}

    print("\n[*] Probing 256 opcodes (0x00 - 0xFF)...")
    for op in range(256):
        # Packet: < OP SEQ(0) LEN(0) >
        pkt = bytes([0x3C, op, 0x00, 0x00, 0x3E])
        try:
            s.send(pkt)
            time.sleep(0.02)
            resp = s.recv(1024)
            resp_type = resp[1] if len(resp) > 1 else None
            payload = resp[4:-1] if len(resp) > 5 else resp

            # If resp_type is not 0x04 (0x04 is NAK / unsupported)
            if resp_type != 0x04:
                print(f"[SPECIAL] OP 0x{op:02X} -> Resp Type: 0x{resp_type:02X} | {resp.hex()} | Data: {payload}")

            valid_responses[op] = (resp_type, resp.hex(), payload)
        except socket.timeout:
            pass
        except Exception as e:
            print(f"Error at 0x{op:02X}: {e}")
            break

    print("\n" + "=" * 60)
    print(f"SUMMARY: Received responses from {len(valid_responses)} opcodes.")
    special = [f"0x{op:02X}" for op, (t, _, _) in valid_responses.items() if t != 0x04]
    print(f"Special opcodes (non-NAK): {special}")
    print("=" * 60)
    s.close()

if __name__ == "__main__":
    main()
