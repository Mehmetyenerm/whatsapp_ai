#!/bin/bash

# WhatsApp AI - Başlatma Scripti
# Tek komutla tüm servisleri başlatır

# Renkler (terminalde görüntü iyileştirme)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Proje kökünü belirle
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Başlık
echo -e "${BLUE}"
echo "╔════════════════════════════════════╗"
echo "║   WhatsApp AI - Başlatma Scripti   ║"
echo "╚════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# 1. ÖN KONTROLLER
# ============================================================================

echo -e "${YELLOW}[1/5] Ön kontroller yapılıyor...${NC}"

# .env dosyası kontrolü
if [ ! -f ".env" ]; then
    echo -e "${RED}✗ .env dosyası bulunamadı!${NC}"
    echo ""
    echo "Lütfen .env dosyasını oluşturun:"
    echo -e "  ${BLUE}cp wa_back/.env.example .env${NC}"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ .env dosyası bulundu${NC}"

# Python kontrol
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 yüklü değil${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION bulundu${NC}"

# Node.js kontrol
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js yüklü değil${NC}"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION bulundu${NC}"

# ============================================================================
# 2. KLASÖR OLUŞTUR
# ============================================================================

echo -e "${YELLOW}[2/5] Gerekli klasörler oluşturuluyor...${NC}"

mkdir -p auth_info
mkdir -p media
mkdir -p data
mkdir -p knowledge

echo -e "${GREEN}✓ Klasörler oluşturuldu${NC}"

# ============================================================================
# 3. VIRTUAL ENVIRONMENT VE BAĞIMLILIKLARI KUR
# ============================================================================

echo -e "${YELLOW}[3/5] Python ortamı hazırlanıyor...${NC}"

if [ ! -d ".venv" ]; then
    echo "  Virtual environment oluşturuluyor..."
    python3 -m venv .venv
fi

# Virtual environment'i aktifleştir
source .venv/bin/activate

# Bağımlılıkları kontrol et
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗ requirements.txt bulunamadı${NC}"
    exit 1
fi

pip install -r requirements.txt
echo -e "${GREEN}✓ Python bağımlılıkları yüklendi${NC}"

# Node.js bağımlılıklarını kontrol et
if [ ! -d "wa_api/node_modules" ]; then
    echo -e "${YELLOW}  Node.js bağımlılıkları yükleniyor (ilk kez uzun sürebilir)...${NC}"

    cd wa_api
    npm install
    cd ..
fi

echo -e "${GREEN}✓ Node.js bağımlılıkları tamam${NC}"

# ============================================================================
# 4. SERVISLER BAŞLAT
# ============================================================================

echo -e "${YELLOW}[4/5] Servisler başlatılıyor...${NC}"

# Log dosyalarını temizle
> backend.log
> wa_api.log

# Python Backend başlat
echo -e "${BLUE}  → FastAPI Backend (port 8000) başlatılıyor...${NC}"
cd "$PROJECT_ROOT/wa_back"
uvicorn main:app --reload  > "$PROJECT_ROOT/backend.log" 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}  ✓ Backend PID: $BACKEND_PID${NC}"

# Backend'in başlamasını bekle
sleep 3

# Backend kontrol et
if ! ps -p $BACKEND_PID > /dev/null; then
    echo -e "${RED}✗ Backend başlatılamadı!${NC}"
    echo "Hata logları:"
    cat "$PROJECT_ROOT/backend.log"
    exit 1
fi

# Node.js Frontend başlat
echo -e "${BLUE}  → WhatsApp API (port 3000) başlatılıyor...${NC}"
cd "$PROJECT_ROOT/wa_api"
npm run dev  > "$PROJECT_ROOT/wa_api.log" 2>&1 & FRONTEND_PID=$!
echo -e "${GREEN}  ✓ wa_api PID: $FRONTEND_PID${NC}"

# Frontend kontrol et
sleep 2
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${RED}✗ wa_api başlatılamadı!${NC}"
    echo "Hata logları:"
    cat "$PROJECT_ROOT/wa_api.log"
    kill $BACKEND_PID
    exit 1
fi

# ============================================================================
# 5. TAMAMLANDI
# ============================================================================

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ WhatsApp AI Başarıyla Başlatıldı!     ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📊 Servis Bilgileri:${NC}"
echo "  Backend  (FastAPI)   : http://127.0.0.1:8000"
echo "  Whatsapp Api (WhatsApp)  : https://127.0.0.1:3000"
echo "  API Dokümantasyonu   : http://127.0.0.1:8000/docs"
echo ""

echo -e "${BLUE}📝 Logları İzleme:${NC}"
echo "  tail -f backend.log   (Başka terminalde açın)"
echo "  tail -f wa_api.log (Başka terminalde açın)"
echo ""

echo -e "${BLUE}🛑 Durdurmak İçin:${NC}"
echo "  Ctrl+C (Bu terminalden) veya"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""

echo -e "${BLUE}📱 İlk Bağlantı:${NC}"
echo "  1. wa_api logları izle: tail -f wa_api.log"
echo "  2. QR kodu bul ve WhatsApp'ta taraması yap"
echo "  3. Bağlı cihazlar kısmında göreceksin"
echo ""

echo -e "${YELLOW}ℹ️  İPUÇLARİ:${NC}"
echo "  • Ollama'nın çalıştığından emin ol: ollama serve"
echo "  • .env dosyasını düzenlemek için: nano .env"
echo ""

tail -n 0 -F "$PROJECT_ROOT/backend.log" | sed "s/^/[BACKEND] /; s/\$//" &
BACKEND_LOG_PID=$!

tail -n 0 -F "$PROJECT_ROOT/wa_api.log" | sed "s/^/[WA_API] /; s/\$//" &
WA_API_LOG_PID=$!


# ============================================================================
# ASIL DÖNGÜ - SİGNAL YAKALAMA
# ============================================================================

# Ctrl+C ile temiz kapatma
trap cleanup INT TERM

cleanup() {
    echo ""
    echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║   Servisler kapatılıyor...             ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"

    # Log takip processlerini kapat
    if ps -p $BACKEND_LOG_PID > /dev/null 2>&1; then
        kill $BACKEND_LOG_PID 2>/dev/null
    fi

    if ps -p $WA_API_LOG_PID > /dev/null 2>&1; then
        kill $WA_API_LOG_PID 2>/dev/null
    fi

    # Processleri kapat
    if ps -p $BACKEND_PID > /dev/null; then
        echo -e "${BLUE}Kapatılıyor: Backend (PID $BACKEND_PID)${NC}"
        kill $BACKEND_PID 2>/dev/null
    fi

    if ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${BLUE}Kapatılıyor: wa_api (PID $FRONTEND_PID)${NC}"
        kill $FRONTEND_PID 2>/dev/null
    fi

    # Çocuk processleri bekle
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null

    echo -e "${GREEN}✓ Servisler kapatıldı${NC}"
    echo ""
    exit 0
}

# Processleri izle
echo -e "${YELLOW}Servisler çalışıyor... (Durdurmak için Ctrl+C)${NC}"
echo ""

while true; do
    # Backend kontrolü
    if ! ps -p $BACKEND_PID > /dev/null; then
        echo -e "${RED}✗ Backend kapandı!${NC}"
        echo "Son hatalar:"
        tail -20 backend.log
        cleanup
    fi

    # Frontend kontrolü
    if ! ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${RED}✗ wa_api kapandı!${NC}"
        echo "Son hatalar:"
        tail -20 wa_api.log
        cleanup
    fi

    sleep 5
done
