# 🚀 DLSS Enabler for Linux (GUI)

<p align="center">
  <img src="assets/icon.png" width="128" height="128" alt="DLSS Enabler Linux Logo" />
</p>

<p align="center">
  <b>Tüm Linux Dağıtımları İçin Otomatik DLSS ve Frame Generation Yöneticisi</b><br>
  <i>Universal DLSS Upscaler & Frame Generation Injector for Proton / Wine</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Linux-blue?logo=linux" alt="Platform Linux" />
  <img src="https://img.shields.io/badge/Python-3.9+-yellow?logo=python" alt="Python 3" />
  <img src="https://img.shields.io/badge/UI-PyQt6-green?logo=qt" alt="PyQt6" />
  <img src="https://img.shields.io/badge/Proton-Compatible-purple?logo=steam" alt="Proton Compatible" />
  <img src="https://img.shields.io/badge/License-MIT-orange" alt="MIT License" />
</p>

---

## 🇹🇷 Türkçe Açıklama

**DLSS Enabler for Linux**, Linux oyuncularının DLSS 2+ (Super Resolution) ve DLSS 3 (Frame Generation / Kare Üretimi) özelliklerini tüm ekran kartlarında (NVIDIA RTX/GTX, AMD Radeon, Intel Arc) tek tıkla kurup yönetmelerini sağlayan modern ve şık bir masaüstü uygulamasıdır.

### ✨ Öne Çıkan Özellikler
- 🔍 **Otomatik Oyun Tarama:** Steam (Yerel, Flatpak, Snap), Heroic Games Launcher (Epic Games, GOG, Amazon Nile), Lutris ve Bottles kütüphanelerinizi tek tıkla otomatik olarak tarar.
- 🎯 **Akıllı Hedef Tespiti:** Unreal Engine shipping dosyalarını (`*Win64-Shipping.exe`), DirectX 12 ikililerini ve alt klasörleri otomatik analiz eder.
- ⚡ **Tek Tıkla En Güncel Sürüm İndirme:** DLSS Enabler ve OptiScaler'ın en güncel resmi GitHub sürümlerini arka planda indirir, açar ve hazır bekletir.
- 🛡️ **Güvenli Yedekleme & Geri Alma (Unpatch):** Orijinal DLL dosyalarını otomatik yedekler (`.dlss_backup`). İstediğiniz zaman tek tıkla oyunu ilk haline döndürür.
- 🎛️ **Geniş Hook Yöntemleri:** `version.dll`, `dxgi.dll`, `winmm.dll`, `d3d12.dll`, `dinput8.dll` arasından oyuna özel önerilen yöntemi otomatik seçer.
- 📋 **Tek Tıkla Başlatma Seçeneği Kopyalama:** Steam ve Proton için gerekli `WINEDLLOVERRIDES="version=n,b" SteamDeck=0 %command%` kodunu tek tıkla panoya kopyalar.
- 🎨 **Siberpunk / Koyu Tema Arayüzü:** Akıcı arayüz, arama çubuğu, platform filtreleri ve oyun kapak görselleri.
- 🐧 **Her Dağıtıma Uyumlu:** Arch, CachyOS, Fedora, Ubuntu, Debian, Pop!_OS, SteamOS, Bazzite ve Manjaro ile tam uyumlu.

---

## 🇬🇧 English Summary

A sleek, native desktop application for Linux gamers to automatically scan installed games and inject the latest **DLSS Enabler** and **OptiScaler** binaries into Proton/Wine game directories with a single click.

---

## 📦 Kurulum / Installation

### Gereksinimler / Prerequisites
- **Python 3.9+**
- **PyQt6** ve **requests**
- **Wine** (Installer çıkarımı için)

#### Dağıtıma Göre Paket Kurulumu:
- **Arch Linux / CachyOS / Manjaro:**
  ```bash
  sudo pacman -S python python-pyqt6 python-requests wine
  ```
- **Ubuntu / Debian / Linux Mint / Pop!_OS:**
  ```bash
  sudo apt install python3 python3-pyqt6 python3-requests wine
  ```
- **Fedora / Nobara / RHEL:**
  ```bash
  sudo dnf install python3 python3-qt6 python3-requests wine
  ```

---

### 🚀 Hızlı Kurulum / Quick Install

Depoyu klonlayıp tek komutla kurun:

```bash
git clone https://github.com/YYOzcan/dlss-enabler-linux.git
cd dlss-enabler-linux
./install.sh
```

Kurulum tamamlandığında uygulama menünüzde **DLSS Enabler** simgesi görünecektir veya terminalden şu komutla çalıştırabilirsiniz:
```bash
dlss-enabler-gui
```

---

## 🎮 Nasıl Kullanılır? / How to Use

1. Uygulamayı açın. Oyunlarınız (Steam, Heroic, Lutris vb.) otomatik taranacaktır.
2. Sağ üstteki **Check / Update** butonu ile en güncel DLSS Enabler ikililerini indirin (halihazırda otomatik kontrol edilir).
3. Listeden oynamak istediğiniz oyunu seçin.
4. **"⚡ Install DLSS Enabler"** butonuna tıklayın.
5. **"📋 Copy"** butonuna basarak Proton başlatma seçeneğini kopyalayın:
   ```text
   WINEDLLOVERRIDES="version=n,b" SteamDeck=0 %command%
   ```
6. Steam'de oyuna sağ tıklayıp **Özellikler > Başlatma Seçenekleri** kutusuna bu satırı yapıştırın.
7. Oyunu başlatın ve oyun içi ayarlardan DLSS ve Frame Generation'ı açın!

---

## 📁 Proje Yapısı / Project Structure

```text
dlss-enabler-linux/
├── assets/                  # SVG & PNG uygulama simgeleri
├── bin/
│   └── dlss-enabler-gui     # Başlatıcı betik
├── src/
│   └── dlss_enabler/
│       ├── downloader.py    # GitHub release indirici & arşiv açıcı
│       ├── patcher.py       # Güvenli DLL enjektörü ve yedekleme yöneticisi
│       ├── scanner.py       # Steam, Heroic, Lutris, Bottles tarama motoru
│       ├── quirks.py        # Oyun uyumluluk ve tavsiye veritabanı
│       ├── gui/
│       │   ├── main_window.py # PyQt6 modern masaüstü arayüzü
│       │   └── styles.py      # Koyu tema QSS stilleri
│       └── main.py          # Program giriş noktası
├── tests/                   # Otomatik doğrulama testleri
├── install.sh               # Çapraz dağıtım otomatik kurulum betiği
├── uninstall.sh             # Temiz kaldırma betiği
├── dlss-enabler.desktop     # Masaüstü entegrasyon dosyası
├── pyproject.toml           # Standart Python paket yapılandırması
└── requirements.txt         # Bağımlılıklar
```

---

## 🤝 Katkıda Bulunma / Contributing
Hata bildirimleri, yeni oyun önerileri veya pull request'ler her zaman memnuniyetle karşılanır!

## 📜 Lisans / License
Bu proje MIT lisansı ile lisanslanmıştır. DLSS Enabler ve OptiScaler bileşenleri ilgili geliştiricilerine aittir.
