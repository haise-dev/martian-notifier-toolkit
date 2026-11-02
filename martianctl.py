#!/usr/bin/env python3
import socket
import struct
import subprocess
import time
import sys
import argparse
import readline

TARGET_MAC = "60:0F:77:03:DB:00"

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

class MartianWatch:
    def __init__(self, mac=TARGET_MAC):
        self.mac = mac
        self.sock = None

    def connect(self, timeout=25.0):
        start = time.time()
        print(f"[*] Đang tìm và kết nối tới {self.mac}...")
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
                print(f"\n[+] KẾT NỐI THÀNH CÔNG RFCOMM CHANNEL 1!")
                # Flush greeting
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

        print("\n[-] Hết thời gian chờ kết nối. Hãy đảm bảo đồng hồ đang ở 'Pair from app'.")
        return False

    def send_packet(self, opcode, payload=b""):
        if not self.sock:
            raise RuntimeError("Chưa kết nối tới đồng hồ.")
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
    print("Các lệnh hỗ trợ:")
    print("  info          - Đọc Firmware version và mức pin %")
    print("  ping          - Gửi tín hiệu kiểm tra (ACK 0x03)")
    print("  notify <text> - Gửi chuỗi text thử nghiệm lên màn hình OLED")
    print("  sync          - Thử nghiệm đồng bộ thời gian")
    print("  raw <hex>     - Gửi chuỗi byte hex tùy ý (ví dụ: 3c0a00003e)")
    print("  exit / quit   - Đóng kết nối và thoát")
    print("=" * 60)

    while True:
        try:
            cmd_line = input("\nmartianctl> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThoát console...")
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
                print("[THÀNH CÔNG] Ping OK (ACK 0x03)!")
            else:
                print("[-] Ping không nhận được ACK.")
        elif cmd == "info" or cmd == "battery":
            data = watch.get_info()
            if data:
                print(f"[+] Firmware: {data['firmware']} | Pin: {data['battery_pct']}% | Raw: {data['raw_hex']}")
            else:
                print("[-] Không đọc được info.")
        elif cmd == "notify":
            msg = arg if arg else "Hello Martian!"
            print(f"[*] Đang gửi notify '{msg}'...")
            res = watch.send_notification(msg)
            print(f"[+] Kết quả phản hồi: {res}")
        elif cmd == "sync":
            print("[*] Đang thử nghiệm đồng bộ thời gian...")
            res = watch.sync_time()
            print(f"[+] Kết quả: {res}")
        elif cmd == "raw":
            if not arg:
                print("Cách dùng: raw <hex>")
                continue
            resp = watch.send_raw(arg)
            print(f"[RAW TX: {arg}] -> RX: {resp}")
        else:
            print(f"[-] Lệnh không nhận diện: '{cmd}'. Gõ 'info', 'ping', 'notify <text>', 'sync', 'raw <hex>' hoặc 'exit'.")

def main():
    parser = argparse.ArgumentParser(description="Martian Notifier CLI Control Tool")
    parser.add_argument("command", nargs="?", default="console", choices=["console", "info", "battery", "ping", "notify", "sync-time", "detect"])
    parser.add_argument("--msg", default="Hello Martian!", help="Nội dung thông báo")
    parser.add_argument("--title", default="Test", help="Tiêu đề thông báo")
    args = parser.parse_args()

    watch = MartianWatch()

    if args.command == "detect":
        print(f"[*] Kiểm tra thiết bị {TARGET_MAC} trong hệ thống...")
        res = subprocess.run(["bluetoothctl", "info", TARGET_MAC], capture_output=True, text=True)
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
                print(f"[THÀNH CÔNG] Firmware Version: {data['firmware']}")
                print(f"[THÀNH CÔNG] Dung lượng Pin: {data['battery_pct']}%")
                print(f"[RAW HEX]: {data['raw_hex']}")
            else:
                print("[-] Không đọc được thông tin từ đồng hồ.")
        elif args.command == "ping":
            if watch.ping():
                print("[THÀNH CÔNG] Ping đồng hồ thành công (Nhận ACK 0x03)!")
            else:
                print("[-] Ping không nhận được ACK.")
        elif args.command == "notify":
            res = watch.send_notification(args.msg)
            print("Kết quả các opcode phản hồi:", res)
        elif args.command == "sync-time":
            res = watch.sync_time()
            print("Kết quả:", res)
    finally:
        watch.close()
        print("[+] Đã đóng kết nối an toàn.")

if __name__ == "__main__":
    main()
