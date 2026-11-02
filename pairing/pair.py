import pexpect
import sys
import time
import os

MAC = os.environ.get("MARTIAN_MAC", "60:0F:77:03:DB:00")

def main():
    print("=" * 60)
    print("BEFORE RUNNING:")
    print("1. On the watch: Press Bottom button -> Setup -> Pair from app.")
    print("   (The LED must be blinking BLUE steadily)")
    print("2. In this mode, the passkey will stay on-screen longer.")
    print("=" * 60)

    child = pexpect.spawn("bluetoothctl", encoding="utf-8", timeout=40)
    child.logfile = sys.stdout

    child.sendline("agent KeyboardDisplay")
    child.expect("Agent registered")

    child.sendline("default-agent")
    child.expect("Default agent request successful")

    print(f"\n[*] Connecting to {MAC} to request pairing...")
    child.sendline(f"pair {MAC}")

    idx = child.expect([
        r"\[agent\] Enter passkey \(number in 0-999999\):",
        r"Pairing successful",
        r"Failed to pair",
        pexpect.TIMEOUT
    ], timeout=30)

    if idx == 0:
        print("\n" + "=" * 60)
        pin = input(">>> ENTER 6-DIGIT PASSKEY SHOWN ON WATCH OLED: ")
        print("=" * 60)
        child.sendline(pin.strip())

        idx2 = child.expect([
            r"Pairing successful",
            r"Failed to pair",
            pexpect.TIMEOUT
        ], timeout=20)

        if idx2 == 0:
            print("\n[SUCCESS] PAIRING AND BONDING COMPLETE!")
            child.sendline(f"trust {MAC}")
            time.sleep(1)
            child.sendline("quit")
            sys.exit(0)
        else:
            print("\n[FAILED] Incorrect passkey or pairing timed out.")
            child.sendline("quit")
            sys.exit(1)
    elif idx == 1:
        print("\n[SUCCESS] Direct pairing completed!")
        child.sendline(f"trust {MAC}")
        time.sleep(1)
        child.sendline("quit")
        sys.exit(0)
    else:
        print("\n[ERROR] No passkey prompt received. Check watch state.")
        child.sendline("quit")
        sys.exit(1)

if __name__ == "__main__":
    main()
