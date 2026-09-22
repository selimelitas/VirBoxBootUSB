"""GUI'siz mantik testleri: usbboot.py akis kontrolu.

Calistirmak icin:  python3 test_usbboot.py
"""
import sys
import types
import unittest.mock as mock

# --- Sahte tkinter modulu (ortamda tkinter olmasa bile test calisir) ---
fake_tk = types.ModuleType("tkinter")


class _FakeWidget:
    def __init__(self, *a, **k):
        self._store = {}

    def __getattr__(self, name):
        return lambda *a, **k: None

    def __setitem__(self, key, value):
        self._store[key] = value

    def __getitem__(self, key):
        return self._store[key]


class FakeTk(_FakeWidget):
    def mainloop(self):
        pass

    def winfo_screenwidth(self):
        return 1920

    def winfo_screenheight(self):
        return 1080

    def winfo_width(self):
        return 480

    def winfo_height(self):
        return 300

    def winfo_rootx(self):
        return 0

    def winfo_rooty(self):
        return 0

    def update_idletasks(self):
        pass


fake_tk.Tk = FakeTk
fake_tk.Toplevel = FakeTk
fake_tk.StringVar = lambda: _FakeWidget()
fake_tk.Frame = _FakeWidget
fake_tk.Button = _FakeWidget
fake_tk.Label = _FakeWidget
fake_tk.Canvas = _FakeWidget
fake_tk.PhotoImage = _FakeWidget
fake_tk.TclError = Exception
fake_tk.NW = "nw"
fake_tk.EW = "ew"
fake_tk.E = "e"

shown = []
fake_msg = types.SimpleNamespace(showinfo=lambda **k: shown.append(k))


class FakeStyle:
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, name):
        return lambda *a, **k: None


class FakeTtkModule(types.SimpleNamespace):
    Style = FakeStyle


sys.modules["tkinter"] = fake_tk
sys.modules["tkinter.messagebox"] = fake_msg
sys.modules["tkinter.ttk"] = FakeTtkModule(Label=_FakeWidget, Combobox=_FakeWidget, Button=_FakeWidget)

sys.path.insert(0, ".")
from virboxbootusb import usbboot  # noqa: E402


def test_list_disks():
    disks = usbboot.list_disks()
    print("1) list_disks():", disks)
    assert isinstance(disks, list)


def test_random_name():
    name = usbboot.App.generate_random_clone_name()
    print("2) clone adi:", name)
    assert name.startswith("clone-") and name.endswith(".vmdk")
    assert len(name) == len("clone-xxxxx.vmdk")


def test_pkexec_flow():
    """Root degil + pkexec var: komut pkexec ile insa edilmeli, Success mesaji donmeli."""
    app = usbboot.App()
    with mock.patch.object(usbboot, "is_root", return_value=False), \
         mock.patch.object(usbboot.shutil, "which", return_value="/usr/bin/pkexec"), \
         mock.patch.object(usbboot.subprocess, "run") as run_mock, \
         mock.patch.object(usbboot.os, "getuid", return_value=1000), \
         mock.patch.object(usbboot.os, "getgid", return_value=1000), \
         mock.patch.object(app.select_usb, "get", return_value="/dev/sdb (238,5G) (disk)"):
        run_mock.return_value = types.SimpleNamespace(returncode=0, stdout="ok", stderr="")
        app.button_clicked()

    cmd = run_mock.call_args[0][0]
    print("3) insa edilen komut:", cmd[0], cmd[1], "'<script>'")
    assert cmd[0] == "pkexec"
    assert cmd[1] == "sh" and cmd[2] == "-c"
    assert "VBoxManage" in cmd[3]
    assert "chown 1000:1000" in cmd[3]
    assert "/dev/sdb" in cmd[3]
    assert shown and shown[-1]["title"] == "Success"
    print("   -> Success mesaji gosterildi")


def test_no_device_selected():
    """Cihaz secilmediginde hata mesaji donmeli, subprocess calismamali."""
    shown.clear()
    app = usbboot.App()
    with mock.patch.object(app.select_usb, "get", return_value=""), \
         mock.patch.object(usbboot.subprocess, "run") as run_mock:
        app.button_clicked()
    assert not run_mock.called
    assert shown and shown[-1]["title"] == "Error"
    print("4) bos secim -> Error mesaji OK")


if __name__ == "__main__":
    test_list_disks()
    test_random_name()
    test_pkexec_flow()
    test_no_device_selected()
    print("TUM TESTLER OK")
