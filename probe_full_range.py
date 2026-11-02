import socket
import struct
import subprocess
import time
import sys

TARGET = "60:0F:77:03:DB:00"

SOL_BLUETOOTH = 274
BT_SECURITY = 4
BT_SECURITY_MEDIUM = 2

def connect():
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
    s.settimeout(5.0)
    s.connect((TARGET, 1))
    return s

def main():
    print("[*] Đang kết nối tới RFCOMM...")
    try:
        s = connect()
        print("[+] KẾT NỐI THÀNH CÔNG!")
    except Exception as e:
        print(f"[-] Không kết nối được: {e}")
        sys.exit(1)

    s.settimeout(0.08)

    # Flush greeting
    try:
        s.recv(1024)
    except Exception:
        pass

    results = {}
    print("[*] Đang quét dải opcode từ 0x10 đến 0xFF (delay 35ms)...")
    for op in range(0x10, 0x100):
        # < OP 00 00 >
        pkt = bytes([0x3C, op, 0x00, 0x00, 0x3E])
        try:
            s.send(pkt)
            time.sleep(0.035)
            resp = s.recv(1024)
            resp_type = resp[1] if len(resp) > 1 else None
            # Bỏ qua 0x04 (NAK chuẩn)
            if resp_type != 0x04:
                print(f"[ĐẶC BIỆT] Opcode 0x{op:02X} -> Phản hồi: {resp.hex()} (Type: 0x{resp_type:02X})")
                results[op] = resp.hex()
        except socket.timeout:
            pass
        except Exception as e:
            print(f"Ngắt quãng tại 0x{op:02X}: {e}")
            break

    print("\n" + "=" * 60)
    print(f"TỔNG KẾT: Tìm thấy {len(results)} opcodes đặc biệt từ 0x10 đến 0xFF:")
    for op, r_hex in results.items():
        print(f"- 0x{op:02X}: {r_hex}")
    print("=" * 60)

    s.close()

if __name__ == "__main__":
    main()
