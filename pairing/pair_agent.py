import pexpect
import sys
import time

MAC = "60:0F:77:03:DB:00"

def run_pairing():
    print(f"[*] Starting bluetoothctl to pair with {MAC}...")
    child = pexpect.spawn("bluetoothctl", encoding="utf-8", timeout=25)
    child.logfile = sys.stdout

    child.sendline("agent KeyboardDisplay")
    child.expect("Agent registered")

    child.sendline("default-agent")
    child.expect("Default agent request successful")

    child.sendline(f"pair {MAC}")

    while True:
        idx = child.expect([
            r"\[agent\] Enter passkey \(number in 0-999999\):",
            r"\[agent\] Enter PIN code:",
            r"\[agent\] Confirm passkey \(yes/no\):",
            r"\[agent\] Authorize service \(yes/no\):",
            r"\[agent\] Request authorization \(yes/no\):",
            r"Pairing successful",
            r"Failed to pair",
            r"Device .* not available",
            pexpect.TIMEOUT,
            pexpect.EOF
        ], timeout=15)

        if idx == 0:
            print("\n[+] Providing passkey 000000...")
            child.sendline("000000")
        elif idx == 1:
            print("\n[+] Providing PIN 0000...")
            child.sendline("0000")
        elif idx in (2, 3, 4):
            print("\n[+] Confirming authorization with yes...")
            child.sendline("yes")
        elif idx == 5:
            print("\n[SUCCESS] Pairing successful!")
            child.sendline(f"trust {MAC}")
            time.sleep(1)
            child.sendline("quit")
            return True
        elif idx == 6:
            print("\n[-] Pairing failed.")
            child.sendline("quit")
            return False
        elif idx == 7:
            print("\n[-] Device not available in cache.")
            child.sendline("quit")
            return False
        elif idx in (8, 9):
            print("\n[-] Timeout or EOF.")
            child.sendline("quit")
            return False

if __name__ == "__main__":
    run_pairing()
