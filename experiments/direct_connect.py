import asyncio
import sys
import os
from bleak import BleakClient, BleakScanner

TARGET_MAC = os.environ.get("MARTIAN_MAC", "60:0F:77:03:DB:00")

# GATT UUIDs
BATTERY_CHAR_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
MFG_NAME_UUID = "00002a29-0000-1000-8000-00805f9b34fb"
MODEL_NUM_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
FW_REV_UUID = "00002a26-0000-1000-8000-00805f9b34fb"
SW_REV_UUID = "00002a28-0000-1000-8000-00805f9b34fb"

MARTIAN_CUSTOM_CHAR = "dd721821-53a8-11e3-b3d3-0002a5d5c51b"

def notification_handler(sender, data):
    print(f"[NOTIFY] From handle {sender}: {data.hex()} (ASCII: {data})")

async def main():
    print(f"[*] Scanning for {TARGET_MAC}... (Press button on watch if display is asleep)")
    device = await BleakScanner.find_device_by_address(TARGET_MAC, timeout=20.0)

    if not device:
        print("[-] Watch not found during 20s scan window.")
        sys.exit(1)

    print(f"[+] Found: {device.name} ({device.address}), RSSI: {device.rssi}")
    print("[*] Connecting via direct BLE GATT (no pairing)...")

    async with BleakClient(device, timeout=20.0) as client:
        print(f"[+] Connected: {client.is_connected}")
        print("\n" + "=" * 50)
        print("DEVICE INFORMATION:")
        print("=" * 50)

        # 1. Read battery
        try:
            bat = await client.read_gatt_char(BATTERY_CHAR_UUID)
            print(f"[BATTERY] Current level: {bat[0]}%")
        except Exception as e:
            print(f"[BATTERY] Read error: {e}")

        # 2. Read hardware/firmware strings
        info_chars = [
            ("Manufacturer", MFG_NAME_UUID),
            ("Model Number", MODEL_NUM_UUID),
            ("Firmware Rev", FW_REV_UUID),
            ("Software Rev", SW_REV_UUID),
        ]
        for label, uuid in info_chars:
            try:
                raw = await client.read_gatt_char(uuid)
                print(f"[{label}]: {raw.decode('utf-8', errors='replace').strip()}")
            except Exception as e:
                print(f"[{label}]: Error {e}")

        # 3. Test Martian Vendor characteristic
        print("\n" + "=" * 50)
        print("MARTIAN VENDOR SERVICE:")
        print("=" * 50)
        try:
            print(f"[*] Subscribing to notifications on {MARTIAN_CUSTOM_CHAR}...")
            await client.start_notify(MARTIAN_CUSTOM_CHAR, notification_handler)
            print("[+] Notification subscription successful!")
        except Exception as e:
            print(f"[-] Notification subscription failed: {e}")

        print("\n[+] Holding connection for 5s to verify link stability...")
        await asyncio.sleep(5)
        print("[+] Direct connection test complete.")

if __name__ == "__main__":
    asyncio.run(main())
