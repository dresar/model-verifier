# Model Verifier AI

Platform Verifikasi Keaslian & Black-Box Behavioral Probing Engine untuk Model AI Gateway (OpenAI, Anthropic, dan Router ByNara).

Dibangun dan Dikembangkan oleh: **Eka Syarif Maulana** (`eka.ckp16799@gmail.com`)  
Repositori Resmi: [https://github.com/dresar/model-verifier](https://github.com/dresar/model-verifier)  
Lisensi: **AGPL-3.0-or-later**

---

## 🌟 Tentang Proyek

**Model Verifier AI** adalah sistem verifikasi independen berskala produksi yang dirancang untuk menguji, memvalidasi, dan mendeteksi integritas model AI yang diakses melalui reverse proxy, agregator API, atau gateway pihak ketiga (seperti Router ByNara, OneAPI, NewAPI, atau proxy kustom).

Sistem ini membantu pengembang dan organisasi memastikan bahwa model AI yang mereka bayar dan panggil adalah model asli yang sesungguhnya, bukan model murah yang disamarkan (*model substitution / downgrade attack*).

---

## 🚀 Fitur Utama

1. **Pengujian Black-Box Multi-Dimensi**:
   - **Kepatuhan Instruksi (Instruction Following)**: Menguji kepatuhan format ketat (JSON murni tanpa markdown) dan batasan negatif.
   - **Penalaran Simbolik & Logika (Reasoning)**: Menguji operasi matematika abstrak baru ($a \diamond b = 2a + 3b - 5$) yang bebas dari bias hafalan dataset pra-latih.
   - **Sintaksis & Debugging Kode**: Melacak kemampuan lokalisasi bug off-by-one pada kode Python dan sintesis perbaikan idiomatik.
   - **Batas Keamanan & Etika**: Memverifikasi penolakan permintaan berbahaya dan respon etis.
   - **Ketahanan Injeksi Prompt (Adversarial Robustness)**: Menguji ketahanan model terhadap pembajakan konteks dokumen tidak langsung.
   - **Konsistensi Identitas & Nonce Probing**: Menyisipkan nonce unik untuk mendeteksi kebingungan vendor (*cross-provider confusion*).
   - **Stabilitas & Determinisme**: Menguji konsistensi deterministik pada `temperature: 0`.

2. **Dukungan Penuh Router ByNara (`https://router.bynara.id`)**:
   - Normalisasi cerdas Base URL (menangani awalan/akhiran `/v1` ganda atau hilang secara transparan).
   - Dukungan transmisi Server-Sent Events (SSE) dengan **Reasoning Deltas** (misal: token penalaran `delta.reasoning_content` pada `gpt-5.6-luna`).
   - Mode streaming dijadikan standar utama untuk performa responsif dan bebas timeout.

3. **Antarmuka Web Modern (Full Bahasa Indonesia, Tanpa Login)**:
   - Akses langsung tanpa hambatan login atau OAuth.
   - Bilah **Template Cepat (Quick Presets)**: 1-klik untuk Router ByNara (`gpt-5.6-luna`), OpenAI (`gpt-4o`), Anthropic (`claude-3-5-sonnet`), dan Mode Simulasi Cepat.
   - Desain presisi non-pill (`rounded-lg` 6-8px, tinggi compact 36-38px, feedback klik aktif `active:scale-[0.98]`).
   - Dukungan aksesibilitas tinggi (WCAG AA), navigasi keyboard penuh, dan ekspor laporan ke PDF resmi.

4. **Siap Deploy Serverless di Vercel**:
   - Struktur monorepo modern yang terintegrasi langsung dengan Vercel.
   - Frontend Vite/React di `apps/web` dan Backend Serverless Functions di `api/index.py`.

---

## 📚 Dokumentasi Lengkap

- [Metodologi Pengujian Model AI](docs/METODOLOGI_PENGUJIAN_MODEL_AI.md): Penjelasan komprehensif 8 dimensi probe dan deteksi downgrade model.
- [Panduan Pengujian Router ByNara](docs/PANDUAN_PENGUJIAN_ROUTER_BYNARA.md): Tutorial pengujian gateway Router ByNara dan model penalaran `gpt-5.6-luna`.
- [Panduan Deployment Vercel Serverless](docs/PANDUAN_DEPLOYMENT_VERCEL_SERVERLESS.md): Langkah deployment serverless ke Vercel tanpa biaya server VPS.

---

## 🛠️ Instalasi & Pengembangan Lokal

### Prasyarat
- Python 3.11+
- Node.js 18+ dan npm

### 1. Menjalankan Backend Python
```bash
# Clone repository
git clone https://github.com/dresar/model-verifier.git
cd model-verifier

# Buat virtual environment & install dependensi
python -m venv .venv
.\.venv\Scripts\activate   # Pada Windows
# source .venv/bin/activate  # Pada Linux/macOS

pip install -e '.[test]'

# Jalankan test suite
pytest -q
```

### 2. Menjalankan Server API Lokal
```bash
model-verifier-demo --host 127.0.0.1 --port 7860
```

### 3. Menjalankan Frontend Web UI
Buka terminal baru:
```bash
cd apps/web
npm install
npm run dev
```
Buka browser di alamat yang ditampilkan oleh Vite (misalnya `http://127.0.0.1:5173/`).

---

## 💻 Penggunaan via CLI

Anda dapat menjalankan verifikasi gateway langsung dari command line:

```bash
model-verifier \
  --base-url https://router.bynara.id \
  --api-key "sk-kunci-anda" \
  --model gpt-5.6-luna \
  --claimed-model gpt-5.6-luna
```

---

## 🐍 Penggunaan sebagai Library Python

```python
from model_verifier.report import run_verification
from model_verifier.types import VerificationOptions, VerificationTarget

target = VerificationTarget(
    source="temporary",
    base_url="https://router.bynara.id",
    model="gpt-5.6-luna",
    api_key="sk-...",
    api_key_masked="sk-...****",
    site_name="Router ByNara",
)

options = VerificationOptions(
    claimed_model="gpt-5.6-luna",
    provider_mode="auto",
    timeout_seconds=90,
)

laporan = run_verification(target, options)
print(f"Status: {laporan['verdict']}")
print(f"Skor Integritas: {laporan['identity_score']}/100")
print(f"Tingkat Risiko: {laporan['risk_level']}")
```

---

## ☁️ Deployment ke Vercel

Proyek ini telah dilengkapi konfigurasi `vercel.json` dan entrypoint `api/index.py`. Untuk mendistribusikan ke Vercel:

```bash
# Menggunakan Vercel CLI
vercel --prod
```

Atau cukup hubungkan repositori GitHub `dresar/model-verifier` ke dashboard Vercel Anda untuk deployment otomatis (CI/CD).

---

## ⚖️ Lisensi & Hak Cipta

- Kode Sumber: Dilisensikan di bawah lisensi terbuka **GNU AGPLv3 (AGPL-3.0-or-later)**.
- Hak Cipta &copy; 2026 **Eka Syarif Maulana** (`eka.ckp16799@gmail.com`).
