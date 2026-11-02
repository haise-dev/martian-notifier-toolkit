#!/usr/bin/env python3
import socket
import struct
import subprocess
import time
import sys
import os
import argparse
import readline

DEFAULT_MAC = os.environ.get("MARTIAN_MAC", "60:0F:77:03:DB:00")

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

class MartianWatch:
    def __init__(self, mac=DEFAULT_MAC):
        self.mac = mac
        self.sock = None

    def connect(self, timeout=25.0):
        start = time.time()
        print(f"[*] Searching and connecting to {self.mac}...")
        while time.time() - start < timeout:
            try:
                subprocess.run(["bluetoothctl", "connect", self.mac], capture_output=True, timeout=2)
            except Exception:
                pass

            try:
                s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
                s.settimeout(2.0)
                s.connect((self.mac, 1))
                self.sock = s
                print(f"\n[+] Successfully connected to RFCOMM Channel 1!")
                # Flush greeting buffer
                self.sock.settimeout(0.3)
                try:
                    self.sock.recv(1024)
                except Exception:
                    pass
                return True
            except Exception:
                s.close()
                time.sleep(0.4)
                print(".", end="", flush=True)

        print("\n[-] Connection timed out. Make sure the watch is in 'Pair from app' mode.")
        return False

    def send_packet(self, opcode, payload=b""):
        if not self.sock:
            raise RuntimeError("Not connected to watch.")
        seq = 0x00
        length = len(payload)
        pkt = bytes([0x3C, opcode, seq, length]) + payload + b">"
        self.sock.send(pkt)
        time.sleep(0.12)
        try:
            self.sock.settimeout(0.8)
            resp = self.sock.recv(1024)
            return resp
        except socket.timeout:
            return None

    def get_info(self):
        resp = self.send_packet(0x0A)
        if not resp or len(resp) < 7:
            return None
        v_major = resp[4]
        v_minor = resp[5]
        battery = resp[6]
        return {
            "firmware": f"{v_major}.{v_minor:02d}",
            "battery_pct": battery,
            "raw_hex": resp.hex()
        }

    def ping(self):
        resp = self.send_packet(0x0C)
        return resp is not None and len(resp) >= 5 and resp[1] == 0x03

    def send_notification(self, msg):
        payload = msg.encode("utf-8")
        results = {}
        for op in [0x01, 0x02, 0x06, 0x07, 0x0B, 0x0D, 0x0E]:
            r = self.send_packet(op, payload)
            if r:
                results[f"0x{op:02X}"] = r.hex()
        return results

    def sync_time(self):
        now = int(time.time())
        ts_le = struct.pack("<I", now)
        ts_be = struct.pack(">I", now)
        lt = time.localtime(now)
        bcd = bytes([
            lt.tm_year // 100, lt.tm_year % 100,
            lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec
        ])

        results = {}
        for op in [0x08, 0x0B, 0x0C, 0x0E, 0x0F, 0x10, 0x12]:
            for p_name, p_data in [("Unix_LE", ts_le), ("Unix_BE", ts_be), ("BCD", bcd)]:
                r = self.send_packet(op, p_data)
                if r and r[1] != 0x04:
                    results[f"0x{op:02X}_{p_name}"] = r.hex()
        return results

    def send_raw(self, hex_str):
        raw = bytes.fromhex(hex_str.replace(" ", ""))
        self.sock.send(raw)
        time.sleep(0.12)
        try:
            self.sock.settimeout(0.8)
            resp = self.sock.recv(1024)
            return resp.hex()
        except socket.timeout:
            return "(No response)"

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

def run_console(watch):
    print("=" * 60)
    print("MARTIAN NOTIFIER INTERACTIVE CONSOLE")
    print("Available commands:")
    print("  info          - Read firmware version and battery %")
    print("  ping          - Send keepalive ping (checks for ACK 0x03)")
    print("  notify <text> - Send notification string to OLED display")
    print("  sync          - Test time synchronization routines")
    print("  raw <hex>     - Send arbitrary framed hex bytes (e.g. 3c0a00003e)")
    print("  exit / quit   - Close connection and exit")
    print("=" * 60)

    while True:
        try:
            cmd_line = input("\nmartianctl> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting console...")
            break

        if not cmd_line:
            continue

        parts = cmd_line.split(" ", 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("exit", "quit", "q"):
            break
        elif cmd == "ping":
            if watch.ping():
                print("[SUCCESS] Ping OK (ACK 0x03)!")
            else:
                print("[-] Ping did not receive ACK.")
        elif cmd == "info" or cmd == "battery":
            data = watch.get_info()
            if data:
                print(f"[+] Firmware: {data['firmware']} | Battery: {data['battery_pct']}% | Raw: {data['raw_hex']}")
            else:
                print("[-] Failed to read info.")
        elif cmd == "notify":
            msg = arg if arg else "Hello Martian!"
            print(f"[*] Sending notification '{msg}'...")
            res = watch.send_notification(msg)
            print(f"[+] Opcode responses: {res}")
        elif cmd == "sync":
            print("[*] Running time synchronization tests...")
            res = watch.sync_time()
            print(f"[+] Result: {res}")
        elif cmd == "raw":
            if not arg:
                print("Usage: raw <hex>")
                continue
            resp = watch.send_raw(arg)
            print(f"[RAW TX: {arg}] -> RX: {resp}")
        else:
            print(f"[-] Unknown command: '{cmd}'. Supported: info, ping, notify <text>, sync, raw <hex>, exit.")

def main():
    parser = argparse.ArgumentParser(description="Martian Notifier CLI Control Tool")
    parser.add_argument("command", nargs="?", default="console", choices=["console", "info", "battery", "ping", "notify", "sync-time", "detect"])
    parser.add_argument("--mac", default=DEFAULT_MAC, help=f"Bluetooth MAC address of the watch (default: {DEFAULT_MAC} or MARTIAN_MAC env var)")
    parser.add_argument("--msg", default="Hello Martian!", help="Notification message payload")
    parser.add_argument("--title", default="Test", help="Notification title")
    args = parser.parse_args()

    watch = MartianWatch(mac=args.mac)

    if args.command == "detect":
        print(f"[*] Checking device {args.mac} in BlueZ subsystem...")
        res = subprocess.run(["bluetoothctl", "info", args.mac], capture_output=True, text=True)
        print(res.stdout)
        return

    if not watch.connect():
        sys.exit(1)

    try:
        if args.command == "console":
            run_console(watch)
        elif args.command in ("info", "battery"):
            data = watch.get_info()
            if data:
                print(f"[SUCCESS] Firmware Version: {data['firmware']}")
                print(f"[SUCCESS] Battery Level: {data['battery_pct']}%")
                print(f"[RAW HEX]: {data['raw_hex']}")
            else:
                print("[-] Failed to retrieve info from watch.")
        elif args.command == "ping":
            if watch.ping():
                print("[SUCCESS] Ping successful (Received ACK 0x03)!")
            else:
                print("[-] Ping did not receive ACK.")
        elif args.command == "notify":
            res = watch.send_notification(args.msg)
            print("Opcode responses:", res)
        elif args.command == "sync-time":
            res = watch.sync_time()
            print("Result:", res)
    finally:
        watch.close()
        print("[+] Connection closed safely.")

if __name__ == "__main__":
    main()
