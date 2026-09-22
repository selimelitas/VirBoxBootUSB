import json
import os
import random
import shlex
import shutil
import string
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

APP_TITLE = "VirtualBox USB Boot"

# Icon search paths: source tree first, then system install location
ICON_CANDIDATES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "image2.png"),
    "/usr/share/icons/hicolor/48x48/apps/image2.png",
]

# ----- Theme -----
BG = "#0f141a"
CARD = "#161f2b"
CARD_BORDER = "#243044"
ACCENT = "#38bdf8"
ACCENT_STRONG = "#0ea5e9"
TEXT = "#e6edf3"
DIM = "#8b98a9"
FONT = "DejaVu Sans"


def is_root():
    """Check if the script is being run as root."""
    return hasattr(os, "geteuid") and os.geteuid() == 0


def find_vboxmanage():
    """Locate the VBoxManage binary."""
    if os.path.isfile("/usr/bin/VBoxManage"):
        return "/usr/bin/VBoxManage"
    return shutil.which("VBoxManage")


def find_lsblk():
    """Locate the lsblk binary."""
    if os.path.isfile("/usr/bin/lsblk"):
        return "/usr/bin/lsblk"
    return shutil.which("lsblk")


def list_disks():
    """Return disk devices as display strings, removable (USB) disks first."""
    lsblk = find_lsblk()
    if not lsblk:
        print("Error retrieving block devices: lsblk not found")
        return []

    try:
        result = subprocess.run(
            [lsblk, "--json", "-o", "NAME,SIZE,TYPE,RM"],
            capture_output=True, text=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError) as e:
        print("Error retrieving block devices:", e)
        return []

    try:
        block_devices_info = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print("Error parsing lsblk output:", e)
        return []

    disks = [
        (f"/dev/{d.get('name', '?')} ({d.get('size', '?')}) ({d.get('type', '?')})",
         d.get("rm", 0) == 1)
        for d in block_devices_info.get("blockdevices", [])
        if d.get("type") == "disk"
    ]
    # Sort removable (USB) disks to the top
    disks.sort(key=lambda item: not item[1])
    return [label for label, _ in disks]


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("480x300")
        self.resizable(False, False)
        self.configure(bg=BG)

        self._center_window()
        self._apply_theme()
        self._build_header()
        self._build_main()
        self._build_statusbar()
        self._set_icon()

        self.refresh_devices()

    # ---------- UI construction ----------

    def _center_window(self):
        """Place the window at the center of the screen."""
        self.update_idletasks()
        w, h = 480, 300
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 3
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _apply_theme(self):
        """Configure ttk widgets to match the dark theme."""
        self.option_add("*TCombobox*Listbox.background", CARD)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT_STRONG)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.option_add("*TCombobox*Listbox.font", (FONT, 10))

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass  # keep the default theme if clam is unavailable

        style.configure("Main.TCombobox",
                        fieldbackground=CARD,
                        background=CARD,
                        foreground=TEXT,
                        arrowcolor=ACCENT,
                        bordercolor=CARD_BORDER,
                        lightcolor=CARD,
                        darkcolor=CARD,
                        borderwidth=1,
                        relief="flat")
        style.map("Main.TCombobox",
                  fieldbackground=[("readonly", CARD)],
                  foreground=[("readonly", TEXT)],
                  bordercolor=[("focus", ACCENT)])

    def _build_header(self):
        header = tk.Frame(self, bg=CARD, pady=12, padx=16)
        header.pack(fill="x")
        header.columnconfigure(1, weight=1)

        logo = self._load_logo(24)
        if logo is not None:
            tk.Label(header, image=logo, bg=CARD).grid(row=0, column=0, rowspan=2, padx=(0, 10))
            self._logo_ref = logo  # prevent garbage collection

        tk.Label(header, text="VirtualBox USB Boot",
                 font=(FONT, 13, "bold"), bg=CARD, fg=TEXT
                 ).grid(row=0, column=1, sticky="w")
        tk.Label(header, text="Boot your VMs from a USB drive",
                 font=(FONT, 9), bg=CARD, fg=DIM
                 ).grid(row=1, column=1, sticky="w")

        about_button = tk.Button(header, text="?", font=(FONT, 10, "bold"),
                                 command=self.open_about, bg=CARD, fg=DIM,
                                 activebackground=CARD, activeforeground=ACCENT,
                                 relief="flat", bd=0, cursor="hand2", width=2)
        about_button.grid(row=0, column=2, rowspan=2, padx=(8, 0))

    def _load_logo(self, size):
        """Return a subsampled PhotoImage of the app logo, or None."""
        for path in ICON_CANDIDATES:
            if os.path.isfile(path):
                try:
                    img = tk.PhotoImage(file=path)
                    factor = max(1, img.width() // size)
                    return img.subsample(factor) if factor > 1 else img
                except tk.TclError:
                    continue
        return None

    def _set_icon(self):
        """Configure the window icon; silently skip if no icon is found."""
        for path in ICON_CANDIDATES:
            if os.path.isfile(path):
                try:
                    self.iconphoto(False, tk.PhotoImage(file=path))
                except tk.TclError:
                    pass  # unsupported format or missing display support
                return

    def _build_main(self):
        main = tk.Frame(self, bg=BG, padx=24, pady=20)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)

        tk.Label(main, text="Select the USB disk you want to boot from:",
                 font=(FONT, 10), bg=BG, fg=DIM, anchor="w"
                 ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        row = tk.Frame(main, bg=BG)
        row.grid(row=1, column=0, sticky="ew")
        row.columnconfigure(0, weight=1)

        self.select_usb = tk.StringVar()
        self.usb_combobox = ttk.Combobox(row, textvariable=self.select_usb,
                                         state="readonly", style="Main.TCombobox",
                                         font=(FONT, 10))
        self.usb_combobox.grid(row=0, column=0, sticky="ew", ipady=6)
        self.usb_combobox.bind("<<ComboboxSelected>>", self.disk_changed)

        refresh_button = tk.Button(row, text="⟳", font=(FONT, 12),
                                   command=self.refresh_devices,
                                   bg=CARD, fg=ACCENT, activebackground=CARD,
                                   activeforeground=TEXT, relief="flat", bd=0,
                                   cursor="hand2", width=3)
        refresh_button.grid(row=0, column=1, padx=(8, 0), ipady=4)

        create_button = tk.Button(main, text="Create VMDK", font=(FONT, 11, "bold"),
                                  command=self.button_clicked,
                                  bg=ACCENT_STRONG, fg="#ffffff",
                                  activebackground=ACCENT, activeforeground="#ffffff",
                                  relief="flat", bd=0, cursor="hand2", pady=8)
        create_button.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        create_button.bind("<Enter>", lambda e: create_button.config(bg=ACCENT))
        create_button.bind("<Leave>", lambda e: create_button.config(bg=ACCENT_STRONG))
        self.create_button = create_button

    def _build_statusbar(self):
        self.status = tk.Label(self, text="Ready", font=(FONT, 9),
                               bg=CARD, fg=DIM, anchor="w", padx=12, pady=6)
        self.status.pack(fill="x", side="bottom")

    def set_status(self, text):
        self.status.config(text=text)

    # ---------- Actions ----------

    def refresh_devices(self):
        """Re-scan disk devices and update the dropdown."""
        self.usb_devices = list_disks()
        self.usb_combobox["values"] = self.usb_devices
        if self.usb_devices:
            self.set_status(f"{len(self.usb_devices)} disk(s) found. Select one and press Create.")
        else:
            self.set_status("No disks found. Plug in a USB drive and press ⟳.")

    def disk_changed(self, event):
        self.set_status(f"Selected: {self.select_usb.get()}")

    @staticmethod
    def generate_random_clone_name():
        """Generate a unique VMDK filename, e.g. 'clone-x5k2a.vmdk'."""
        random_string = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=5))
        return f"clone-{random_string}.vmdk"

    def button_clicked(self):
        try:
            if not self.select_usb.get():
                messagebox.showinfo(
                    title="Error",
                    message="No USB device selected. Please select a device from the dropdown."
                )
                return

            vboxmanage = find_vboxmanage()
            if not vboxmanage:
                messagebox.showinfo(
                    title="Error",
                    message="VBoxManage is not installed or not found in the PATH."
                )
                return

            usb_path = self.select_usb.get().split()[0]  # e.g. '/dev/sdx'
            clone_name = os.path.abspath(self.generate_random_clone_name())

            vbox_args = [
                "createmedium", "disk",
                "--filename", clone_name,
                "--variant", "RawDisk",
                "--format", "VMDK",
                "--property", f"RawDrive={usb_path}",
            ]

            if is_root():
                # Already running as root: run VBoxManage directly.
                command = [vboxmanage] + vbox_args
            elif shutil.which("pkexec"):
                # Graphical privilege escalation via polkit: shows a password
                # prompt without needing a terminal. The resulting VMDK is
                # chowned back to the invoking user in the same step.
                uid, gid = os.getuid(), os.getgid()
                quoted = " ".join(shlex.quote(a) for a in [vboxmanage] + vbox_args)
                command = [
                    "pkexec", "sh", "-c",
                    f"{quoted} && chown {uid}:{gid} {shlex.quote(clone_name)}",
                ]
            else:
                messagebox.showinfo(
                    title="Root required",
                    message=("Neither root privileges nor pkexec is available.\n"
                             "Please run the application from a terminal with sudo.")
                )
                return

            self.set_status("Working... approve the password prompt if it appears.")
            self.create_button.config(state="disabled")
            self.update_idletasks()
            try:
                create_result = subprocess.run(command, capture_output=True, text=True)
            finally:
                self.create_button.config(state="normal")

            if create_result.returncode == 0:
                self.set_status(f"Created {os.path.basename(clone_name)}")
                messagebox.showinfo(
                    title="Success",
                    message=f"VMDK created:\n{clone_name}\n\n{create_result.stdout}"
                )
            else:
                self.set_status("Create failed.")
                messagebox.showinfo(
                    title="Error",
                    message=f"Command not executed successfully:\n{create_result.stderr}"
                )
        except Exception as e:  # last-resort guard for the GUI
            self.set_status("Unexpected error.")
            messagebox.showinfo(
                title="Unexpected Error",
                message=f"An unexpected error occurred: {e}"
            )

    def open_about(self):
        about_window = tk.Toplevel(self)
        about_window.title("About")
        about_window.geometry("420x240")
        about_window.config(bg=BG)
        about_window.resizable(False, False)
        about_window.transient(self)

        # Center the about window relative to the main window
        about_window.geometry("+{}+{}".format(
            self.winfo_rootx() + (self.winfo_width() - 420) // 2,
            self.winfo_rooty() + (self.winfo_height() - 240) // 2))

        tk.Label(about_window, text="VirBoxBootUSB",
                 font=(FONT, 14, "bold"), bg=BG, fg=ACCENT).pack(pady=(24, 4))
        tk.Label(about_window,
                 text=("It's a freeware software for test purpose.\n"
                       "You can improve, share and distribute\nwithout permission."),
                 font=(FONT, 10), bg=BG, fg=TEXT, justify="center").pack(pady=8)

        tk.Label(about_window, text="SelHome Yazılım Inc.© - 2025 · Selim Elitaş",
                 font=(FONT, 9), fg=DIM, bg=BG).pack(side="bottom", pady=12)


def main():
    # The app runs as a normal user; privileges are only requested (via
    # pkexec, with a graphical prompt) when the Create action needs them.
    App().mainloop()


if __name__ == "__main__":
    main()
