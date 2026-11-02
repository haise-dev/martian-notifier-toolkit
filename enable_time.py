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
        print(f"TX [0x{op:02X}]: len={len(payload)} ({payload.hex()}) -> RX: {resp.hex()}")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}]: Timeout")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        sys.exit(1)

    s.settimeout(0.5)

    # 1. Nạp Timestamp vào 0x29
    now = int(time.time())
    print(f"\n--- 1. Nạp Timestamp {now} vào 0x29 ---")
    send(s, 0x29, struct.pack(">I", now))

    # 2. Thử nghiệm các opcode cặp ghi cho 0x2F và 0x32:
    # Nếu 0x32 là đọc, lệnh ghi thường là 0x30, 0x31 hoặc 0x33
    # Nếu 0x2F là đọc, lệnh ghi là 0x28 hoặc 0x2C
    print("\n--- 2. Thử nghiệm ghi bật World Clock vào các opcode 0x28, 0x30, 0x31, 0x33 ---")
    # Payload bật World Clock: [Enable=1, TZ_Offset=7, DST=0]
    wc_payload = bytes([0x01, 0x07, 0x00])
    for op in [0x28, 0x30, 0x31, 0x33, 0x34, 0x35]:
        send(s, op, wc_payload)
        send(s, op, bytes([0x01]))

    # 3. Thử opcode 0x0C với các tham số thời gian
    print("\n--- 3. Thử nghiệm Opcode 0x0C (Opcode luôn trả về ACK) ---")
    # Thử gửi giờ hiện tại [Hour=10, Min=45, Sec=0]
    send(s, 0x0C, bytes([10, 45, 0]))
    send(s, 0x0C, struct.pack(">I", now))
    send(s, 0x0C, bytes([0x01, 10, 45]))

    time.sleep(2)
    s.close()
    print("\n[+] Đã gửi xong toàn bộ gói tin bật giờ.")

if __name__ == "__main__":
    main()
