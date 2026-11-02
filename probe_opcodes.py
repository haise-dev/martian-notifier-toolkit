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
    print("[*] Đang chờ đồng hồ thức giấc... HÃY BẤM NÚT DƯỚI BÊN TRÁI TRÊN ĐỒNG HỒ!")
    while time.time() - start < timeout_sec:
        # Thử connect baseband qua bluetoothctl
        subprocess.run(["bluetoothctl", "connect", TARGET], capture_output=True, timeout=2)
        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
            s.settimeout(2.0)
            s.connect((TARGET, 1))
            print("\n[+] ĐÃ KẾT NỐI THÀNH CÔNG VỚI ĐỒNG HỒ TRÊN RFCOMM CH 1!")
            return s
        except Exception:
            s.close()
            time.sleep(0.4)
            print(".", end="", flush=True)
    return None

def main():
    s = connect_with_retry(20.0)
    if not s:
        print("\n[-] Hết thời gian chờ kết nối.")
        sys.exit(1)

    s.settimeout(0.06)
    valid_responses = {}

    print("\n[*] Đang probe 256 opcodes (0x00 - 0xFF)...")
    for op in range(256):
        # Packet: < OP SEQ(0) LEN(0) >
        pkt = bytes([0x3C, op, 0x00, 0x00, 0x3E])
        try:
            s.send(pkt)
            time.sleep(0.02)
            resp = s.recv(1024)
            resp_type = resp[1] if len(resp) > 1 else None
            payload = resp[4:-1] if len(resp) > 5 else resp

            # Nếu resp_type khác 0x04 (0x04 là unsupported command)
            if resp_type != 0x04:
                print(f"[ĐẶC BIỆT] OP 0x{op:02X} -> Resp Type: 0x{resp_type:02X} | {resp.hex()} | Data: {payload}")
            else:
                # 0x04 là NAK chuẩn
                pass

            valid_responses[op] = (resp_type, resp.hex(), payload)
        except socket.timeout:
            pass
        except Exception as e:
            print(f"Lỗi tại 0x{op:02X}: {e}")
            break

    print("\n" + "=" * 60)
    print(f"TỔNG KẾT: Có {len(valid_responses)} opcodes có phản hồi từ vi điều khiển.")
    special = [f"0x{op:02X}" for op, (t, _, _) in valid_responses.items() if t != 0x04]
    print(f"Các opcodes ĐẶC BIỆT (khác mã lỗi 0x04): {special}")
    print("=" * 60)
    s.close()

if __name__ == "__main__":
    main()
