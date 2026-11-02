import asyncio
import sys
from bleak import BleakClient, BleakScanner

TARGET_MAC = "60:0F:77:03:DB:00"

async def main():
    print(f"Scanning for {TARGET_MAC}...")
    device = await BleakScanner.find_device_by_address(TARGET_MAC, timeout=12.0)
    if not device:
        print("Device not found during scan.")
        sys.exit(1)

    print(f"Found: {device.name} ({device.address}), RSSI: {device.rssi}")
    print("Connecting to device...")

    async with BleakClient(device, timeout=15.0) as client:
        print(f"Connected: {client.is_connected}")
        print("\n=== GATT SERVICES & CHARACTERISTICS ===")
        for service in client.services:
            print(f"\n[Service] {service.uuid} ({service.description})")
            for char in service.characteristics:
                props = ", ".join(char.properties)
                print(f"  [Char] {char.uuid} ({char.description}) | Props: [{props}]")
                for desc in char.descriptors:
                    print(f"    [Desc] {desc.uuid} ({desc.description})")

if __name__ == "__main__":
    asyncio.run(main())
