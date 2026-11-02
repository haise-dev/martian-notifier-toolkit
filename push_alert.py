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
    time.sleep(0.08)
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

    s.settimeout(0.3)

    # Thử nghiệm các cấu trúc thông báo đẩy
    msg = b"HELLO"
    print("\n[*] Thử nghiệm các cấu trúc gói tin đẩy thông báo OLED...")

    for op in [0x01, 0x02, 0x03, 0x05, 0x06, 0x07, 0x0D, 0x0E]:
        for n_type in [0x01, 0x02, 0x03]: # Call, SMS, Alert
            for v_type in [0x00, 0x01, 0x02]: # Vibe
                payload = bytes([n_type, v_type]) + msg
                resp = send(s, op, payload)
                if resp and resp[1] != 0x04:
                    print(f"\n[!!! TÌM THẤY LỆNH ĐẨY MÀN HÌNH !!!] Opcode 0x{op:02X} chấp nhận: Type={n_type}, Vibe={v_type}")
                    time.sleep(2)
                    s.close()
                    return

    s.close()
    print("\n[+] Đã test xong.")

if __name__ == "__main__":
    main()
