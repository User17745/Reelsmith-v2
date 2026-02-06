# Reelsmith v2 Roadmap

This roadmap assumes the project is at POC stage. The goal is to reach a stable MVP with reliable TTS, aligned subtitles, and ethical background media. Each sprint is sized for a small team (1–2 engineers) and includes test case definitions.

Sprint codes should be used for branching and versioning (for example, `feature/RS-S1-tts-provider`, `release/RS-S3-broll`). All test suites (unit and e2e), including existing ones, must pass before a sprint is considered complete.

## Sprint 1 (RS-S1): Baseline Stability + Configurable TTS (1–2 weeks)

Goals:
1. Make the pipeline deterministic and debuggable.
2. Ensure TTS providers can be switched via env.
3. Establish testing baselines for audio and render.

Features:
1. TTS provider selection via env (Gemini and ElevenLabs).
2. Centralized config validation with clear error messages.
3. Structured logging for each pipeline step (harvest, extract, script, tts, render).
4. Basic output artifact checks (audio file exists, video file exists).

Test cases:
1. `TTS_PROVIDER=gemini` produces a WAV with expected sample rate (24kHz).
2. `TTS_PROVIDER=elevenlabs` produces a WAV with expected sample rate (from env).
3. Missing required env variables fail fast with clear errors.
4. Render step fails gracefully if audio is missing.

## Sprint 2 (RS-S2): Subtitle Sync + Timing Integrity (1–2 weeks)

Goals:
1. Subtitles match spoken audio timing.
2. Timing issues are detectable and testable.

Features:
1. Generate subtitles based on actual audio length.
2. Align subtitle segments with TTS timing (word-level or sentence-level).
3. Add a subtitle timing verification step.

Test cases:
1. Subtitle duration equals audio duration within a small tolerance (e.g., 200 ms).
2. Segment timestamps are strictly increasing and non-overlapping.
3. Rendered video shows last subtitle before audio ends (no trailing silence mismatch).
4. Pipeline flags scripts that exceed a max duration (configurable threshold).

## Sprint 3 (RS-S3): Ethical Background B-Roll MVP (2 weeks)

Goals:
1. Add background videos to improve retention.
2. Ensure licensing is explicit and auditable.

Features:
1. Media registry with license metadata (source, attribution, allowed edits).
2. Download and cache approved background clips.
3. Simple montage generator: select, trim, and loop background clips to match audio length.

Test cases:
1. Only clips from the registry are used.
2. Missing license metadata fails the pipeline.
3. Montage duration matches audio length (within tolerance).
4. Backgrounds render behind text cards without visual overlap bugs.

## Sprint 4 (RS-S4): Visual Quality + Motion (2 weeks)

Goals:
1. Improve visual appeal and pacing.
2. Make output less static and more engaging.

Features:
1. Add subtle motion (zoom/pan) to cards.
2. Scene transitions (fade or cut) synchronized with narration.
3. Optional overlay styling for readability (blur, gradient, or vignette).

Test cases:
1. Transitions occur at scene boundaries.
2. Zoom/pan stays within frame bounds (no black edges).
3. Subtitles remain readable against backgrounds (contrast check).

## Sprint 5 (RS-S5): Selection Intelligence + Content Safety (2 weeks)

Goals:
1. Improve background selection relevance.
2. Strengthen content safety.

Features:
1. Background selection heuristics (motion score, tone tags, duration).
2. Content safety checks for background sources (manual allowlist).
3. Add pipeline metrics (duration, sync, render time) for observability.

Test cases:
1. Clips with low motion score are deprioritized.
2. Allowlist enforcement blocks unapproved domains.
3. Metrics emitted for each pipeline run with consistent schema.

## Sprint 6 (RS-S6): MVP Hardening (1–2 weeks)

Goals:
1. Reduce edge-case failures.
2. Prepare for internal beta usage.

Features:
1. Robust retry/backoff for TTS and external APIs.
2. End-to-end pipeline test mode using fixed fixtures.
3. Output validation report per video (JSON summary).

Test cases:
1. Retry logic triggers on transient failures and succeeds on recovery.
2. E2E pipeline test produces consistent outputs from fixtures.
3. Validation report includes audio duration, subtitle duration, and montage duration.

## Notes

1. Sprint durations are estimates and can be adjusted based on team size.
2. Each sprint should end with a demo video and a short release note.
3. If only one sprint can be delivered first, Sprint 2 (subtitle sync) yields the biggest perceived quality gain.
