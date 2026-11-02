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

def send(s, op, payload=b""):
    pkt = bytes([0x3C, op, 0x00, len(payload)]) + payload + b">"
    s.send(pkt)
    time.sleep(0.1)
    try:
        resp = s.recv(1024)
        print(f"TX [0x{op:02X}] {payload.hex()} -> RX: {resp.hex()}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}] -> Timeout")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.5)

    # 1. Nạp Timestamp vào 0x29
    now_utc = int(time.time())
    ts_bytes = struct.pack(">I", now_utc)
    print(f"\n--- 1. Nạp UTC Timestamp ({now_utc}) vào Opcode 0x29 ---")
    send(s, 0x29, ts_bytes)

    # 2. Nạp Ngày (Tháng 11, Ngày 2) vào 0x2E
    print("\n--- 2. Nạp Ngày (Tháng 11, Ngày 02) vào Opcode 0x2E ---")
    send(s, 0x2E, bytes([11, 2]))

    # 3. Kích hoạt World Clock trên 0x32:
    # Byte 0: 0x01 (BẬT tính năng World Clock)
    # Byte 1: 0x07 (Múi giờ UTC+7 Việt Nam)
    # Byte 2: 0x00 (Daylight Saving Time = 0)
    print("\n--- 3. Kích hoạt World Clock vào Opcode 0x32 (Bật=1, Múi giờ=+7, DST=0) ---")
    send(s, 0x32, bytes([0x01, 0x07, 0x00]))

    # Thử thêm thành phố hoặc tên múi giờ nếu 0x32 có subcommand
    # Hoặc thử 0x31 / 0x33 nếu có
    print("\n--- 4. Đọc lại trạng thái xác nhận ---")
    send(s, 0x32) # Đọc lại 0x32
    send(s, 0x2E) # Đọc lại 0x2E

    time.sleep(2)
    s.close()
    print("\n[+] ĐÃ KÍCH HOẠT VÀ NẠP XONG TOÀN BỘ GIỜ & NGÀY!")

if __name__ == "__main__":
    main()
