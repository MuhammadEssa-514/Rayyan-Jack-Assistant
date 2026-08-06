# 🤖 Jack AI — Personal Voice Assistant

Jack AI ek offline-first, multilingual personal AI assistant hai jo Urdu, English, aur Roman Urdu mein kaam karta hai. Yeh aapke Windows laptop aur Android phone ko voice commands se control karta hai.

---

## 📦 Project Structure

```
Personal Assistant/
├── server/           # Node.js Core Server (Express + Socket.IO + MongoDB)
├── voice-engine/     # Python Voice Service (Whisper + OpenWakeWord + Piper)
├── windows-agent/    # Python Windows Automation (PyAutoGUI + Playwright)
├── android-app/      # React Native Android Companion App
└── dashboard/        # Next.js Web Dashboard
```

---

## ⚡ Quick Start

### 1. Prerequisites

| Tool | Version | Download |
|------|---------|---------|
| Node.js | 20+ | https://nodejs.org |
| Python | 3.10+ | https://python.org |
| MongoDB | 7+ | https://mongodb.com/try/download/community |
| Ollama | Latest | https://ollama.com |
| Git | Latest | https://git-scm.com |

### 2. Pull Ollama Model

```bash
ollama pull qwen2.5:7b
```

### 3. Start Core Server

```bash
cd server
npm install
cp .env.example .env
npm run dev
```

### 4. Start Voice Engine

```bash
cd voice-engine
pip install -r requirements.txt
python main.py
```

### 5. Start Windows Agent

```bash
cd windows-agent
pip install -r requirements.txt
python main.py
```

### 6. Start Dashboard

```bash
cd dashboard
npm install
npm run dev
# Open http://localhost:3000
```

---

## 🗣️ Voice Commands (Urdu Examples)

| Command | Urdu | Action |
|---------|------|--------|
| Open App | "Jack, Chrome kholo" | Launches Chrome |
| WhatsApp | "Jack, Ali ko message bhejo: main aa raha hoon" | Sends WhatsApp message |
| Search | "Jack, YouTube par songs chalao" | Opens YouTube |
| Volume | "Jack, volume badha do" | Increases volume |
| Screenshot | "Jack, screenshot lo" | Takes screenshot |
| Shutdown | "Jack, computer band karo" | Shuts down PC |

---

## 🧠 AI Brain — JSON Format

Every voice command is converted to this structure:

```json
{
  "intent": "send_whatsapp_message",
  "target": "android",
  "confidence": 0.95,
  "parameters": {
    "contact": "Ali",
    "message": "Main aa raha hoon"
  },
  "response_text": "Ali ko message bhej diya"
}
```

---

## 🗺️ Milestones

- [x] **M1** — Voice Pipeline + Dashboard (Current)
- [ ] **M2** — Windows Automation (Full)
- [ ] **M3** — Android Companion App
- [ ] **M4** — Memory System + Advanced Dashboard
- [ ] **M5** — Computer Vision + Advanced AI

---

## 📜 License

Personal use only. All rights reserved.
