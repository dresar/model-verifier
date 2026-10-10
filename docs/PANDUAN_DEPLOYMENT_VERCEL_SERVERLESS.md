# Panduan Deployment Serverless ke Vercel

Dokumen Resmi Panduan Deployment Vercel
Pemilik & Arsitek Sistem: **Eka Syarif Maulana** (`eka.ckp16799@gmail.com`)

---

## 1. Arsitektur Serverless di Vercel

Model Verifier AI telah dikonfigurasi penuh untuk berjalan secara serverless di infrastruktur cloud Vercel:

1. **Frontend Web UI**: Dibangun menggunakan React 19, TypeScript, dan Vite yang dikompilasi menjadi aset statis performa tinggi di `apps/web/dist`.
2. **Backend Serverless Functions**: Menggunakan runtime Python Vercel di `api/index.py` yang melayani semua permintaan `/api/*` secara on-demand tanpa memerlukan VPS atau container Docker yang berjalan terus menerus.
3. **Konfigurasi `vercel.json`**:
   - Memetakan rute `/api/(.*)` ke fungsi serverless `api/index.py`.
   - Mengalihkan rute frontend ke `index.html` (SPA fallback).
   - Menjalankan build otomatis via `npm run build` yang memicu kompilasi Vite.

---

## 2. Struktur File Konfigurasi Vercel

Proyek ini telah dilengkapi dengan berkas-berkas pendukung Vercel:

- `vercel.json`: Konfigurasi build dan routing.
- `package.json` (root): Berisi script `"build": "npm --prefix apps/web run build"`.
- `requirements.txt` (root): Dependensi Python untuk runtime serverless Vercel (`httpx>=0.27.0`).
- `api/index.py`: Entrypoint WSGI dan BaseHTTPRequestHandler untuk menangani request API.

---

## 3. Langkah Deployment via Vercel CLI

Jika Anda memiliki Vercel CLI terpasang di komputer:

```bash
# 1. Pastikan Anda berada di direktori project
cd model-verifier

# 2. Login ke akun Vercel Anda (jika belum)
vercel login

# 3. Jalankan deployment
vercel --prod
```

Vercel akan secara otomatis:
- Mengunduh dependensi Node.js di `apps/web`.
- Mengompilasi TypeScript dan Vite bundle.
- Memasang dependensi Python dari `requirements.txt`.
- Mempublikasikan website ke domain Vercel Anda (contoh: `https://model-verifier.vercel.app`).

---

## 4. Langkah Deployment via GitHub Integration

1. Buat repositori baru di GitHub akun Anda (`dresar/model-verifier`).
2. Push source code proyek ini ke branch `main`.
3. Buka dashboard Vercel (`https://vercel.com/dashboard`).
4. Klik **Add New Project** &rarr; **Import Git Repository**.
5. Pilih repositori `model-verifier`.
6. Vercel akan otomatis mendeteksi konfigurasi `vercel.json` dan `apps/web`.
7. Klik **Deploy**.
8. Dalam waktu kurang dari 2 menit, aplikasi verifikasi model AI Anda siap digunakan di seluruh dunia!

---

## 5. Keuntungan Arsitektur Serverless

- **Zero-Maintenance**: Tidak perlu mengurus patch OS Linux, Nginx, atau Docker.
- **Biaya Hemat (Free Tier Compatible)**: Hanya menggunakan komputasi saat ada pengujian yang berjalan.
- **Skalabilitas Global**: Didistribusikan melalui Vercel Edge Network untuk latensi terendah.
