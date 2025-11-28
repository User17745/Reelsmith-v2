# Reelsmith v2

**Reelsmith v2** is a single-container, Python-first automation tool that generates **vertical short-form videos** (Reels / TikToks / Shorts) from **trending Reddit posts** — end-to-end.

It handles:
- Content harvesting  
- Trend scoring  
- Moderation  
- Script writing  
- Voiceover (TTS)  
- Video rendering  
- Local preview + flagged content queue

All inside one Docker image, with **zero paid tools**, using **Google Gemini free tier** for all LLM & TTS tasks.

---

# ✨ Features

| Feature | Description |
|--------|-------------|
| **Fully automated pipeline** | Harvest → Score → Extract → Moderate → Script → TTS → Render |
| **Single Docker container** | No external services, no cloud infra, no Redis/Kafka |
| **Gemini-powered generation** | Script writing, tone/pacing/CTA selection, moderation, & TTS |
| **1080×1920 vertical videos** | FFmpeg-rendered with caption cards & voiceover |
| **Local storage** | Everything stored in `/workspace/` & SQLite — portable and private |
| **Strong moderation** | Gemini-based safety classification + flagged folder |
| **Simple UI (optional)** | FastAPI local server to preview outputs & flagged items |
| **API key rotation** | Multiple Gemini API keys supported to avoid rate limits |

---

# 🧱 Architecture Overview

```
Reddit API  →  harvest.py
                ↓
            score.py
                ↓
           extract.py
                ↓
       moderate.py (Gemini)
                ↓  (FLAG → flagged/)
   script_gen.py (Gemini)
                ↓
      tts_gen.py (Gemini TTS)
                ↓
         render.py (FFmpeg)
                ↓
       output/*.mp4 ready!
```

Everything runs locally.  
Gemini is the only external service.

---

# 📦 Project Structure

```
Reelsmith-v2/
│
├── app/
│   ├── harvest.py
│   ├── score.py
│   ├── extract.py
│   ├── moderate.py
│   ├── script_gen.py
│   ├── tts_gen.py
│   ├── render.py
│   ├── genai_client.py
│   ├── db.py
│   └── utils.py
│
├── workspace/
│   ├── raw/
│   ├── canonical/
│   ├── scripts/
│   ├── output/
│   └── flagged/
│
├── prompts/
│   ├── moderation_prompt.txt
│   └── script_prompt.txt
│
├── data/
│   └── app.db
│
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md  ← (this file)
```

---

# 🔧 Technologies Used

| Category | Technology |
|----------|------------|
| Language | Python 3.11+ |
| Video | FFmpeg |
| LLM / TTS | **Google Gemini** via `google-genai` SDK |
| Storage | SQLite + local filesystem |
| UI | FastAPI (optional) |
| Image work | Pillow |
| Reddit | PRAW |
| Container | Docker |

---

# 🔑 Required Credentials

You need:

## 1. Gemini API Key(s)
Used for:
- Script generation  
- Moderation  
- TTS (Audio Gen API)

Set in environment:

```env
GEMINI_API_KEYS_FILE=/secrets/keys.json
```

`keys.json` format:

```json
{ "gemini_keys": ["KEY1", "KEY2"] }
```

---

## 2. Reddit API Credentials
Create a “personal use script” in Reddit developer settings.

Add to `.env`:

```env
REDDIT_CLIENT_ID=xxxx
REDDIT_CLIENT_SECRET=yyyy
REDDIT_USER_AGENT=reelsmith-v2 (by /u/yourname)
```

---

# ⚙️ Configuration

Copy `.env.example` → `.env` and fill credentials.

Example `.env`:

```env
GEMINI_API_KEYS_FILE=/secrets/keys.json
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=reelsmith-v2
WORKSPACE_DIR=/workspace
DB_PATH=/data/app.db
```

---

# 🐳 Running via Docker

Build the image:

```bash
docker build -t reelsmith-v2 .
```

Run the container:

```bash
docker run --rm -it \
  -v $(pwd)/workspace:/workspace \
  -v $(pwd)/secrets:/secrets \
  --env-file .env \
  reelsmith-v2 /bin/bash
```

---

# 🚀 Running the Full Pipeline

Inside the container:

```bash
python app/harvest.py
python app/score.py
python app/extract.py
python app/moderate.py
python app/script_gen.py
python app/tts_gen.py
python app/render.py
```

Or create a combined runner:

```bash
python app/run_pipeline.py
```

---

# 🧪 Outputs

After a successful run:

```
workspace/
│
├── output/
│   └── <post_id>.mp4      ← FINAL VIDEO
│
├── scripts/
│   └── <post_id>.json     ← Script + tone/pacing/CTA chosen by Gemini
│
├── flagged/
│   └── <post_id>.json     ← Unsafe content to review manually
```

---

# 🧠 How Gemini Is Used in Reelsmith v2

| Task | Gemini Model |
|------|--------------|
| Moderation | Gemini (classification) |
| Script writing | Gemini (creative generation) |
| Automatic tone/pacing/CTA | Gemini (style reasoning) |
| TTS | Gemini Audio Generation |

This keeps your stack **ultra-lean** and eliminates local ML weights.

---

# 📝 Moderation Behavior

1. Reelsmith v2 sends Reddit content to Gemini with platform rules.
2. Gemini returns:

```json
{ "flag": true/false, "reasons": ["..."] }
```

3. If flagged → saved to `workspace/flagged/` and **skipped**.

---

# 🎬 Rendering Details

- All videos are 1080×1920 vertical MP4.
- Scenes are rendered using:
  - Pillow → PNG cards
  - FFmpeg → merging PNGs + TTS audio
  - Optional SRT caption overlay

Example:

```bash
ffmpeg -f concat -safe 0 -i scenes.txt \
       -i voiceover.wav \
       -c:v libx264 -vf "format=yuv420p" \
       -c:a aac -shortest output.mp4
```

---

# 🧹 Cleanup & Retention

Old content can be purged:

```bash
python app/cleanup.py --days 7
```

---

# 📈 Roadmap

| Priority | Feature |
|---------|---------|
| Medium | Auto-publishing to TikTok/IG/YT |
| Medium | Multiple rendering styles |
| Low | Analytics feedback loop |
| Low | Voice cloning |

---

# ⚠️ Disclaimers

- Reddit posts may contain copyrighted images — review required.
- Gemini free tier has usage limits — enable key rotation.
- Output quality depends on input content & moderation strictness.

---

# 🧭 License

This project is fully yours — use, modify, and distribute freely.

---

# 🤝 Contributing

PRs welcome. Ensure:
- No API keys in commits  
- Modular, clean code  
- PEP8 formatting

---

# 📞 Support

For issues: open a ticket in the repo.
For implementation help: use ChatGPT to generate or debug modules.