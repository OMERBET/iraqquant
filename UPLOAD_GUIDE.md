# دليل رفع الملفات على GitHub

## الهيكل النهائي للمشروع

```
iraqquant/                          ← المجلد الرئيسي (repo root)
├── .gitignore
├── .gitattributes
├── .env.example
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── UPLOAD_GUIDE.md
├── Dockerfile
├── docker-compose.yml
├── vercel.json
├── runtime.txt
│
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── config.py
│       ├── main.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── mps_engine.py       ← FIXED
│       │   └── gates.py
│       ├── noise/
│       │   ├── __init__.py
│       │   ├── pauli_noise.py
│       │   └── burst_events.py
│       ├── qec/
│       │   ├── __init__.py
│       │   └── surface_code.py
│       ├── topology/
│       │   ├── __init__.py
│       │   └── manager.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py
│       │   └── job.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   └── jobs.py             ← FIXED
│       └── workers/
│           ├── __init__.py
│           └── tasks.py            ← FIXED
│
└── frontend/
    ├── index.html                  ← UPDATED
    ├── css/
    │   └── style.css               ← UPDATED
    └── js/
        ├── auth.js                 ← NEW
        ├── circuit.js              ← NEW
        └── app.js                  ← NEW
```

## خطوات الرفع على GitHub

1. أنشئ repo جديد على github.com باسم `iraqquant`
2. في جهازك:
```bash
git init
git add .
git commit -m "Initial release: IraqQuant v1.0.0"
git branch -M main
git remote add origin https://github.com/USERNAME/iraqquant.git
git push -u origin main
```

## تشغيل محلي

```bash
cd backend
pip install -r requirements.txt
python -m app.main
# افتح: http://localhost:5000
```

## تشغيل بـ Docker

```bash
docker-compose up -d
# افتح: http://localhost:5000
```
