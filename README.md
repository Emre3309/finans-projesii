# Finans Takip Uygulaması (Windows)

Basit bir **kâr-zarar** takip uygulaması. Faturaları/işlemleri manuel girersiniz; uygulama **haftalık/aylık** toplamları ve grafik üretir.

## Kurulum (Windows)
1) [Python 3.12+](https://www.python.org/downloads/windows/) kurulu olsun. Kurarken **"Add Python to PATH"** kutusunu işaretlemeyi unutmayın.
2) Proje klasörünü indirin ve bir klasöre çıkartın.
3) PowerShell'i bu klasörün içinde açın ve sanal ortam oluşturun:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4) Uygulamayı çalıştırın:
   ```powershell
   python main.py
   ```

## Özellikler
- İşlem ekleme: **tarih, dükkân, tür (gelir/gider), tutar, not**
- Kayıtları tablo halinde görme ve tarih/tür filtreleme
- Toplam **gelir, gider, kâr** hesapları
- **CSV'ye aktar** butonu
- **Aylık/Haftalık** grafikleri

## Dosyalar
- `main.py` — PySide6 arayüz
- `database.py` — SQLite veritabanı işlemleri
- `utils.py` — basit yardımcılar

## Notlar
- Veritabanı dosyası: `data.db` (aynı klasörde otomatik oluşur)
- Tür için sadece `gelir` ve `gider` kullanın.
- Her şey yerel cihazınızda çalışır, internet gerekmez.