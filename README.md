# VirBoxBootUSB

**VirtualBox USB Boot Addon** — VirtualBox'ta sanal makinelerinizi bir USB diskten
başlatmanızı sağlayan basit bir grafik arayüz (Tkinter).

Aracın yaptığı iş: Seçtiğiniz USB diski (örn. `/dev/sdc`), VirtualBox'ın ham disk
(raw disk) olarak görebildiği bir `clone-xxxxx.vmdk` tanım dosyasına bağlar.
Bu VMDK'yı VM'nize disk olarak ekleyip VM'yi USB'den başlatabilirsiniz.

> ⚠️ **Uyarı:** Ham disk erişimi tehlikeli olabilir. USB diski VM'ye vermeden önce
> ana sistemde **mutlaka çıkarın (unmount)**. Aynı diske aynı anda iki sistem
> yazmaya çalışırsa veri bozulabilir.

---

## Gereksinimler

| Gereksinim | Amaç | Kurulum |
|---|---|---|
| Linux (Pardus/Debian/Ubuntu) | Test edildiği platform | — |
| Python 3.10+ | Uygulama dili | Dağıtımınızın paket yöneticisi |
| `python3-tk` | Grafik arayüz | `sudo apt install python3-tk` |
| VirtualBox (`VBoxManage`) | VMDK oluşturma | `sudo apt install virtualbox` |
| `pkexec` (polkit) | Şifre penceresi | `sudo apt install policykit-1` (çoğu sistemde kurulu) |
| `lsblk` | Disk listeleme | Sistemde varsayılan olarak bulunur |

---

## Kurulum

### 1) Paketi kur

```bash
cd virboxbootusb
sudo pip3 install .
```

Kurulumdan sonra uygulama üç şekilde erişilebilir olur:

- Uygulama menüsünden **VirBoxBootUSB** (masaüstü girdisi kurulur)
- Terminalden `VirBoxBootUSB` komutu
- Doğrudan: `python3 -m virboxbootusb.usbboot`

### 2) Kullanıcı gruplarını ayarla (ÖNEMLİ)

İki grup üyeliği gereklidir. Bu adım **bir kez** yapılır:

```bash
# a) VirtualBox'ın USB cihazlarını VM'lere pas geçebilmesi için:
sudo usermod -aG vboxusers $USER

# b) VirtualBox'ın ham diski (VMDK'nın işaret ettiği /dev/sdX cihazını) okuyabilmesi için:
sudo usermod -aG disk $USER
```

> **Not:** Komutta kullanıcı adından sonra `:grup` **yazılmaz** — sadece kullanıcı adı.
> Doğru: `sudo usermod -aG vboxusers selim`
> Yanlış: `sudo usermod -aG vboxusers selim:selim` (bu chown sözdizimidir, usermod değil)

Ayrıca grup adı **`vboxusers`** (çoğul) şeklindedir; `vboxuser` diye bir grup yoktur.
Doğrulamak için:

```bash
getent group | grep -i vbox
```

### 3) Oturumu yenile

Grup üyelikleri yalnızca **yeni oturumda** etkin olur:

- Oturumu kapatıp açın (veya bilgisayarı yeniden başlatın), sonra kontrol edin:

```bash
id -nG | grep -wx vboxusers && echo "vboxusers: etkin"
id -nG | grep -wx disk      && echo "disk: etkin"
```

İki satır da çıktı vermelidir.

---

## Kullanım

1. USB diski takın. **Disk ana sistemde takılıysa (mount) çıkarın** — dosya
   yöneticisinde diske sağ tık → *Çıkar*.
2. Uygulamayı açın (menüden **VirBoxBootUSB** veya terminalden `VirBoxBootUSB`).
3. Açılır listeden USB diskinizi seçin (çıkartılabilir diskler üste sabitlenir).
4. **Create VMDK** düğmesine basın.
5. Polkit şifre penceresi açılır → kullanıcı şifrenizi girin.
   (Uygulama sadece VMDK oluşturma anında yetki ister; açılışta istemez.)
6. İşlem bitince VM klasörünüzde `clone-xxxxx.vmdk` dosyası oluşur
   (sahipliği otomatik olarak size devredilir).

### VMDK'yı VM'ye ekleme

1. VirtualBox → hedef VM → **Ayarlar → Depolama**
2. **SATA Denetleyicisi** → sabit disk ekle (➕ ikonu) → **Seç**
3. Ortam seçicide **Ekle** düğmesiyle `clone-xxxxx.vmdk` dosyasını gösterin ve seçin
4. VM'yi başlatın — artık USB diskinizden boot eder

