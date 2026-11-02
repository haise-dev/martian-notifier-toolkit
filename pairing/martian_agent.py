import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import sys
import threading
import time

AGENT_PATH = "/martian/agent"
TARGET_MAC = "60:0F:77:03:DB:00"

class MartianAgent(dbus.service.Object):
    def __init__(self, bus, path, loop):
        super().__init__(bus, path)
        self.loop = loop

    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Release(self):
        print("[*] Agent released")

    @dbus.service.method("org.bluez.Agent1", in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print("\n" + "=" * 60)
        print(f"[+] NUMERIC COMPARISON: Mã hiển thị trên đồng hồ: {passkey:06d}")
        print("[+] Máy tính ĐÃ TỰ ĐỘNG XÁC NHẬN!")
        print(">>> BẤM NÚT TRÊN BÊN TRÁI TRÊN ĐỒNG HỒ ĐỂ ĐỒNG Ý!")
        print("=" * 60)
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        print(f"\n[*] Yêu cầu Passkey cho: {device}")
        pin = input(">>> NHẬP 6 SỐ: ")
        try:
            return dbus.UInt32(int(pin.strip()))
        except Exception:
            return dbus.UInt32(0)

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        print(f"[*] RequestPinCode: {device}")
        return "0000"

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        print(f"[+] RequestAuthorization cho {device} -> Chấp thuận")
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print(f"[+] AuthorizeService cho {device} ({uuid}) -> Chấp thuận")
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Cancel(self):
        print("[*] Cancel called")

def pair_worker(bus, loop):
    time.sleep(1)
    dev_path = "/org/bluez/hci0/dev_" + TARGET_MAC.replace(":", "_")
    try:
        dev = bus.get_object("org.bluez", dev_path)
        dev_iface = dbus.Interface(dev, "org.bluez.Device1")
        print(f"[*] Đang pair với {TARGET_MAC}...")
        dev_iface.Pair()
        print("\n[THÀNH CÔNG] ĐÃ GHÉP NỐI THÀNH CÔNG!")
        dev_props = dbus.Interface(dev, "org.freedesktop.DBus.Properties")
        dev_props.Set("org.bluez.Device1", "Trusted", dbus.Boolean(True))
        print("[+] Đã lưu Trusted!")
    except Exception as e:
        print(f"[*] Trạng thái: {e}")
    finally:
        time.sleep(2)
        loop.quit()

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"), "org.bluez.AgentManager1")

    loop = GLib.MainLoop()
    agent = MartianAgent(bus, AGENT_PATH, loop)

    # Đăng ký với DisplayYesNo để máy tính tự động Approve, người dùng chỉ cần bấm nút trên đồng hồ!
    manager.RegisterAgent(AGENT_PATH, "DisplayYesNo")
    manager.RequestDefaultAgent(AGENT_PATH)
    print("[*] Agent DisplayYesNo đã kích hoạt. Bạn KHÔNG CẦN gõ số.")

    t = threading.Thread(target=pair_worker, args=(bus, loop), daemon=True)
    t.start()

    try:
        loop.run()
    finally:
        try:
            manager.UnregisterAgent(AGENT_PATH)
        except Exception:
            pass

if __name__ == "__main__":
    main()
