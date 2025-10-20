# 📋 FOU4 - Yapılacaklar Listesi (TODO)

**Proje:** Kali Tool - Penetration Testing Toolkit  
**Durum:** %82 Tamamlandı  
**Son Güncelleme:** 20 Ekim 2025

---

## 🎯 YOL HARİTASI

### ✅ FAZ 0: TAMAMLANMIŞ (100%)
- [x] Wi-Fi Module - Monitor mode, scanning, deauth, handshake, cracking
- [x] Network Module - Port scan, service detection, vuln scan, packet sniffing
- [x] Password Module - SSH, FTP, HTTP, MySQL attacks with Hydra
- [x] Database System - SQLite with workspace management
- [x] Configuration System - JSON config with defaults
- [x] Dependency Checker - Python packages and system tools
- [x] CLI & Interactive Modes - Both modes fully functional
- [x] Rich UI - Beautiful terminal interface

---

### 🔴 FAZ 1: KRİTİK EKSİKLER (1-2 Hafta)

#### 1.1 OSINT - Email Harvesting ⭐⭐⭐⭐⭐
- [ ] `harvest_emails()` fonksiyonu oluştur
- [ ] theHarvester output parsing
- [ ] Email regex pattern matching
- [ ] Email validation (opsiyonel)
- [ ] Database'e email kaydetme
- [ ] Rich table ile gösterim
- [ ] Export email list (txt/csv)
- [ ] Menüye entegrasyon (seçenek 2)

**Tahmini Süre:** 2-3 gün  
**Dosya:** `modules/osint_module.py`  
**Bağımlılık:** theHarvester (zaten kurulu)

**Kod Taslağı:**
```python
def harvest_emails(domain: str) -> List[str]:
    """Collect email addresses from domain using theHarvester"""
    # Run theHarvester
    # Parse output with regex
    # Deduplicate emails
    # Save to database
    # Display results
    return emails
```

---

#### 1.2 Web - XSS Detection ⭐⭐⭐⭐⭐
- [ ] `test_xss_vulnerability()` fonksiyonu oluştur
- [ ] XSS payload library hazırla
- [ ] URL parameter extraction
- [ ] Reflected XSS testing
- [ ] Response analysis
- [ ] Vulnerability reporting
- [ ] Database integration
- [ ] Menü seçenek 3'ü düzelt (Nikto yerine XSS test)

**Tahmini Süre:** 3-4 gün  
**Dosya:** `modules/web_module.py`  
**Bağımlılık:** requests, urllib

**Kod Taslağı:**
```python
def test_xss_vulnerability(target_url: str) -> Dict:
    """Test for XSS vulnerabilities"""
    payloads = ["<script>alert(1)</script>", ...]
    # Extract parameters
    # Test each payload
    # Analyze responses
    # Report vulnerabilities
    return results
```

---

#### 1.3 Web - Web Crawler ⭐⭐⭐⭐
- [ ] `web_crawler()` fonksiyonu oluştur
- [ ] BeautifulSoup entegrasyonu
- [ ] Recursive link extraction
- [ ] Depth control
- [ ] Form detection
- [ ] Asset mapping (js, css, images)
- [ ] Robots.txt parser
- [ ] Sitemap visualization
- [ ] Menüye entegrasyon (seçenek 5)

**Tahmini Süre:** 3-4 gün  
**Dosya:** `modules/web_module.py`  
**Bağımlılık:** `pip install beautifulsoup4 lxml`

**Kod Taslağı:**
```python
def web_crawler(target_url: str, max_depth: int = 2) -> Dict:
    """Crawl website and map structure"""
    # Initialize visited set
    # BFS/DFS crawling
    # Extract links with BeautifulSoup
    # Find forms
    # Build sitemap
    return results
```

---

### 🟡 FAZ 2: ORTA ÖNCELİK (2-3 Hafta)

#### 2.1 OSINT - Social Media OSINT ⭐⭐⭐⭐
- [ ] `social_media_osint()` fonksiyonu
- [ ] Sherlock tool entegrasyonu
- [ ] Username search across platforms
- [ ] Profile information extraction
- [ ] LinkedIn, Twitter, GitHub scraping
- [ ] Username correlation
- [ ] Database kaydetme
- [ ] Menüye entegrasyon (seçenek 4)

**Tahmini Süre:** 4-5 gün  
**Dosya:** `modules/osint_module.py`  
**Bağımlılık:** `pip install sherlock-project`

