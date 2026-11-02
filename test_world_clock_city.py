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
        print(f"TX [0x{op:02X}] len={len(payload)}: {pkt.hex()} -> RX: {resp.hex()}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}]: Timeout")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.5)
    now = time.localtime()

    print("\n--- 1. Nạp UTC Timestamp vào Opcode 0x29 ---")
    send(s, 0x29, struct.pack(">I", int(time.time())))

    print("\n--- 2. Nạp RTC Time [YY, MM, DD, HH, MM, SS] vào Opcode 0x2A ---")
    send(s, 0x2A, bytes([now.tm_year % 100, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec]))

    print("\n--- 3. Thử nghiệm Opcode 0x2C (City Name / Tên thành phố) ---")
    # Thử gửi tên thành phố "HANOI" hoặc "LOCAL"
    send(s, 0x2C, b"HANOI")
    send(s, 0x2C, b"LOCAL\x00")
    send(s, 0x2C, bytes([0x01]) + b"HANOI")

    print("\n--- 4. Thử nghiệm Opcode 0x2D với City / Timezone ---")
    send(s, 0x2D, b"HANOI")
    send(s, 0x2D, bytes([0x01, 0x07]) + b"HANOI")

    print("\n--- 5. Thử nghiệm các Opcode 0x30, 0x31, 0x33, 0x34 với chuỗi thành phố ---")
    for op in [0x30, 0x31, 0x33, 0x34]:
        send(s, op, b"HANOI")

    print("\n--- 6. Kích hoạt cờ World Clock trên 0x32 ---")
    send(s, 0x32, bytes([0x01, 0x07, 0x00]))
    send(s, 0x32, bytes([0x01, 0x00, 0x07]))
    send(s, 0x32, b"HANOI\x00")

    time.sleep(2)
    s.close()
    print("\n[+] ĐÃ HOÀN TẤT THỬ NGHIỆM TÊN THÀNH PHỐ VÀ GIỜ SỐ!")

if __name__ == "__main__":
    main()
