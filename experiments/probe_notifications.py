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

def send_test(s, op, payload):
    pkt = bytes([0x3C, op, 0x00, len(payload)]) + payload + b">"
    s.send(pkt)
    time.sleep(0.08)
    try:
        resp = s.recv(1024)
        if resp and resp[1] != 0x04:
            print(f"\n[!!! TÍN HIỆU ĐẶC BIỆT !!!] Opcode 0x{op:02X} phản hồi: {resp.hex()}")
            return True
        return False
    except socket.timeout:
        return False

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.3)
    text = b"MARTIAN TEST"

    print("\n[*] Đang thử nghiệm bắn thông báo vào các Opcode từ 0x01 đến 0x28...")

    # Các dạng header thông báo thông dụng
    formats = [
        ("Raw Text", text),
        ("AppID 1 + Text", bytes([0x01]) + text),
        ("AppID 1 + Vibe 1 + Text", bytes([0x01, 0x01]) + text),
        ("Vibe 1 + App 1 + Text", bytes([0x01, 0x01, 0x00]) + text),
        ("Type 0x02 (SMS) + Text", bytes([0x02, 0x01]) + text),
    ]

    found = False
    for name, p in formats:
        print(f"\n--- Thử dạng: {name} ---")
        for op in range(0x01, 0x28):
            if send_test(s, op, p):
                print(f"[+] Opcode 0x{op:02X} chấp nhận {name}!")
                found = True
                time.sleep(1)

    time.sleep(2)
    s.close()
    print("\n[+] Hoàn tất phiên kiểm tra.")

if __name__ == "__main__":
    main()
