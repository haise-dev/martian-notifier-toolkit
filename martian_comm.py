import socket
import struct
import time
import sys

TARGET = "60:0F:77:03:DB:00"

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

def connect_rfcomm():
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
    s.settimeout(5.0)

    print(f"[*] Đang cố gắng kết nối tới Martian RFCOMM Channel 1 ({TARGET})...")
    s.connect((TARGET, 1))
    print("[+] KẾT NỐI THÀNH CÔNG VỚI ĐỒNG HỒ!")
    return s

def send_and_recv(s, cmd_bytes, wait_sec=0.2):
    print(f"\n[TX] Gửi: {cmd_bytes} (hex: {cmd_bytes.hex()})")
    s.send(cmd_bytes)
    time.sleep(wait_sec)
    try:
        data = s.recv(1024)
        print(f"[RX] Nhận: {data} (hex: {data.hex()})")
        return data
    except socket.timeout:
        print("[RX] Timeout không phản hồi.")
        return None

def main():
    try:
        s = connect_rfcomm()
    except Exception as e:
        print(f"[-] Lỗi kết nối: {e}")
        print("[-] Đảm bảo đồng hồ đang ở màn hình 'Pair from app' để bật sóng radio.")
        sys.exit(1)

    s.settimeout(2.0)

    # 1. Thử nhận gói tin chào mừng ban đầu nếu có
    try:
        init_data = s.recv(1024)
        print(f"[RX-INIT] Đồng hồ tự gửi: {init_data} ({init_data.hex()})")
    except socket.timeout:
        pass

    # 2. Thử nghiệm các lệnh truy vấn
    # Trong giao thức Martian, các lệnh thường có dạng <cmd> hoặc <cmd:param>
    probes = [
        b"<?>",
        b"<I>",
        b"<B>",
        b"<S>",
        b"<V>",
        b"<T>",
        b"<M:Hello Martian>",
        b"<T:20261102094500>",
    ]

    for p in probes:
        send_and_recv(s, p)

    print("\n[*] Giữ kết nối trong 3 giây...")
    time.sleep(3)
    s.close()
    print("[+] Đóng kết nối an toàn.")

if __name__ == "__main__":
    main()
