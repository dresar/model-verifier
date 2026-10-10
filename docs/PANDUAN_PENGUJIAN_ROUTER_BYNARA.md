# Panduan Pengujian & Verifikasi Router ByNara

Dokumen Resmi Pengujian AI Gateway Router ByNara
Pemilik & Arsitek Sistem: **Eka Syarif Maulana** (`eka.ckp16799@gmail.com`)

---

## 1. Mengenal Router ByNara

Router ByNara (`https://router.bynara.id`) adalah gateway model AI modern yang mengagregasikan berbagai model canggih seperti `gpt-5.6-luna`, keluarga GPT-4, Claude, dan model penalaran (*reasoning models*).

Karakteristik penting pada Router ByNara yang ditangani oleh **Model Verifier AI**:
1. **Normalisasi Base URL Otomatis**:
   Sebagian pengguna memasukkan Base URL sebagai `https://router.bynara.id` sementara yang lain memasukkan `https://router.bynara.id/v1` atau `https://router.bynara.id/v1/`.
   Sistem Model Verifier secara otomatis menormalisasi URL sehingga endpoint `/v1/chat/completions` dan `/v1/models` tidak pernah mengalami duplikasi `/v1/v1/`.
2. **Streaming Reasoning Deltas**:
   Model penalaran generasi baru seperti `gpt-5.6-luna` mengirimkan token penalaran internal melalui field `delta.reasoning_content` atau `delta.reasoning` sebelum mengalirkan jawaban akhir pada `delta.content`.
   Model Verifier AI mendukung penangkapan kedua jenis delta ini secara mulus.
3. **Streaming Sebagai Mode Utama**:
   Router ByNara dioptimalkan untuk transmisi streaming berbasis Server-Sent Events (SSE). Pemanggilan model default pada Model Verifier AI menggunakan mode streaming untuk mencegah terjadinya timeout atau pemutusan socket.

---

## 2. Cara Menguji Menggunakan Web Interface

1. Buka antarmuka Model Verifier AI di browser Anda.
2. Pada bilah **Template Cepat**, klik tombol **Router ByNara (gpt-5.6-luna)**.
3. Form akan terisi secara otomatis:
   - **Base URL Gateway**: `https://router.bynara.id`
   - **Protokol**: `OpenAI Kompatibel`
   - **Model Target**: `gpt-5.6-luna`
4. Masukkan Kunci Akses Anda (`sk-...`) pada kolom API Key.
5. (Opsional) Klik tombol **Sinkronkan Daftar Model** untuk memvalidasi kunci dan mengambil seluruh daftar model yang tersedia di Router ByNara.
6. Tekan tombol **Mulai Verifikasi Model**.
7. Amati proses verifikasi real-time:
   - Tahap 1: Validasi koneksi gateway.
   - Tahap 2: Eksekusi probe instruksi, logika matematika, kode, dan keamanan.
   - Tahap 3: Perhitungan skor integritas dan deteksi keaslian model.

---

## 3. Cara Menguji Menggunakan CLI Python

Jalankan perintah verifikasi langsung dari terminal:

```bash
model-verifier \
  --base-url https://router.bynara.id \
  --api-key "sk-kunci-anda" \
  --model gpt-5.6-luna \
  --claimed-model gpt-5.6-luna
```

Hasil verifikasi akan menampilkan ringkasan skor dan status model di terminal:
```text
Model: gpt-5.6-luna
Verdict: verified (Skor Integritas: 96/100)
Tingkat Risiko: low (Risiko Rendah)
Reasoning Deltas: Terdeteksi dan tervalidasi
```

---

## 4. Contoh Pemanggilan cURL dengan Streaming

Untuk memeriksa respon mentah dari Router ByNara secara langsung:

```bash
curl -X POST "https://router.bynara.id/v1/chat/completions" \
  -H "Authorization: Bearer sk-kunci-anda" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.6-luna",
    "messages": [
      {"role": "user", "content": "Jelaskan perbedaan CPU dan GPU dalam 2 kalimat."}
    ],
    "temperature": 0,
    "stream": true,
    "stream_options": {"include_usage": true}
  }'
```

Output SSE akan dialirkan berupa:
```text
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","model":"gpt-5.6-luna","choices":[{"index":0,"delta":{"reasoning_content":"Menganalisis arsitektur pemrosesan..."}}]}
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","model":"gpt-5.6-luna","choices":[{"index":0,"delta":{"content":"CPU dirancang untuk..."}}]}
...
data: [DONE]
```

Model Verifier AI mengagregasikan seluruh chunk tersebut, mengevaluasi latensi time-to-first-token (TTFT), dan mengonfirmasi integritas model.
