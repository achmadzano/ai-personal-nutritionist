# AI Personal Nutritionist

AI Personal Nutritionist adalah aplikasi berbasis AI yang membantu kamu memantau asupan makanan harian, menghitung kalori, protein, dan memberikan saran nutrisi berdasarkan foto makanan serta profil tubuh (berat, tinggi, target berat, BMI, dsb).

## Fitur

- 🔐 **Authentication**: Register, login, dan logout dengan MongoDB
- 📸 **Upload Foto**: Upload foto makanan (JPG, JPEG, PNG)
- 🤖 **AI Analysis**: Deteksi kalori, protein, dan nutrisi dengan **SambaNova Cloud AI** (Llama-4 Maverick)
- 🍽️ **Kategori Makan**: Tandai makanan sebagai sarapan, makan siang, atau makan malam
- 📊 **Evaluasi Harian**: Lihat total kalori & protein harian, saran sesuai BMI & target
- 📝 **Riwayat**: Simpan & lihat riwayat analisis makanan
- 👤 **Profil Tubuh**: Input & update tinggi, berat, target, usia, gender, aktivitas
- 💡 **Saran Nutrisi**: Saran otomatis berdasarkan status tubuh dan asupan
- 📱 **Responsive UI**: Interface user-friendly dengan Streamlit

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **AI/ML**: SambaNova Cloud AI (Llama-4 Maverick-17B-128E-Instruct)
- **Framework**: LangChain
- **Database**: MongoDB
- **Visualization**: Plotly

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup MongoDB

Pastikan MongoDB berjalan di localhost:27017 atau update `MONGODB_URI` di file `.env`

### 3. Setup SambaNova Cloud AI

1. Daftar di SambaNova Cloud (atau IBM WatsonX jika via integrasi)
2. Dapatkan API Key dan Project ID
3. Update file `.env` dengan credentials Anda:

```env
SAMBANOVA_API_KEY=your_sambanova_api_key_here
```

### 4. Jalankan Aplikasi

```bash
streamlit run app.py
```

## Struktur Proyek

```
ai-personal-nutritionist/
├── app.py              # Main Streamlit application
├── ai_analyzer.py      # AI analysis using LangChain + SambaNova
├── database.py         # MongoDB operations
├── requirements.txt    # Python dependencies
├── .env                # Environment variables
└── README.md           # Project documentation
```

## Penggunaan

1. **Register/Login**: Buat akun baru atau login
2. **Profil**: Lengkapi data tubuh (tinggi, berat, target, usia, gender, aktivitas)
3. **Upload Foto**: Pilih foto makanan, pilih jenis makan (sarapan/siang/malam)
4. **Analisis & Simpan**: Dapatkan deteksi makanan, kalori, protein, saran nutrisi
5. **Beranda**: Lihat evaluasi harian (kalori, protein, status BMI, saran)
6. **Riwayat**: Lihat semua analisis yang pernah dilakukan

## Cara Kerja Perhitungan

- **Kalori**: Dihitung otomatis dari AI SambaNova, kebutuhan harian berdasarkan BMR (Mifflin-St Jeor) + aktivitas + target berat
- **Protein**: Target harian = 1.2g x berat badan (kg)
- **Saran**: Disesuaikan status BMI, asupan, dan tujuan berat badan

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SAMBANOVA_APIKEY` | API key untuk SambaNova AI |
| `SAMBANOVA_PROJECT_ID` | Project ID SambaNova AI |
| `SAMBANOVA_URL` | URL endpoint SambaNova AI |
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DB_NAME` | Nama database MongoDB |
| `SECRET_KEY` | Secret key untuk JWT |
| `MODEL_NAME` | Model name (llama-4-maverick-17b-128e-instruct) |

## Troubleshooting

- **Auth Error**: Pastikan API Key & Project ID SambaNova AI benar
- **Database Error**: Pastikan MongoDB aktif & string koneksi benar
- **Upload Error**: Pastikan file JPG/JPEG/PNG & ukuran tidak terlalu besar

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT License