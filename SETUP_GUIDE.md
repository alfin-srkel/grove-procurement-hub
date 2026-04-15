# GROVE Procurement Hub — Setup Guide

## 1. Google Sheets Setup

Buat spreadsheet baru di Google Drive, lalu buat 6 sheet/tab berikut dengan header row persis seperti ini:

### Tab: `Vendors`
```
vendor_id | vendor_name | category | subcategory | contact_person | phone | email | address | rating | notes | last_used | status
```

### Tab: `Items`
```
item_id | vendor_id | category | item_name | description | unit | unit_price | min_order | lead_time_days | last_updated | source
```

### Tab: `ProcurementCart`
```
cart_id | created_by | created_at | item_id | vendor_id | item_name | qty | unit_price | subtotal | purpose | status
```

### Tab: `Users`
```
email | name | role | password_hash | salt | created_at
```

### Tab: `SearchLog`
```
search_id | searched_by | query | source | results_count | timestamp
```

**PENTING:** Share spreadsheet ke service account:
`grove-analytics@grove-sales-analytics.iam.gserviceaccount.com` (Editor)

Catat Spreadsheet ID dari URL:
`https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_DISINI/edit`

---

## 2. GitHub Repository

1. Buat repo baru: `grove-procurement-hub`
2. Upload file-file berikut:
   - `app.py`
   - `db.py`
   - `search.py`
   - `requirements.txt`
   - `runtime.txt`
   - `.streamlit/config.toml`

---

## 3. Streamlit Cloud Deployment

1. Buka [share.streamlit.io](https://share.streamlit.io)
2. Deploy dari repo `grove-procurement-hub`
3. Main file: `app.py`
4. Di **App Settings > Secrets**, paste isi dari `secrets_template.toml`
   — Ganti `YOUR_GOOGLE_SHEETS_SPREADSHEET_ID` dengan ID spreadsheet yang sudah dibuat
   — Gunakan credentials service account yang sama dengan Sales Analytics

---

## 4. First Login

1. Buka app yang sudah deploy
2. Akan muncul form **Setup Awal** — buat akun Admin pertama
3. Gunakan email `@srkel.id` atau `@teamup.id`
4. Setelah login, isi data vendor dan item awal via menu **Kelola Vendor** dan **Kelola Item**

---

## 5. Struktur File

```
grove-procurement-hub/
├── .streamlit/
│   └── config.toml          # Theme GROVE
├── app.py                    # Main application (UI + routing)
├── db.py                     # Database layer (Google Sheets + caching)
├── search.py                 # Internet digging (DuckDuckGo)
├── requirements.txt          # Python dependencies
├── runtime.txt               # Python 3.11.0
└── secrets_template.toml     # Template untuk Streamlit secrets
```
