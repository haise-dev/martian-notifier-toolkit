import asyncio
import sys
from bleak import BleakClient, BleakScanner

TARGET_MAC = "60:0F:77:03:DB:00"

# GATT UUIDs
BATTERY_CHAR_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
MFG_NAME_UUID = "00002a29-0000-1000-8000-00805f9b34fb"
MODEL_NUM_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
FW_REV_UUID = "00002a26-0000-1000-8000-00805f9b34fb"
SW_REV_UUID = "00002a28-0000-1000-8000-00805f9b34fb"

MARTIAN_CUSTOM_CHAR = "dd721821-53a8-11e3-b3d3-0002a5d5c51b"

def notification_handler(sender, data):
    print(f"[NOTIFY] Từ handle {sender}: {data.hex()} (ASCII: {data})")

async def main():
    print(f"[*] Đang quét tìm đồng hồ {TARGET_MAC} (Hãy bấm nút trên đồng hồ nếu màn hình đang tắt)...")
    device = await BleakScanner.find_device_by_address(TARGET_MAC, timeout=20.0)

    if not device:
        print("[-] Không tìm thấy đồng hồ phát sóng trong 20 giây.")
        sys.exit(1)

    print(f"[+] Tìm thấy: {device.name} ({device.address}), RSSI: {device.rssi}")
    print("[*] Đang kết nối trực tiếp (GATT thuần, KHÔNG Pair)...")

    # pair=False by default in Bleak
    async with BleakClient(device, timeout=20.0) as client:
        print(f"[+] KẾT NỐI THÀNH CÔNG: {client.is_connected}")
        print("\n" + "=" * 50)
        print("THÔNG TIN THIẾT BỊ:")
        print("=" * 50)

        # 1. Đọc pin
        try:
            bat = await client.read_gatt_char(BATTERY_CHAR_UUID)
            print(f"[PIN] Mức pin hiện tại: {bat[0]}%")
        except Exception as e:
            print(f"[PIN] Không đọc được: {e}")

        # 2. Đọc thông tin phần cứng/firmware
        info_chars = [
            ("Nhà sản xuất", MFG_NAME_UUID),
            ("Model", MODEL_NUM_UUID),
            ("Firmware", FW_REV_UUID),
            ("Software", SW_REV_UUID),
        ]
        for label, uuid in info_chars:
            try:
                raw = await client.read_gatt_char(uuid)
                print(f"[{label}]: {raw.decode('utf-8', errors='replace').strip()}")
            except Exception as e:
                print(f"[{label}]: Lỗi {e}")

        # 3. Kiểm tra characteristic Vendor Martian
        print("\n" + "=" * 50)
        print("DỊCH VỤ VENDOR MARTIAN:")
        print("=" * 50)
        try:
            print(f"[*] Thử đăng ký nhận Notification từ {MARTIAN_CUSTOM_CHAR}...")
            await client.start_notify(MARTIAN_CUSTOM_CHAR, notification_handler)
            print("[+] Đăng ký Notification thành công!")
        except Exception as e:
            print(f"[-] Đăng ký Notification thất bại: {e}")

        print("\n[+] Giữ kết nối trong 5 giây để kiểm tra độ ổn định...")
        await asyncio.sleep(5)
        print("[+] Hoàn tất phiên kiểm tra trực tiếp.")

if __name__ == "__main__":
    asyncio.run(main())
