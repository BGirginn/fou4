#!/bin/bash

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}fou4 Global Kurulum Betiği${NC}"
echo -e "${YELLOW}UYARI: Bu betik, Python paketlerini sistem geneline kuracak ve sanal ortam korumasını devre dışı bırakacaktır.${NC}"
echo "======================================================================"

# --- Adım 1: Sudo yetkilerini kontrol et ---
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[X] Bu betik sudo yetkileriyle çalıştırılmalıdır. Lütfen 'sudo ./global_install.sh' komutunu kullanın.${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] Sudo yetkileri mevcut.${NC}"

# Projenin bulunduğu tam yolu al
PROJECT_DIR=$(pwd)

# --- Adım 2: Gerekli Python kütüphanelerini sistem geneline kur ---
echo "[!] Python kütüphaneleri sistem geneline kuruluyor..."
echo "[!] Kali'nin sanal ortam koruması (--break-system-packages) ile devre dışı bırakılacak."

# requirements.txt dosyasının varlığını kontrol et
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}[X] Hata: requirements.txt dosyası bulunamadı!${NC}"
    exit 1
fi

python3 -m pip install --break-system-packages -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}[X] Hata: Python kütüphaneleri kurulamadı. Lütfen hatayı kontrol edin.${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] Gerekli Python kütüphaneleri başarıyla kuruldu.${NC}"

# --- Adım 3: Ana betiği çalıştırılabilir yap ---
echo "[!] Ana betik (fou4.py) çalıştırılabilir yapılıyor..."
chmod +x fou4.py
echo -e "${GREEN}[✓] İzinler ayarlandı.${NC}"

# --- Adım 4: 'fou4' komutunu oluştur ---
# /usr/local/bin klasörüne sembolik link oluşturarak komutu global hale getir
echo "[!] 'fou4' komutu /usr/local/bin altına oluşturuluyor..."
ln -sf "$PROJECT_DIR/fou4.py" /usr/local/bin/fou4
if [ $? -ne 0 ]; then
    echo -e "${RED}[X] Hata: 'fou4' komutu oluşturulamadı. /usr/local/bin dizinine yazma izniniz olduğundan emin olun.${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] Sembolik link başarıyla oluşturuldu: /usr/local/bin/fou4${NC}"

# --- Bitiş ---
echo ""
echo -e "${GREEN}==================== KURULUM TAMAMLANDI ====================${NC}"
echo -e "Artık yeni bir terminal açıp herhangi bir dizindeyken 'fou4' yazarak aracı çalıştırabilirsiniz."
echo "Örnek kullanım:"
echo -e "${YELLOW}  fou4 --module network --tool port-scan --target 127.0.0.1${NC}"
echo ""
