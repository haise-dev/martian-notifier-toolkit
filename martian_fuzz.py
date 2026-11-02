import socket
import struct
import subprocess
import time
import sys

TARGET = "60:0F:77:03:DB:00"

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

def main():
    print("[*] Đang chờ đồng hồ thức giấc... HÃY BẤM NÚT DƯỚI BÊN TRÁI TRÊN ĐỒNG HỒ!")

    s = None
    connected = False
    start_time = time.time()

    while time.time() - start_time < 20.0:
        # Thử kết nối baseband trước
        try:
            subprocess.run(["bluetoothctl", "connect", TARGET], capture_output=True, timeout=3)
        except Exception:
            pass

        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
            s.settimeout(2.0)
            s.connect((TARGET, 1))
            connected = True
            print("\n[+] ĐÃ KẾT NỐI THÀNH CÔNG VỚI ĐỒNG HỒ TRÊN RFCOMM CH 1!")
            break
        except Exception:
            s.close()
            time.sleep(0.5)
            print(".", end="", flush=True)

    if not connected:
        print("\n[-] Quá thời gian 20s không kết nối được.")
        sys.exit(1)

    s.settimeout(0.3)
    letters = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?"

    test_framings = [
        ("Short", b"<", b">"),
        ("Standard", b"<", b"\x00\x00>"),
        ("Param0", b"<", b"\x00\x01\x00>"),
        ("Param1", b"<", b"\x00\x01\x01>"),
    ]

    recognized_cmds = []

    for name, prefix, suffix in test_framings:
        print(f"\n[*] Kiểm tra định dạng: {name} (Mẫu: {prefix}[C]{suffix})")
        for b in letters:
            pkt = prefix + bytes([b]) + suffix
            try:
                s.send(pkt)
                time.sleep(0.04)
                resp = s.recv(1024)
                print(f"[RECOG] Lệnh: {chr(b)} -> Phản hồi: {resp} (hex: {resp.hex()})")
                recognized_cmds.append((chr(b), name, pkt.hex(), resp.hex()))
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Lỗi: {e}")
                break

    print("\n" + "=" * 60)
    print("TỔNG HỢP CÁC LỆNH ĐƯỢC ĐỒNG HỒ PHẢN HỒI:")
    for cmd, fmt, p_hex, r_hex in recognized_cmds:
        print(f"- Lệnh '{cmd}' ({fmt}): Gửi {p_hex} -> Nhận {r_hex}")
    print("=" * 60)

    s.close()

if __name__ == "__main__":
    main()
