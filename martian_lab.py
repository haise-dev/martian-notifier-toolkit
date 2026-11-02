#!/usr/bin/env python3
import socket
import struct
import subprocess
import time
import sys
import threading
import readline

TARGET_MAC = "60:0F:77:03:DB:00"

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

class MartianLab:
    def __init__(self, mac=TARGET_MAC):
        self.mac = mac
        self.sock = None
        self.running = False
        self.lock = threading.Lock()

    def connect(self, timeout=30.0):
        start = time.time()
        print(f"[*] Đang kết nối tới {self.mac}...")
        while time.time() - start < timeout:
            try:
                s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
                s.settimeout(2.5)
                s.connect((self.mac, 1))
                self.sock = s
                self.running = True
                print("\n[+] ĐÃ THIẾT LẬP KẾT NỐI DUY TRÌ LIÊN TỤC VỚI ĐỒNG HỒ!")
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
        print("\n[-] Hết thời gian chờ kết nối.")
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
                print(f"\n[-] Lỗi socket: {e}")
                self.running = False
                return None

    def send_cmd(self, opcode, payload=b""):
        pkt = bytes([0x3C, opcode, 0x00, len(payload)]) + payload + b">"
        resp = self.send_raw(pkt)
        r_hex = resp.hex() if resp else "(No response)"
        return pkt, resp, r_hex

    def keep_alive_worker(self):
        # Giữ kết nối không bao giờ bị ngắt
        while self.running:
            time.sleep(8.0)
            if not self.running:
                break
            # Gửi ping 0x0C nhẹ nhàng giữ radio thức
            self.send_cmd(0x0C)

    def probe_lengths(self, opcode, min_l=1, max_l=16):
        print(f"[*] Đang dò độ dài payload cho Opcode 0x{opcode:02X} từ {min_l} đến {max_l} bytes...")
        accepted = []
        for l in range(min_l, max_l + 1):
            test_data = bytes([i % 256 for i in range(l)])
            pkt, resp, r_hex = self.send_cmd(opcode, test_data)
            if resp and resp[1] != 0x04:
                print(f"[CHẤP NHẬN] Opcode 0x{opcode:02X} len={l}: RX={r_hex}")
                accepted.append((l, r_hex))
            else:
                pass
        if not accepted:
            print(f"[-] Opcode 0x{opcode:02X} không chấp nhận độ dài nào trong khoảng này.")
        return accepted

def run_interactive(lab):
    t = threading.Thread(target=lab.keep_alive_worker, daemon=True)
    t.start()

    print("\n" + "=" * 65)
    print("MARTIAN NOTIFIER LIVE LAB - KẾT NỐI ĐANG ĐƯỢC GIỮ SỐNG LIÊN TỤC")
    print("Các lệnh sẵn sàng gõ:")
    print("  time                 - Nạp giờ và ngày thực tế của máy tính")
    print("  date <tháng> <ngày>  - Nạp ngày tháng tùy ý (vd: date 11 2)")
    print("  probe <opcode_hex>   - Dò độ dài payload được chấp nhận (vd: probe 2c)")
    print("  send <op> <hex_data> - Gửi lệnh tùy ý (vd: send 2a 1a0b020a1500)")
    print("  info                 - Xem version và pin hiện tại")
    print("  exit                 - Thoát và đóng kết nối")
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
                print(f"[INFO] Firmware: {resp[4]}.{resp[5]:02d} | Pin: {resp[6]}%")
            else:
                print(f"[-] RX: {r_hex}")

        elif cmd == "time":
            lt = time.localtime()
            now = int(time.time())
            print(f"[*] Nạp thời gian: {lt.tm_hour:02d}:{lt.tm_min:02d}:{lt.tm_sec:02d} Ngày {lt.tm_mday}/{lt.tm_mon}")
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
            print("[+] ĐÃ NẠP TOÀN BỘ BỘ ĐỆM THỜI GIAN!")

        elif cmd == "date":
            if len(parts) < 3:
                print("Cách dùng: date <tháng> <ngày> (ví dụ: date 11 2)")
                continue
            m = int(parts[1])
            d = int(parts[2])
            pkt, resp, r_hex = lab.send_cmd(0x2E, bytes([m, d]))
            print(f"[+] Nạp Ngày {d}/{m} vào 0x2E -> RX: {r_hex}")

        elif cmd == "probe":
            if len(parts) < 2:
                print("Cách dùng: probe <opcode_hex> (ví dụ: probe 2c)")
                continue
            op = int(parts[1], 16)
            lab.probe_lengths(op, 1, 16)

        elif cmd == "send":
            if len(parts) < 2:
                print("Cách dùng: send <op_hex> [data_hex] (ví dụ: send 2a 1a0b02)")
                continue
            op = int(parts[1], 16)
            data = bytes.fromhex(parts[2]) if len(parts) > 2 else b""
            pkt, resp, r_hex = lab.send_cmd(op, data)
            print(f"TX: {pkt.hex()} -> RX: {r_hex}")

        else:
            print(f"[-] Lệnh không nhận diện: '{cmd}'. Gõ 'time', 'date', 'probe', 'send', 'info', hoặc 'exit'.")

    lab.running = False
    if lab.sock:
        lab.sock.close()
    print("[+] Đã ngắt kết nối an toàn.")

def main():
    lab = MartianLab()
    if not lab.connect():
        sys.exit(1)
    run_interactive(lab)

if __name__ == "__main__":
    main()
