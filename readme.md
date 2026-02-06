# Reelsmith v2

Reelsmith v2 is an automated tool to bulk-generate vertical short videos (9:16) from trending Reddit posts. It uses a single Linux Docker container, Python scripts, FFmpeg, and Google Gemini (LLM + TTS).

## Features

- **Harvest**: Fetches trending posts from configured Subreddits.
- **Score**: Calculates a virality score based on upvotes, comments, and age.
- **Extract**: Sanitizes text and extracts canonical data (OP + top comments).
- **Moderate**: Uses Gemini to flag inappropriate content.
- **Script Gen**: Uses Gemini to generate a video script with tone, pacing, and visual suggestions.
- **TTS**: Uses Gemini or ElevenLabs to generate audio narration (selectable via env).
- **Subtitles**: Generates subtitles aligned to audio duration with verification checks.
- **B-roll**: Optional background montage from an explicit, licensed registry.
- **Render**: Uses Pillow and FFmpeg to generate video cards, motion, transitions, and burn-in subtitles.
- **UI**: Simple local dashboard to view outputs and manage flagged items.
- **Orchestration**: Automated pipeline runner.
- **Validation**: Per-video JSON report with audio/subtitle/montage durations.

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
    # Single key
    GEMINI_API_KEY=your_gemini_key
    
    # OR List of keys for rotation
    GEMINI_API_KEYS=["key1", "key2", "key3"]

    # Optional: override the TTS model used for Gemini audio generation
    GEMINI_TTS_MODEL=gemini-2.5-flash-preview-tts

    # TTS provider selection: gemini or elevenlabs
    TTS_PROVIDER=gemini

    # ElevenLabs (only required if TTS_PROVIDER=elevenlabs)
    ELEVENLABS_API_KEY=your_elevenlabs_key
    ELEVENLABS_VOICE_ID=your_voice_id
    # Optional overrides
    ELEVENLABS_MODEL_ID=eleven_multilingual_v2
    ELEVENLABS_OUTPUT_FORMAT=pcm_24000
    # Optional JSON for voice settings (e.g. {"stability":0.5,"similarity_boost":0.8})
    # ELEVENLABS_VOICE_SETTINGS_JSON={"stability":0.5,"similarity_boost":0.8}

    # Subtitle limits (seconds)
    MAX_SCRIPT_DURATION_SECONDS=120

    # B-roll registry + allowlist (comma-separated domains)
    MEDIA_REGISTRY_PATH=data/media_registry.json
    BROLL_ALLOWLIST=example.com,cdn.example.com
    
    REDDIT_CLIENT_ID=your_reddit_client_id
    REDDIT_CLIENT_SECRET=your_reddit_client_secret
    REDDIT_USER_AGENT=reelsmith:v2 (by /u/yourname)
    ```

3.  **Run with Docker Compose**:
    ```bash
    docker-compose up -d
    ```
    This will start both the worker and the UI in the background.

## Usage

### Dashboard
Visit `http://localhost:8000` in your browser to view outputs and manage flagged items.

### Logs
To view logs for the worker (where the pipeline runs):
```bash
docker-compose logs -f worker
```

To view logs for the UI:
```bash
docker-compose logs -f ui
```

### Stopping
```bash
docker-compose down
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

# Subtitles (optional manual run)
docker run --rm -v $(pwd)/workspace:/workspace --env-file .env reelsmith:v2 python app/subtitles.py

# Fixtures-based pipeline test mode
docker run --rm -v $(pwd)/workspace:/workspace --env-file .env reelsmith:v2 python app/pipeline_test.py
```

### Media Registry Format
`data/media_registry.json` must be a JSON list. Each entry must include explicit license metadata:
```json
[
  {
    "id": "clip-001",
    "source": "https://example.com/license-page",
    "source_url": "https://cdn.example.com/clip-001.mp4",
    "license": "CC-BY-4.0",
    "attribution": "Example Creator",
    "allowed_edits": true,
    "motion_score": 0.7,
    "tone_tags": ["funny", "energetic"],
    "duration_seconds": 12
  }
]
```
Only sources whose domain appears in `BROLL_ALLOWLIST` are eligible.

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
- `data/media_registry.json`: Licensed background clip registry.

## License
AGPL v3
