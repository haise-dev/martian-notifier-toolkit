import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import sys
import os
import threading
import time

AGENT_PATH = "/martian/agent"
TARGET_MAC = os.environ.get("MARTIAN_MAC", "60:0F:77:03:DB:00")

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
        print(f"[+] NUMERIC COMPARISON: Passkey on watch: {passkey:06d}")
        print("[+] Host automatically confirmed!")
        print(">>> Press the TOP-LEFT button on the watch to accept!")
        print("=" * 60)
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        print(f"\n[*] RequestPasskey for: {device}")
        pin = input(">>> Enter 6-digit passkey: ")
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
        print(f"[+] RequestAuthorization for {device} -> Accepted")
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print(f"[+] AuthorizeService for {device} ({uuid}) -> Accepted")
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
        print(f"[*] Pairing with {TARGET_MAC}...")
        dev_iface.Pair()
        print("\n[SUCCESS] PAIRING SUCCESSFUL!")
        dev_props = dbus.Interface(dev, "org.freedesktop.DBus.Properties")
        dev_props.Set("org.bluez.Device1", "Trusted", dbus.Boolean(True))
        print("[+] Device marked as Trusted!")
    except Exception as e:
        print(f"[*] Pairing status: {e}")
    finally:
        time.sleep(2)
        loop.quit()

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"), "org.bluez.AgentManager1")

    loop = GLib.MainLoop()
    agent = MartianAgent(bus, AGENT_PATH, loop)

    # Register as DisplayYesNo so the host automatically approves, user only confirms on the watch
    manager.RegisterAgent(AGENT_PATH, "DisplayYesNo")
    manager.RequestDefaultAgent(AGENT_PATH)
    print("[*] DisplayYesNo Agent registered. Automated pairing active.")

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
