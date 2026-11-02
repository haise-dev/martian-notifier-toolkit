import pexpect
import sys
import time

MAC = "60:0F:77:03:DB:00"

def main():
    print("=" * 60)
    print("HƯỚNG DẪN TRƯỚC KHI CHẠY:")
    print("1. Trên đồng hồ: Bấm Nút dưới -> Setup -> Pair from app.")
    print("   (Đèn LED phải đang nháy XANH DƯƠNG liên tục)")
    print("2. Khi ở đúng chế độ này, mã PIN sẽ giữ sáng lâu (không bị tắt vội).")
    print("=" * 60)

    child = pexpect.spawn("bluetoothctl", encoding="utf-8", timeout=40)
    child.logfile = sys.stdout

    child.sendline("agent KeyboardDisplay")
    child.expect("Agent registered")

    child.sendline("default-agent")
    child.expect("Default agent request successful")

    print("\n[*] Đang kết nối tới đồng hồ để lấy mã PIN...")
    child.sendline(f"pair {MAC}")

    idx = child.expect([
        r"\[agent\] Enter passkey \(number in 0-999999\):",
        r"Pairing successful",
        r"Failed to pair",
        pexpect.TIMEOUT
    ], timeout=30)

    if idx == 0:
        print("\n" + "=" * 60)
        pin = input(">>> NHẬP MÃ 6 SỐ ĐANG HIỆN TRÊN OLED ĐỒNG HỒ: ")
        print("=" * 60)
        child.sendline(pin.strip())

        idx2 = child.expect([
            r"Pairing successful",
            r"Failed to pair",
            pexpect.TIMEOUT
        ], timeout=20)

        if idx2 == 0:
            print("\n[THÀNH CÔNG] ĐÃ GHÉP NỐI VÀ LƯU BẢO MẬT HOÀN TẤT!")
            child.sendline(f"trust {MAC}")
            time.sleep(1)
            child.sendline("quit")
            sys.exit(0)
        else:
            print("\n[THẤT BẠI] Sai mã hoặc quá thời gian xác thực.")
            child.sendline("quit")
            sys.exit(1)
    elif idx == 1:
        print("\n[THÀNH CÔNG] Ghép nối trực tiếp thành công!")
        child.sendline(f"trust {MAC}")
        time.sleep(1)
        child.sendline("quit")
        sys.exit(0)
    else:
        print("\n[LỖI] Không nhận được yêu cầu nhập PIN. Kiểm tra lại chế độ trên đồng hồ.")
        child.sendline("quit")
        sys.exit(1)

if __name__ == "__main__":
    main()
