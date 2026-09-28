import codecs
import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = "1.0"
DESCRIPTION = "VirtualBox VM USB Boot Addon"
LONG_DESCRIPTION = "A package that allows you to boot your VMs from USB"

setup(
    name="VirBoxBootUSB",
    version=VERSION,
    author="Selim Elitaş",
    author_email="selimelitas7@gmail.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=["virboxbootusb"],
    data_files=[
        ("share/applications", ["VirBoxBootUSB.desktop"]),
        ("share/icons/hicolor/48x48/apps", ["image2.png"]),
    ],
    entry_points={
        "gui_scripts": [
            "VirBoxBootUSB=virboxbootusb.usbboot:master",
        ],
    },
    classifiers=[
        "Environment :: X11 Applications",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
)
