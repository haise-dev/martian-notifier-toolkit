import pexpect
import sys
import time
import os

MAC = os.environ.get("MARTIAN_MAC", "60:0F:77:03:DB:00")

def main():
    print("=" * 60)
    print("[*] Launching bluetoothctl pairing process...")
    print("[*] OBSERVE THE WATCH OLED DISPLAY FOR THE 6-DIGIT PASSKEY.")
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
        pin = input(">>> ENTER 6-DIGIT PASSKEY DISPLAYED ON OLED AND PRESS ENTER: ")
        print("=" * 60)
        child.sendline(pin.strip())

        idx2 = child.expect([
            r"Pairing successful",
            r"Failed to pair",
            pexpect.TIMEOUT
        ], timeout=15)

        if idx2 == 0:
            print("\n[SUCCESS] Pairing successful!")
            child.sendline(f"trust {MAC}")
            time.sleep(1)
            child.sendline("quit")
            sys.exit(0)
        else:
            print("\n[ERROR] Pairing failed (incorrect passkey or timeout).")
            child.sendline("quit")
            sys.exit(1)

    elif idx == 1:
        print("\n[SUCCESS] Direct pairing completed without PIN prompt!")
        child.sendline(f"trust {MAC}")
        time.sleep(1)
        child.sendline("quit")
        sys.exit(0)
    else:
        print("\n[ERROR] Did not receive passkey prompt from watch.")
        child.sendline("quit")
        sys.exit(1)

if __name__ == "__main__":
    main()