---

#### 2.2 OSINT - Metadata Extraction ⭐⭐⭐
- [ ] `extract_metadata()` fonksiyonu
- [ ] ExifTool entegrasyonu
- [ ] Image EXIF data extraction
- [ ] PDF metadata parsing
- [ ] Office document properties
- [ ] GPS coordinate extraction
- [ ] Timestamp analysis
- [ ] Menüye entegrasyon (seçenek 5)

**Tahmini Süre:** 3-4 gün  
**Dosya:** `modules/osint_module.py`  
**Bağımlılık:** `apt-get install exiftool`, `pip install PyPDF2 pillow`

---

#### 2.3 Web - Authentication Testing Fix ⭐⭐⭐
- [ ] `test_authentication()` fonksiyonunu düzelt
- [ ] Gerçek brute-force implementasyonu
- [ ] Session handling
- [ ] Cookie management
- [ ] CSRF token handling
- [ ] Veya Hydra'ya yönlendirme yap
- [ ] Results database'e kaydet

**Tahmini Süre:** 2-3 gün  
**Dosya:** `modules/web_module.py`

---

#### 2.4 OSINT - Domain Lookup İyileştirme ⭐⭐⭐
- [ ] theHarvester output parsing ekle
- [ ] Subfinder output parsing ekle
- [ ] WHOIS lookup entegrasyonu
- [ ] DNS record extraction
- [ ] Subdomain'leri database'e kaydet
- [ ] Rich table ile gösterim
- [ ] Subdomain live check

**Tahmini Süre:** 2-3 gün  
**Dosya:** `modules/osint_module.py`

---

### 🟢 FAZ 3: İYİLEŞTİRMELER (1 Hafta)

#### 3.1 Reporting - PDF Export ⭐⭐
- [ ] `export_vulnerabilities_to_pdf()` fonksiyonu
- [ ] ReportLab veya WeasyPrint kullan
- [ ] Güzel PDF template tasarımı
- [ ] Logo ve branding ekle
- [ ] Charts ve graphs
- [ ] Menüye PDF seçeneği ekle

**Tahmini Süre:** 2-3 gün  
**Dosya:** `modules/reporting_module.py`  
**Bağımlılık:** `pip install reportlab` veya `pip install weasyprint`

---

#### 3.2 Reporting - Delete Report ⭐⭐
- [ ] Report dosyalarını listele
- [ ] Kullanıcıdan seçim al
- [ ] Confirmation prompt
- [ ] Dosya silme işlemi
- [ ] Success/error feedback
- [ ] Menüye entegrasyon (seçenek 4)

**Tahmini Süre:** 1 gün  
**Dosya:** `modules/reporting_module.py`

---

#### 3.3 Workspace - Clean Workspace ⭐
- [ ] `clean_workspace()` fonksiyonu
- [ ] Temporary files temizleme
- [ ] Old captures silme
- [ ] Database optimization
- [ ] User confirmation
- [ ] Size statistics
- [ ] Menüye entegrasyon (seçenek 5)

**Tahmini Süre:** 1 gün  
**Dosya:** `modules/workspace_module.py`

---

#### 3.4 Workspace - Manual Save Session ⭐
- [ ] Manual save trigger
- [ ] Export workspace data
- [ ] Backup creation
- [ ] Snapshot functionality
- [ ] Compress and archive
- [ ] Menüye düzgün entegrasyon (seçenek 3)

**Tahmini Süre:** 1 gün  
**Dosya:** `modules/workspace_module.py`

---

## 📊 SÜRE TAHMİNLERİ

```
┌─────────────┬──────────────┬────────────┐
│ Faz         │ Özellik      │ Süre       │
├─────────────┼──────────────┼────────────┤
│ Faz 1       │ 3 kritik     │ 1-2 hafta  │
│ Faz 2       │ 4 orta       │ 2-3 hafta  │
│ Faz 3       │ 4 düşük      │ 1 hafta    │
├─────────────┼──────────────┼────────────┤
│ TOPLAM      │ 11 özellik   │ 4-6 hafta  │
└─────────────┴──────────────┴────────────┘
```

**Not:** Part-time çalışma varsayımı ile (günde 2-3 saat)

---

## 🎯 ÖNCELİK TABLOSU

