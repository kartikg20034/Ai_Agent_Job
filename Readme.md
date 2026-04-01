# 🤖 AI Job Agent

An automated job discovery system that scans multiple platforms, ranks jobs using AI based on your resume, and sends top matches directly to WhatsApp.

---

## 🚀 Features

* 🔍 Multi-platform job scraping (7+ sources)
* 🧠 AI-powered job matching (semantic similarity)
* 🚀 Startup-focused job discovery
* 📱 WhatsApp notifications (via Twilio)
* ☁️ Runs automatically using GitHub Actions
* 🔄 Fault-tolerant (skips failed websites)

---

## 🌐 Supported Platforms

* Wellfound
* Indeed
* Remotive
* Remote OK
* YC Jobs
* Hirist

---

## 📁 Project Structure

```
job-agent-ai/
│
├── cloud_main.py          # Main pipeline (cloud)
├── config.py              # Configuration
├── ai_utils.py            # AI logic (resume matching)
│
├── scrapers/              # Website scrapers
│   ├── wellfound.py
│   ├── indeed.py
│   ├── hirist.py
│   ├── remotive.py
│   ├── remoteok.py
│   └── yc_jobs.py
│
├── data/
│   └── resume.pdf         # YOUR resume
│
├── .env                   # 🔐 Secrets (not committed)
├── requirements.txt
└── .github/workflows/     # GitHub Actions
```

---

## ⚙️ Setup (Local)

### 1️⃣ Clone the repo

```
git clone https://github.com/your-username/job-agent-ai.git
cd job-agent-ai
```

---

### 2️⃣ Install dependencies

```
pip install -r requirements.txt
playwright install chromium
```

---

### 3️⃣ Add your resume

Place your resume here:

```
data/resume.pdf
```

---

### 4️⃣ Create `.env` file

Create a file named `.env` in the root directory:

```
OPENAI_API_KEY=your_openrouter_key

TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_FROM=whatsapp:+14155238886
TWILIO_TO=whatsapp:+91XXXXXXXXXX
```

---

## 🔐 Required Credentials

### 🧠 OpenAI / OpenRouter

Used for AI job matching
Get API key and add to `.env`

---

### 📱 WhatsApp (Twilio)

Used to send job alerts

Steps:

1. Create Twilio account
2. Enable WhatsApp sandbox
3. Join sandbox from your phone
4. Add credentials to `.env`

---

## ▶️ Run Locally

```
python cloud_main.py
```

### Output:

* 📄 `data/jobs.csv` → Top job matches
* 📱 WhatsApp message → Top jobs

---

## ☁️ Run Automatically (GitHub Actions)

### Setup:

1. Push code to GitHub

2. Go to:

   ```
   Repo → Settings → Secrets → Actions
   ```

3. Add:

```
OPENAI_API_KEY
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_FROM
TWILIO_TO
```

---

### Workflow Features

* 🟢 Manual trigger (Run anytime)
* 🟣 Automatic daily run (12 AM IST)

---

## ⚙️ Customization

### 🔧 Change job roles

Edit in `config.py`:

```
KEYWORDS = ["Python Developer", "AI Engineer", "Backend Developer"]
```

---

### 📍 Change locations

```
LOCATIONS = ["Remote", "Bangalore", "Hyderabad"]
```

---

### 📊 Change number of jobs

In `cloud_main.py`:

```
top_jobs = df.head(50)
```

---

## ⚠️ Notes

* Some sites may fail → agent skips automatically
* WhatsApp messages are limited in length
* Best results for tech/startup roles

---

## 🔥 Future Improvements

* 🧠 “Why this job matches you” explanation
* 📊 Web dashboard
* 🤖 Auto-apply to top jobs
* 📩 Telegram/Email notifications

---

## 🛡️ Security

* `.env` is ignored (no secrets in repo)
* No passwords stored
* Safe for public GitHub

---

## 👨‍💻 Author

Built as an AI-powered job automation system to streamline job search.

---

## ⭐ If you like this project

Give it a star ⭐ on GitHub!
