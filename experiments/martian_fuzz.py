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

def main():
    print("[*] Waiting for watch to wake... Press Bottom-Left button on watch!")

    s = None
    connected = False
    start_time = time.time()

    while time.time() - start_time < 20.0:
        try:
            subprocess.run(["bluetoothctl", "connect", TARGET], capture_output=True, timeout=3)
        except Exception:
            pass

        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
            s.settimeout(2.0)
            s.connect((TARGET, 1))
            connected = True
            print("\n[+] CONNECTED TO RFCOMM CHANNEL 1!")
            break
        except Exception:
            s.close()
            time.sleep(0.5)
            print(".", end="", flush=True)

    if not connected:
        print("\n[-] Connection timed out after 20s.")
        sys.exit(1)

    s.settimeout(0.3)
    letters = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?"

    test_framings = [
        ("Short", b"<", b">"),
        ("Standard", b"<", b"\x00\x00>"),
        ("Param0", b"<", b"\x00\x01\x00>"),
        ("Param1", b"<", b"\x00\x01\x01>"),
    ]

    recognized_cmds = []

    for name, prefix, suffix in test_framings:
        print(f"\n[*] Testing framing: {name} (Pattern: {prefix}[C]{suffix})")
        for b in letters:
            pkt = prefix + bytes([b]) + suffix
            try:
                s.send(pkt)
                time.sleep(0.04)
                resp = s.recv(1024)
                print(f"[RECOG] Command: {chr(b)} -> Response: {resp} (hex: {resp.hex()})")
                recognized_cmds.append((chr(b), name, pkt.hex(), resp.hex()))
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Error: {e}")
                break

    print("\n" + "=" * 60)
    print("SUMMARY OF COMMANDS WITH WATCH RESPONSES:")
    for cmd, fmt, p_hex, r_hex in recognized_cmds:
        print(f"- Command '{cmd}' ({fmt}): Sent {p_hex} -> Recv {r_hex}")
    print("=" * 60)

    s.close()

if __name__ == "__main__":
    main()
