#!/usr/bin/env python3
import socket
import struct
import subprocess
import time
import sys
import os
import threading
import readline

DEFAULT_MAC = os.environ.get("MARTIAN_MAC", "60:0F:77:03:DB:00")

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

class MartianLab:
    def __init__(self, mac=DEFAULT_MAC):
        self.mac = mac
        self.sock = None
        self.running = False
        self.lock = threading.Lock()

    def connect(self, timeout=30.0):
        start = time.time()
        print(f"[*] Connecting to {self.mac}...")
        while time.time() - start < timeout:
            try:
                s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
                s.settimeout(2.5)
                s.connect((self.mac, 1))
                self.sock = s
                self.running = True
                print("\n[+] PERSISTENT RFCOMM SESSION ESTABLISHED!")
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
        print("\n[-] Connection timed out.")
        return False

    def send_raw(self, pkt):
        with self.lock:
            if not self.sock:
                return None
            try:
                self.sock.send(pkt)
                time.sleep(0.08)
                self.sock.settimeout(0.6)
                resp = self.sock.recv(1024)
                return resp
            except socket.timeout:
                return None
            except Exception as e:
                print(f"\n[-] Socket error: {e}")
                self.running = False
                return None

    def send_cmd(self, opcode, payload=b""):
        pkt = bytes([0x3C, opcode, 0x00, len(payload)]) + payload + b">"
        resp = self.send_raw(pkt)
        r_hex = resp.hex() if resp else "(No response)"
        return pkt, resp, r_hex

    def keep_alive_worker(self):
        # Keeps connection alive indefinitely
        while self.running:
            time.sleep(8.0)
            if not self.running:
                break
            # Send lightweight ping (0x0C) to keep radio awake
            self.send_cmd(0x0C)

    def probe_lengths(self, opcode, min_l=1, max_l=16):
        print(f"[*] Probing payload length for Opcode 0x{opcode:02X} from {min_l} to {max_l} bytes...")
        accepted = []
        for l in range(min_l, max_l + 1):
            test_data = bytes([i % 256 for i in range(l)])
            pkt, resp, r_hex = self.send_cmd(opcode, test_data)
            if resp and resp[1] != 0x04:
                print(f"[ACCEPTED] Opcode 0x{opcode:02X} len={l}: RX={r_hex}")
                accepted.append((l, r_hex))
        if not accepted:
            print(f"[-] Opcode 0x{opcode:02X} rejected all lengths in this range.")
        return accepted

def run_interactive(lab):
    t = threading.Thread(target=lab.keep_alive_worker, daemon=True)
    t.start()

    print("\n" + "=" * 65)
    print("MARTIAN NOTIFIER LIVE LAB - PERSISTENT CONNECTION ACTIVE")
    print("Commands:")
    print("  time                 - Inject current host system time and date")
    print("  date <month> <day>   - Inject custom month/day (e.g. date 11 2)")
    print("  probe <opcode_hex>   - Probe accepted payload lengths (e.g. probe 2c)")
    print("  send <op> [hex_data] - Send custom packet (e.g. send 2a 1a0b020a1500)")
    print("  info                 - Query firmware build and battery level")
    print("  exit / quit          - Disconnect and exit")
    print("=" * 65)

    while lab.running:
        try:
            line = input("\nlab> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower()

        if cmd in ("exit", "quit", "q"):
            break

        elif cmd == "info":
            _, resp, r_hex = lab.send_cmd(0x0A)
            if resp and len(resp) >= 7:
                print(f"[INFO] Firmware: {resp[4]}.{resp[5]:02d} | Battery: {resp[6]}%")
            else:
                print(f"[-] RX: {r_hex}")

        elif cmd == "time":
            lt = time.localtime()
            now = int(time.time())
            print(f"[*] Injecting time: {lt.tm_hour:02d}:{lt.tm_min:02d}:{lt.tm_sec:02d} Date {lt.tm_mday}/{lt.tm_mon}")
            # 0x29: UTC timestamp
            p29, r29, h29 = lab.send_cmd(0x29, struct.pack(">I", now))
            print(f"[0x29 Timestamp] -> {h29}")
            # 0x2A: RTC local
            rtc_data = bytes([lt.tm_year % 100, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec])
            p2a, r2a, h2a = lab.send_cmd(0x2A, rtc_data)
            print(f"[0x2A RTC Time]  -> {h2a}")
            # 0x2E: Date
            p2e, r2e, h2e = lab.send_cmd(0x2E, bytes([lt.tm_mon, lt.tm_mday]))
            print(f"[0x2E Date]      -> {h2e}")
            print("[+] Time buffers successfully injected!")

        elif cmd == "date":
            if len(parts) < 3:
                print("Usage: date <month> <day> (e.g. date 11 2)")
                continue
            m = int(parts[1])
            d = int(parts[2])
            pkt, resp, r_hex = lab.send_cmd(0x2E, bytes([m, d]))
            print(f"[+] Injecting Date {d}/{m} into 0x2E -> RX: {r_hex}")

        elif cmd == "probe":
            if len(parts) < 2:
                print("Usage: probe <opcode_hex> (e.g. probe 2c)")
                continue
            op = int(parts[1], 16)
            lab.probe_lengths(op, 1, 16)

        elif cmd == "send":
            if len(parts) < 2:
                print("Usage: send <opcode_hex> [data_hex] (e.g. send 2a 1a0b02)")
                continue
            op = int(parts[1], 16)
            data = bytes.fromhex(parts[2]) if len(parts) > 2 else b""
            pkt, resp, r_hex = lab.send_cmd(op, data)
            print(f"TX: {pkt.hex()} -> RX: {r_hex}")

        else:
            print(f"[-] Unknown command: '{cmd}'. Available: time, date, probe, send, info, exit.")

    lab.running = False
    if lab.sock:
        lab.sock.close()
    print("[+] Disconnected safely.")

def main():
    mac = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else DEFAULT_MAC
    lab = MartianLab(mac=mac)
    if not lab.connect():
        sys.exit(1)
    run_interactive(lab)

if __name__ == "__main__":
    main()
