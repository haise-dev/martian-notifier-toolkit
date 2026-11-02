import pexpect
import sys
import time

MAC = "60:0F:77:03:DB:00"

def main():
    print("=" * 60)
    print("[*] Đang khởi động bluetoothctl và yêu cầu ghép nối...")
    print("[*] HÃY NHÌN VÀO MÀN HÌNH OLED ĐỒNG HỒ ĐỂ LẤY MÃ 6 SỐ.")
    print("=" * 60)

    child = pexpect.spawn("bluetoothctl", encoding="utf-8", timeout=30)

    child.sendline("agent KeyboardDisplay")
    child.expect("Agent registered")

    child.sendline("default-agent")
    child.expect("Default agent request successful")

    child.sendline(f"pair {MAC}")

    idx = child.expect([
        r"\[agent\] Enter passkey \(number in 0-999999\):",
        r"Pairing successful",
        r"Failed to pair",
        pexpect.TIMEOUT
    ], timeout=25)

    if idx == 0:
        print("\n" + "=" * 60)
        pin = input(">>> NHẬP MÃ 6 SỐ ĐANG HIỆN TRÊN OLED ĐỒNG HỒ RỒI BẤM ENTER: ")
        print("=" * 60)
        child.sendline(pin.strip())

        idx2 = child.expect([
            r"Pairing successful",
            r"Failed to pair",
            pexpect.TIMEOUT
        ], timeout=15)

        if idx2 == 0:
            print("\n[THÀNH CÔNG] Đã ghép nối thành công!")
            child.sendline(f"trust {MAC}")
            time.sleep(1)
            child.sendline("quit")
            sys.exit(0)
        else:
            print("\n[LỖI] Ghép nối thất bại (sai mã PIN hoặc timeout).")
            child.sendline("quit")
            sys.exit(1)

    elif idx == 1:
        print("\n[THÀNH CÔNG] Đã ghép nối trực tiếp không cần PIN!")
        child.sendline(f"trust {MAC}")
        time.sleep(1)
        child.sendline("quit")
        sys.exit(0)
    else:
        print("\n[LỖI] Không nhận được yêu cầu nhập mã PIN từ đồng hồ.")
        child.sendline("quit")
        sys.exit(1)

if __name__ == "__main__":
    main()