| # | Özellik | Modül | Öncelik | Süre | Status |
|---|---------|-------|---------|------|--------|
| 1 | Email Harvesting | OSINT | 🔴 Kritik | 2-3 gün | ⬜ Todo |
| 2 | XSS Detection | Web | 🔴 Kritik | 3-4 gün | ⬜ Todo |
| 3 | Web Crawler | Web | 🔴 Kritik | 3-4 gün | ⬜ Todo |
| 4 | Social Media OSINT | OSINT | 🟡 Orta | 4-5 gün | ⬜ Todo |
| 5 | Metadata Extraction | OSINT | 🟡 Orta | 3-4 gün | ⬜ Todo |
| 6 | Auth Testing Fix | Web | 🟡 Orta | 2-3 gün | ⬜ Todo |
| 7 | Domain Lookup Fix | OSINT | 🟡 Orta | 2-3 gün | ⬜ Todo |
| 8 | PDF Export | Reporting | 🟢 Düşük | 2-3 gün | ⬜ Todo |
| 9 | Delete Report | Reporting | 🟢 Düşük | 1 gün | ⬜ Todo |
| 10 | Clean Workspace | Workspace | 🟢 Düşük | 1 gün | ⬜ Todo |
| 11 | Manual Save | Workspace | 🟢 Düşük | 1 gün | ⬜ Todo |

---

## 🛠️ GEREKLI KURULUMLAR

### Python Paketleri
```bash
# Faz 1 için
pip install beautifulsoup4 lxml

# Faz 2 için
pip install sherlock-project PyPDF2 pillow python-whois

# Faz 3 için
pip install reportlab weasyprint
```

### Sistem Paketleri
```bash
# Metadata extraction için
sudo apt-get install exiftool

# PDF export için (WeasyPrint kullanılacaksa)
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0
```

---

## 📝 CHECKLIST - Hızlı Takip

### Faz 1 - Kritik (Bu Ay)
- [ ] Email Harvesting
- [ ] XSS Detection
- [ ] Web Crawler

### Faz 2 - Orta (Gelecek Ay)
- [ ] Social Media OSINT
- [ ] Metadata Extraction
- [ ] Auth Testing Fix
- [ ] Domain Lookup Fix

### Faz 3 - Düşük (İsteğe Bağlı)
- [ ] PDF Export
- [ ] Delete Report
- [ ] Clean Workspace
- [ ] Manual Save

---

## 🚀 BAŞLANGIÇ REHBERİ

### İlk Özelliği Eklemek İçin (Email Harvesting)

1. **Dosyayı Aç:**
   ```bash
   nano modules/osint_module.py
   ```

2. **Fonksiyon Ekle:**
   ```python
   def harvest_emails(domain: str) -> List[str]:
       # Implementation here
   ```

3. **Menüye Bağla:**
   ```python
   elif choice == '2':  # Email Harvesting
       domain = Prompt.ask("Enter domain")
       emails = harvest_emails(domain)
   ```

4. **Test Et:**
   ```bash
   python3 fou4.py
   # OSINT Module -> Email Harvesting
   ```

---

## 📈 İLERLEME TAKİBİ

```
Tamamlanan: 0/11 (0%)
[                                        ] 0%

Hedef:
[████████████████████████████████████████] 100%
```

**Son Tamamlanan:** -  
**Şu An Üzerinde Çalışılan:** -  
**Sonraki:** Email Harvesting

---

## 💡 İPUÇLARI

1. **Küçük Adımlarla İlerle:** Her özelliği tek seferde bitirmeye çalışma
2. **Test Et:** Her özellik sonrası mutlaka test et
3. **Commit Yap:** Her tamamlanan özellik için git commit
4. **Dokümante Et:** Yeni fonksiyonlara docstring ekle
5. **Error Handling:** Try-except blokları kullan
6. **User Feedback:** print_info/success/error mesajları ekle

---

## 🔗 İLGİLİ DOSYALAR

- **Detaylı Analiz:** `INCOMPLETE_FEATURES_ANALYSIS.md`
- **Hızlı Referans:** `EKSIK_OZELLIKLER_HIZLI_REFERANS.md`
- **Türkçe Detay:** `EKSIK_OZELLIKLER_DETAYLI_TR.md`
- **Kısa Özet:** `INCOMPLETE_FEATURES_SUMMARY.md`

---

**Başarılar! 🚀**

*"The best time to plant a tree was 20 years ago. The second best time is now."*