> 💡 **İpucu:** VM'nin BIOS sırasinda USB diskin ilk sırada olması gerekmez;
> VMDK zaten doğrudan diski gösterir. Boot sırası VM ayarlarından
> *Sistem → Boot Order* üzerinden değiştirilebilir.

---

## Nasıl çalışır?

`VBoxManage createmedium disk --variant RawDisk` komutu, fiziksel diskin tamamını
kaplayan bir VMDK **tanım dosyası** üretir. Dosya yalnızca ~536 bayttır ve
`/dev/sdX` cihazına işaret eder:

```
# Disk DescriptorFile
version=1
CID=ac63fd42
parentCID=ffffffff
createType="fullDevice"

# Extent description
RW 15730688 FLAT "/dev/sdc" 0
```

VirtualBox bu dosyayı açtığında ham diske erişir — bu yüzden kullanıcının `disk`
grubuna üyeliği gereklidir.

---

## Sorun Giderme

### `Permission problem ... VERR_ACCESS_DENIED`

VirtualBox, VMDK'nın işaret ettiği ham diske erişemiyor demektir.

**Çözüm:**

```bash
sudo usermod -aG disk $USER
```

→ Oturumu kapat/aç → kontrol: `id -nG | grep -wx disk`

Ayrıca VMDK'nın işaret ettiği cihazın izinlerini kontrol edin:

```bash
cat ~/VirtualBox\ VMs/<VM-klasörü>/clone-*.vmdk | grep FLAT
ls -l /dev/sdX        # rw-rw---- root disk görünmeli
```

### `usermod: group 'vboxuser' does not exist`

Grup adı **`vboxusers`** (çoğul) — `x` harfi yok:

```bash
sudo usermod -aG vboxusers $USER
```

### `sudo: şifreyi okumak için bir terminal gereklidir`

Bu hata eski sürümlerde, uygulama açılışta tüm süreci `sudo` ile yeniden başlatmaya
çalışırken olurdu. **Güncel sürümde bu akış kalktı**: yetki yalnızca Create anında,
`pkexec` ile **grafik şifre penceresiyle** istenir. Bu hatayı görüyorsanız
uygulamayı güncel sürüme güncelleyin.

### `No module named 'tkinter'`

`tkinter` pip paketi değildir; sistem paketidir:

```bash
sudo apt install python3-tk
```

### `VBoxManage is not installed`

VirtualBox kurulu değil ya da PATH dışında:

```bash
sudo apt install virtualbox
which VBoxManage    # /usr/bin/VBoxManage olmalı
```

### Listedeki diskler güncel değil

USB'yi takıtıktan sonra penceredeki **⟳** düğmesine basın; uygulama diskleri
yeniden tarar.

---

## Test

GUI gerektirmeden çalışan mantık testleri:

```bash
cd virboxbootusb
python3 test_usbboot.py
```

Beklenen çıktı:

```
1) list_disks(): ['/dev/sdb (238,5G) (disk)', ...]
2) clone adi: clone-xxxxx.vmdk
3) insa edilen komut: pkexec sh '<script>'
   -> Success mesaji gosterildi
4) bos secim -> Error mesaji OK
TUM TESTLER OK
```

---

## Paketleme (DEB)

Debian paketi oluşturmak için:

```bash
cd virboxbootusb
dpkg-buildpackage -us -uc
sudo dpkg -i ../virboxbootusb_1.0_all.deb
```

Not: `debian/control` dosyasına `python3-tk` bağımlılığı eklenebilir
(şu an `setup.py` üzerinden kurulur).

---

## Proje Yapısı

```
virboxbootusb/
├── setup.py                    # setuptools kurulumu + gui_scripts giriş noktası
├── virboxbootusb/
│   ├── __init__.py
│   └── usbboot.py              # Ana uygulama (Tkinter GUI)
├── test_usbboot.py             # GUI'siz mantık testleri
├── VirBoxBootUSB.desktop       # Masaüstü girdisi
├── image2.png                  # Uygulama ikonu
├── debian/                     # DEB paketleme dosyaları
└── LICENCE
```

---

## Yazar

**Selim Elitaş** — SelHome Yazılım Inc.© · 2025

Freeware/test amaçlıdır; geliştirebilir, paylaşabilir ve izinsiz dağıtabilirsiniz.
