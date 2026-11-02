#!/usr/bin/env python3
import socket
import struct
import subprocess
import time
import sys

TARGET = "60:0F:77:03:DB:00"

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

def connect_watch(timeout=30.0):
    start = time.time()
    print("[*] Đang tự động kết nối ngầm... Hãy bấm nút bất kỳ trên đồng hồ để đánh thức!")
    while time.time() - start < timeout:
        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
            s.settimeout(2.5)
            s.connect((TARGET, 1))
            print("\n[+] ĐÃ BẮT ĐƯỢC ĐỒNG HỒ THÀNH CÔNG!")
            # Xả sạch bộ đệm ban đầu
            s.settimeout(0.3)
            try:
                s.recv(1024)
            except Exception:
                pass
            return s
        except Exception:
            s.close()
            time.sleep(0.4)
            print(".", end="", flush=True)
    print("\n[-] Hết thời gian chờ kết nối.")
    return None

def send_packet(s, opcode, payload=b""):
    pkt = bytes([0x3C, opcode, 0x00, len(payload)]) + payload + b">"
    s.send(pkt)
    time.sleep(0.35) # Delay an toàn chống tràn bộ đệm
    try:
        s.settimeout(0.8)
        resp = s.recv(1024)
        return pkt, resp, resp.hex() if resp else None
    except socket.timeout:
        return pkt, None, "(Timeout)"

def main():
    s = connect_watch(30.0)
    if not s:
        sys.exit(1)

    now = int(time.time())
    lt = time.localtime(now)
    h, m, sec = lt.tm_hour, lt.tm_min, lt.tm_sec
    mon, day, yr = lt.tm_mon, lt.tm_mday, lt.tm_year % 100

    print("\n" + "=" * 60)
    print(f"BẮT ĐẦU NẠP CẤU HÌNH THỜI GIAN CHUẨN: {h:02d}:{m:02d}:{sec:02d} Ngày {day:02d}/{mon:02d}/20{yr:02d}")
    print("=" * 60)

    # 1. Nạp UTC Timestamp vào 0x29 (Đồng hồ dùng để tính thứ trong tuần)
    print("\n[Bước 1/6] Nạp Timestamp vào 0x29...")
    _, _, h29 = send_packet(s, 0x29, struct.pack(">I", now))
    print(f"-> RX: {h29}")

    # 2. Nạp RTC Time [YY, MM, DD, HH, MM, SS] vào 0x2A
    print("\n[Bước 2/6] Nạp RTC Time [Năm, Tháng, Ngày, Giờ, Phút, Giây] vào 0x2A...")
    rtc_data = bytes([yr, mon, day, h, m, sec])
    _, _, h2a = send_packet(s, 0x2A, rtc_data)
    print(f"-> RX: {h2a}")

    # 3. Nạp Ngày [Tháng, Ngày] vào 0x2E (Kích hoạt hiển thị ngày)
    print("\n[Bước 3/6] Nạp Ngày vào 0x2E...")
    _, _, h2e = send_packet(s, 0x2E, bytes([mon, day]))
    print(f"-> RX: {h2e}")

    # 4. Kích hoạt World Clock trên 0x28 (Opcode 3 byte: Bật=1, Múi giờ=+7, DST=0)
    print("\n[Bước 4/6] Kích hoạt World Clock 3 byte vào 0x28...")
    _, _, h28 = send_packet(s, 0x28, bytes([0x01, 0x07, 0x00]))
    print(f"-> RX: {h28}")

    # 5. Thử các cờ kích hoạt hiển thị 0x2B
    print("\n[Bước 5/6] Thử các cờ kích hoạt hiển thị vào 0x2B...")
    for flag_val in [bytes([0x01]), bytes([0x01, 0x01]), bytes([0x00, 0x01])]:
        _, _, h2b = send_packet(s, 0x2B, flag_val)
        print(f"   0x2B {flag_val.hex()} -> RX: {h2b}")

    # 6. Thử cấu hình hiển thị World Clock vào 0x32
    print("\n[Bước 6/6] Thử cấu hình hiển thị vào 0x32...")
    for wc_val in [bytes([0x01, 0x07, 0x00]), bytes([0x01, 0x00, 0x07])]:
        _, _, h32 = send_packet(s, 0x32, wc_val)
        print(f"   0x32 {wc_val.hex()} -> RX: {h32}")

    print("\n" + "=" * 60)
    print("[HOÀN TẤT] Đã nạp xong toàn bộ 6 bước cấu hình thời gian chuẩn!")
    print("=" * 60)

    time.sleep(2)
    s.close()

if __name__ == "__main__":
    main()
