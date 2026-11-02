import socket
import struct
import subprocess
import time
import sys

TARGET = "60:0F:77:03:DB:00"

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

def connect_with_retry(timeout_sec=20.0):
    start = time.time()
    print("[*] Đang chờ đồng hồ kết nối... (Bấm nút trên đồng hồ nếu màn hình tắt)")
    while time.time() - start < timeout_sec:
        try:
            subprocess.run(["bluetoothctl", "connect", TARGET], capture_output=True, timeout=2)
        except Exception:
            pass

        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
            s.settimeout(2.0)
            s.connect((TARGET, 1))
            print("\n[+] KẾT NỐI THÀNH CÔNG VỚI MARTIAN NOTIFIER!")
            return s
        except Exception:
            s.close()
            time.sleep(0.4)
            print(".", end="", flush=True)
    return None

def send_cmd(s, op, payload=b""):
    seq = 0x00
    length = len(payload)
    pkt = bytes([0x3C, op, seq, length]) + payload + b">"
    s.send(pkt)
    time.sleep(0.1)
    try:
        resp = s.recv(1024)
        print(f"TX [0x{op:02X}]: {pkt.hex()} -> RX: {resp.hex()} (ASCII: {resp})")
        return resp
    except socket.timeout:
        print(f"TX [0x{op:02X}]: {pkt.hex()} -> (No response)")
        return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        print("\n[-] Không kết nối được sau 20s.")
        sys.exit(1)

    s.settimeout(0.4)

    print("\n--- 1. Kiểm tra Opcode 0x0A (Info/Battery/Version) ---")
    resp_0a = send_cmd(s, 0x0A)
    if resp_0a and len(resp_0a) >= 7:
        v_major = resp_0a[4]
        v_minor = resp_0a[5]
        bat = resp_0a[6]
        print(f"[*] PHÂN TÍCH: Firmware Version: {v_major}.{v_minor:02d} | Mức Pin: {bat}% ({hex(bat)})")

    print("\n--- 2. Kiểm tra Opcode 0x0C ---")
    send_cmd(s, 0x0C)

    print("\n--- 3. Thử nghiệm gửi chuỗi Text lên OLED ---")
    test_msg = b"HELLO MARTIAN"
    for op in [0x01, 0x02, 0x03, 0x05, 0x06, 0x07, 0x08, 0x0B, 0x0C, 0x0D, 0x0E, 0x10]:
        print(f"Thử đẩy text qua Opcode 0x{op:02X}:")
        send_cmd(s, op, test_msg)

    print("\n[*] Giữ kết nối 3s để quan sát đồng hồ...")
    time.sleep(3)
    s.close()
    print("[+] Đóng kết nối.")

if __name__ == "__main__":
    main()
