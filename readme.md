# Reelsmith v2

Reelsmith v2 is an automated tool to bulk-generate vertical short videos (9:16) from trending Reddit posts. It uses a single Linux Docker container, Python scripts, FFmpeg, and Google Gemini (LLM + TTS).

## Features

- **Harvest**: Fetches trending posts from configured Subreddits.
- **Score**: Calculates a virality score based on upvotes, comments, and age.
- **Extract**: Sanitizes text and extracts canonical data (OP + top comments).
- **Moderate**: Uses Gemini to flag inappropriate content.
- **Script Gen**: Uses Gemini to generate a video script with tone, pacing, and visual suggestions.
- **TTS**: Uses Gemini to generate audio narration.
- **Render**: Uses Pillow and FFmpeg to generate video cards and stitch them with audio.
- **UI**: Simple local dashboard to view outputs and manage flagged items.
- **Orchestration**: Automated pipeline runner.

## Prerequisites

- **Docker**: Ensure Docker is installed and running.
- **Gemini API Key**: Get an API key from [Google AI Studio](https://aistudio.google.com/).
- **Reddit API Credentials**: Create an app on [Reddit](https://www.reddit.com/prefs/apps) to get a Client ID and Secret.

## Setup

1.  **Clone the repository**:
    ```bash
    git clone <repo_url>
    cd Reelsmith-v2
    ```

2.  **Configure Environment**:
    Copy `.env.example` to `.env` and fill in your credentials.
    ```bash
    cp .env.example .env
    ```
    
    Edit `.env`:
    ```ini
    GEMINI_API_KEY=your_gemini_key
    REDDIT_CLIENT_ID=your_reddit_client_id
    REDDIT_CLIENT_SECRET=your_reddit_client_secret
    REDDIT_USER_AGENT=reelsmith:v2 (by /u/yourname)
    ```

3.  **Build Docker Image**:
    ```bash
    docker build -t reelsmith:v2 .
    ```

## Usage

### Running the Orchestration Worker
The worker runs the full pipeline (Harvest -> Score -> Extract -> Moderate -> Script -> TTS -> Render) every hour.

```bash
docker run -d \
  --name reelsmith-worker \
  -v $(pwd)/workspace:/workspace \
  -v $(pwd)/data:/data \
  --env-file .env \
  reelsmith:v2 python app/worker.py
```

### Running the UI
The UI allows you to view generated videos and manage flagged content.

```bash
docker run -d \
  --name reelsmith-ui \
  -p 8000:8000 \
  -v $(pwd)/workspace:/workspace \
  -v $(pwd)/data:/data \
  --env-file .env \
  reelsmith:v2 uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` in your browser.

### Running Individual Steps (Manual)
You can run individual scripts for debugging or manual processing:

```bash
# Harvest
docker run --rm -v $(pwd)/workspace:/workspace -v $(pwd)/data:/data --env-file .env reelsmith:v2 python app/harvest.py

# Score
docker run --rm -v $(pwd)/data:/data --env-file .env reelsmith:v2 python app/score.py

# Extract
docker run --rm -v $(pwd)/workspace:/workspace --env-file .env reelsmith:v2 python app/extract.py

# Moderate
docker run --rm -v $(pwd)/workspace:/workspace -v $(pwd)/data:/data --env-file .env reelsmith:v2 python app/moderate.py

# Script Gen
docker run --rm -v $(pwd)/workspace:/workspace -v $(pwd)/data:/data --env-file .env reelsmith:v2 python app/script_gen.py

# TTS
docker run --rm -v $(pwd)/workspace:/workspace --env-file .env reelsmith:v2 python app/tts_gen.py

# Render
docker run --rm -v $(pwd)/workspace:/workspace --env-file .env reelsmith:v2 python app/render.py
```

## Development

### Running Tests
```bash
docker run --rm -v $(pwd):/app -e PYTHONPATH=/app reelsmith:v2 pytest
```

### Directory Structure
- `app/`: Source code.
- `tests/`: Unit and integration tests.
- `workspace/`: Data directory (raw, canonical, scripts, output).
- `data/`: SQLite database.

## License
MIT