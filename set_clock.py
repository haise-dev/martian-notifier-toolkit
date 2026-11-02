import socket
import struct
import time
import sys

TARGET = "60:0F:77:03:DB:00"

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

def connect_with_retry(timeout_sec=20.0):
    start = time.time()
    print("[*] Đang chờ kết nối... (Hãy vào 'Pair from app' trên đồng hồ)")
    while time.time() - start < timeout_sec:
        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
            s.settimeout(2.0)
            s.connect((TARGET, 1))
            print("\n[+] ĐÃ KẾT NỐI THÀNH CÔNG!")
            return s
        except Exception:
            s.close()
            time.sleep(0.4)
            print(".", end="", flush=True)
    return None

def send_pkt(s, op, data=b""):
    seq = 0x00
    pkt = bytes([0x3C, op, seq, len(data)]) + data + b">"
    s.send(pkt)
    time.sleep(0.08)
    try:
        resp = s.recv(1024)
        print(f"TX [0x{op:02X}]: {pkt.hex()} -> RX: {resp.hex()}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}]: {pkt.hex()} -> Timeout")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.4)
    now = time.localtime()
    hour = now.tm_hour
    minute = now.tm_min
    sec = now.tm_sec
    month = now.tm_mon
    day = now.tm_mday
    year = now.tm_year % 100

    print(f"\n[*] Đang cài đặt: Giờ {hour:02d}:{minute:02d}:{sec:02d} | Ngày {day:02d}/{month:02d}/20{year:02d}")

    # 1. Ghi vào thanh ghi Giờ 0x32 (3 bytes: HH MM SS)
    # Thử cả Decimal và BCD
    print("\n--- Nạp Giờ vào Opcode 0x32 (3 bytes: HH MM SS) ---")
    send_pkt(s, 0x32, bytes([hour, minute, sec]))

    # 2. Ghi vào thanh ghi Ngày 0x2E (2 bytes: MM DD)
    print("\n--- Nạp Ngày vào Opcode 0x2E (2 bytes: MM DD) ---")
    send_pkt(s, 0x2E, bytes([month, day]))

    # 3. Ghi vào thanh ghi 0x2D (4 bytes: Year, Timezone, flags)
    print("\n--- Nạp Opcode 0x2D (4 bytes: YYYY / Offset) ---")
    send_pkt(s, 0x2D, bytes([20, year, month, day]))

    # 4. Ghi bật cờ hiển thị 0x2B
    print("\n--- Bật cờ tính năng 0x2B ---")
    send_pkt(s, 0x2B, bytes([0x01]))
    send_pkt(s, 0x2B, bytes([0x01, 0x01]))

    # 5. Đọc lại toàn bộ để kiểm tra đồng hồ đã lưu chưa
    print("\n--- ĐỌC LẠI CÁC THANH GHI SAU KHI NẠP ---")
    send_pkt(s, 0x32) # Giờ
    send_pkt(s, 0x2E) # Ngày
    send_pkt(s, 0x2D) # 0x2D
    send_pkt(s, 0x2B) # Cờ 0x2B

    time.sleep(2)
    s.close()
    print("\n[+] Đã nạp xong toàn bộ dữ liệu ngày giờ!")

if __name__ == "__main__":
    main()
