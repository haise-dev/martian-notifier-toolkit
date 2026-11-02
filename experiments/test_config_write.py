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
    time.sleep(0.12)
    try:
        resp = s.recv(1024)
        print(f"TX [0x{op:02X}]: len={len(payload)} -> RX: {resp.hex() if resp else 'None'}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}]: Timeout")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.5)

    # 1. Đọc bảng cấu hình 48 byte hiện tại của 0x2F
    print("\n--- 1. Đọc bảng cấu hình 0x2F ---")
    resp_2f = send(s, 0x2F)
    if not resp_2f or len(resp_2f) < 50:
        print("[-] Không đọc được 0x2F")
        s.close()
        sys.exit(1)

    cfg_data = bytearray(resp_2f[4:-1])
    print(f"Bảng 0x2F hiện tại ({len(cfg_data)} bytes): {cfg_data.hex()}")

    # Thử bật bit 1 và bit 2 của Byte 44 (chuyển 0xC1 -> 0xC7 hoặc 0xFF)
    orig_b44 = cfg_data[44]
    cfg_data[44] = 0xFF # Bật toàn bộ các cờ tính năng (World Clock, Weather, Alerts...)
    print(f"Sửa Byte 44 từ 0x{orig_b44:02X} thành 0x{cfg_data[44]:02X}")

    # Ghi lại bảng 0x2F vào đồng hồ
    print("\n--- 2. Ghi bảng 0x2F đã bật toàn bộ tính năng ---")
    write_resp = send(s, 0x2F, bytes(cfg_data))

    # Đọc lại xác nhận
    print("\n--- 3. Đọc lại 0x2F xác nhận đã lưu vào Flash chưa ---")
    read_back = send(s, 0x2F)
    if read_back and len(read_back) >= 50:
        new_b44 = read_back[4:-1][44]
        print(f"[*] Byte 44 sau khi ghi: 0x{new_b44:02X}")
        if new_b44 == 0xFF:
            print("[THÀNH CÔNG] ĐÃ BẬT VÀ LƯU TOÀN BỘ CỜ TÍNH NĂNG VÀO BỘ NHỚ FLASH!")
        else:
            print(f"[*] Chưa đổi: 0x{new_b44:02X}")

    time.sleep(2)
    s.close()
    print("[+] Hoàn tất.")

if __name__ == "__main__":
    main()
