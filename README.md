# 🔗 URL Shortener API  
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey?logo=flask)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Stable-success)

A minimalist **Flask + SQLite** API that converts long URLs into short, trackable links.  
Includes analytics (`click_count`, `last_accessed`), validation, and duplicate detection.

---

## 🚀 Key Features
- ✨ Shorten long URLs instantly  
- 🔁 Redirect via `/short_id`  
- 🧠 Detect duplicate URLs automatically  
- ✅ Validate `http/https` URLs  
- 📊 Track clicks & last access time  
- ⚙️ Configurable `.env` (SQLite / PostgreSQL / MySQL)  
- 🌐 Minimal HTML form for quick browser testing  

---

## 🧩 Tech Stack
| Layer | Technology |
|-------|-------------|
| Backend | Flask 3.x |
| Database | SQLite (default) |
| ORM | SQLAlchemy |
| Config | python-dotenv |
| Language | Python 3.12 |

---

## ⚙️ Quick Setup

### 🔹 1. Clone & Create Virtual Environment
```bash
git clone https://github.com/<yourusername>/url-shortener-api.git
cd url-shortener-api

# Windows
py -m venv .venv && .\.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv && source .venv/bin/activate
```

### 🔹 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 🔹 3. Configure Environment
```bash
cp .env.example .env
```

Edit `.env`:
```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///urls.db
```

### 🔹 4. Run the App
```bash
py main.py
```

Open: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🧪 API Usage

### ➕ Create a Short Link
```bash
curl -X POST http://127.0.0.1:5000/shorten      -H "Content-Type: application/json"      -d '{"url":"https://example.com"}'
```

**Response**
```json
{
  "short_id": "Ab3xYz",
  "short_url": "http://127.0.0.1:5000/Ab3xYz",
  "original_url": "https://example.com"
}
```

### 🔁 Redirect
```
GET http://127.0.0.1:5000/Ab3xYz
```

### 📊 Analytics
```
GET http://127.0.0.1:5000/stats/Ab3xYz
```

---

## 🚀 Deploy on Render or Railway

### 🔸 Render
1. Push repo to GitHub  
2. Go to [Render.com](https://render.com) → “New Web Service”  
3. Select repo →  
   - **Build Command:** `pip install -r requirements.txt`  
   - **Start Command:** `python main.py`

### 🔸 Railway
1. Import GitHub repo  
2. Add environment variables  
3. Deploy with 1 click 🚀

---

## 🧾 Example Commit
```bash
git add .
git commit -m "feat(api): add shorten, redirect, and analytics tracking"
```

---

## 👩‍💻 Author

**Priyanka Jawalkar**  
Master’s in Computer Science  
[GitHub](https://github.com/PriyaJ31)

---


