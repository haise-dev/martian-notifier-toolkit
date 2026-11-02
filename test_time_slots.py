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
        print(f"TX [0x{op:02X}]: {pkt.hex()} -> RX: {resp.hex()}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}]: Timeout")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.5)

    # Thử nạp giờ 10:35 vào các thanh ghi hiển thị
    h, m, s_sec = 10, 35, 0
    print(f"\n[*] Đang nạp giá trị Giờ {h}:{m} vào các thanh ghi...")

    # 1. Thử vào 0x2E: [Hour, Minute] = [10, 35]
    print("\n--- 1. Nạp [10, 35] vào Opcode 0x2E ---")
    send(s, 0x2E, bytes([h, m]))

    # 2. Thử vào 0x32: [10, 35, 0]
    print("\n--- 2. Nạp [10, 35, 0] vào Opcode 0x32 ---")
    send(s, 0x32, bytes([h, m, s_sec]))

    # 3. Thử vào 0x2D: [10, 35, 0, 0]
    print("\n--- 3. Nạp [10, 35, 0, 0] vào Opcode 0x2D ---")
    send(s, 0x2D, bytes([h, m, s_sec, 0]))

    # 4. Thử vào 0x2A với đầy đủ [26, 11, 2, 10, 35, 0]
    print("\n--- 4. Nạp [26, 11, 2, 10, 35, 0] vào Opcode 0x2A ---")
    send(s, 0x2A, bytes([26, 11, 2, h, m, s_sec]))

    time.sleep(2)
    s.close()
    print("\n[+] ĐÃ NẠP XONG GIỜ 10:35 VÀO CÁC THANH GHI!")

if __name__ == "__main__":
    main()
