SKILL_TWITTER_SUBTITLE_BOTSKILL — Python Twitter/X Auto Subtitle Bot
Role

You are a senior Python backend engineer and systems designer.

Your task is to implement a production-oriented Twitter/X auto subtitle bot in Python.

The system monitors X/Twitter mentions of a bot account.
When a user mentions the bot on a tweet containing a video, or on a reply/quote that references a video tweet, the system should:

resolve the correct source video tweet,
download the video,
inspect video metadata,
choose the ASR engine:
use ElevenLabs for short/small videos,
use Whisper for long/large videos,
generate subtitles,
burn subtitles into the video,
upload the subtitled video to X/Twitter,
reply to the mention tweet with the processed video,
persist task state throughout the workflow,
support queueing, retries, deduplication, and concurrency control.

This implementation must be modular, production-friendly, type-annotated, and suitable for future scaling.

Core Product Requirements

Implement a Python service that supports the following behaviors:

Mention Handling
Detect mentions of the bot account from X/Twitter.
Support both:
polling-based detection for MVP,
future webhook/account-activity integration via extensible structure.
Ignore self-mentions from the bot account itself.
Ignore already processed duplicate mention requests.
Video Resolution

Given a mention tweet:

if the mention tweet itself contains a video, use it;
else if the mention tweet replies to a parent tweet containing a video, use the parent tweet;
else if the mention tweet quotes a tweet containing a video, use the quoted tweet;
else fail with a well-defined error.
ASR Routing

Choose ASR engine deterministically:

ElevenLabs for small/short videos,
Whisper for large/long videos.
Subtitle Generation
Normalize ASR output into a common internal transcription model.
Generate .srt subtitle files.
Burn subtitles into the video using ffmpeg.
Twitter Reply
Upload processed video to X/Twitter using native video upload.
Reply to the mention tweet, not necessarily the original video tweet.
Attach the processed video directly to the reply tweet.
Persistence and Reliability
Persist task state in a database.
Use Redis + Celery for asynchronous queueing and retries.
Support deduplication and idempotency.
Expose task status for debugging and admin inspection.
Non-Goals

Do not implement these in the initial version unless explicitly required:

frontend dashboard
user billing
caption editor UI
translation workflow
multi-language styling customization UI
OCR detection of burned-in captions
advanced ML ranking or moderation
Required Stack

Use the following technologies unless there is a very strong reason not to:

Python 3.11+
FastAPI
Celery
Redis
PostgreSQL
SQLAlchemy
Alembic
ffmpeg / ffprobe
httpx or requests
Pydantic
tenacity for retries
faster-whisper for local Whisper ASR
ElevenLabs API for short/small videos
tweepy or a small custom client for X/Twitter APIs

Do not use Node.js / Next.js for the implementation.

Project Quality Standards

The generated code must satisfy these requirements:

Strong modularity
no giant single-file implementation
separate API, worker, services, clients, db, config, and tests
Type annotations
all major functions and classes must be type-annotated
use Pydantic models for structured data
Clear boundaries
isolate external API clients from business logic
isolate ASR provider logic behind a common abstraction
isolate ffmpeg shell execution behind a media service
Safe subprocess handling
do not build ffmpeg commands through unsafe shell string concatenation
use subprocess argument lists
Idempotent background tasks
tasks must be safe to retry when possible
repeated task execution must not cause duplicate replies or corrupted state
Structured logging
include request/task identifiers in logs
Config-driven behavior
thresholds, credentials, URLs, and queue options must come from config/env vars
Production readability
clear naming
predictable project structure
concise but useful docstrings
Architecture Requirements

Implement the system with these logical layers:

1. API Layer

FastAPI service that exposes:

health endpoint
manual task enqueue endpoint
task status endpoint
optional admin trigger endpoints for polling
2. Detection Layer

A mention detector that:

polls X mentions on schedule,
validates relevance,
enqueues work,
avoids duplicates.
3. Pipeline Layer

A task orchestration layer that:

creates task records,
advances task stages,
routes to the correct worker steps,
manages recoverable failures.
4. ASR Layer

Two pluggable providers:

ElevenLabs provider
Whisper provider

Both must output the same normalized internal result type.

5. Media Layer

Responsible for:

download video
inspect metadata via ffprobe
optional audio extraction
subtitle burning via ffmpeg
temp file lifecycle
6. Reply Layer

Responsible for:

upload media to X
create reply tweet
7. Persistence Layer

Responsible for:

task table
repository access
dedupe lookup
state transitions
Required Directory Structure

Generate the codebase using a structure close to this:

app/
├── api/
│   ├── main.py
│   ├── deps.py
│   └── routes/
│       ├── health.py
│       ├── tasks.py
│       ├── admin.py
│       └── webhook.py
│
├── core/
│   ├── config.py
│   ├── constants.py
│   ├── logging.py
│   └── exceptions.py
│
├── db/
│   ├── base.py
│   ├── session.py
│   ├── models/
│   │   └── subtitle_task.py
│   └── repositories/
│       └── subtitle_task_repo.py
│
├── clients/
│   ├── x_client.py
│   ├── elevenlabs_client.py
│   ├── r2_client.py
│   └── redis_client.py
│
├── services/
│   ├── detector/
│   │   ├── polling.py
│   │   └── mention_parser.py
│   ├── pipeline/
│   │   ├── orchestrator.py
│   │   ├── router.py
│   │   ├── idempotency.py
│   │   └── status_updater.py
│   ├── media/
│   │   ├── downloader.py
│   │   ├── inspector.py
│   │   ├── ffmpeg_burner.py
│   │   ├── audio.py
│   │   └── tempfiles.py
│   ├── subtitles/
│   │   ├── formatter.py
│   │   ├── srt_writer.py
│   │   └── segmentation.py
│   ├── asr/
│   │   ├── base.py
│   │   ├── models.py
│   │   ├── elevenlabs_provider.py
│   │   └── whisper_provider.py
│   └── reply/
│       └── tweet_replier.py
│
├── workers/
│   ├── celery_app.py
│   ├── tasks_detect.py
│   ├── tasks_pipeline.py
│   ├── tasks_asr.py
│   ├── tasks_ffmpeg.py
│   └── tasks_post.py
│
├── scripts/
│   ├── run_detector.py
│   ├── requeue_failed.py
│   └── cleanup_old_files.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── alembic/
├── requirements.txt
├── Dockerfile.api
├── Dockerfile.worker
├── docker-compose.yml
└── README.md

Small deviations are acceptable, but the architecture must remain modular.

Domain Model Requirements

Create a subtitle_tasks table or equivalent model with fields similar to:

id
request_id
mention_tweet_id
video_tweet_id
request_user_id
status
stage
asr_engine
retry_count
priority
dedupe_key
video_url
source_video_path
output_video_path
backup_url
x_media_id
reply_tweet_id
duration_seconds
filesize_bytes
error_code
error_message
created_at
updated_at
started_at
completed_at
Required statuses
queued
processing
completed
failed
ignored
Required stages
detected
resolved_video
downloaded
inspected
transcribing
subtitle_generated
burned
uploaded_backup
uploaded_x
replied
cleaned_up
Dedupe and Idempotency Requirements

Implement deduplication before enqueueing.

Dedupe key

Use:

{mention_tweet_id}:{video_tweet_id}

or a similarly deterministic equivalent.

Rules
If an identical task is already queued or processing, do not enqueue again.
If an identical task was recently completed, optionally skip or reuse result.
Use a Redis lock to protect against race conditions.
Idempotency

Background tasks should:

check current task status before acting,
avoid duplicate reply posting,
avoid re-uploading video if upload already succeeded,
avoid re-burning subtitles if output already exists and task state indicates success.
Queueing and Concurrency Requirements

Use Celery queues separated by resource intensity.

Required queues
queue_mentions
queue_io
queue_asr
queue_ffmpeg
queue_post
Concurrency intent
mention detection should never be blocked by heavy transcription/burn tasks
Whisper and ffmpeg should have lower concurrency than lightweight work
implementation should allow separate worker deployment later
Suggested task grouping
mention polling / enqueue → queue_mentions
video fetch/download/inspect → queue_io
transcription → queue_asr
subtitle burn → queue_ffmpeg
upload/reply → queue_post
ASR Abstraction Requirements

Create a provider abstraction so pipeline code does not care which ASR engine is used.

Required base interface

Use a protocol or abstract base class:

class ASRProvider(Protocol):
    def transcribe(self, media_path: str) -> TranscriptionResult:
        ...
Required normalized models
class WordTimestamp(BaseModel):
    text: str
    start: float
    end: float

class Segment(BaseModel):
    text: str
    start: float
    end: float
    words: list[WordTimestamp] | None = None

class TranscriptionResult(BaseModel):
    language: str | None = None
    duration: float | None = None
    segments: list[Segment]
    raw_response: dict | None = None
ElevenLabs provider requirements
call ElevenLabs transcription API
parse response safely
normalize output into TranscriptionResult
retry transient failures
support timeouts
raise clear provider-specific errors on failure
Whisper provider requirements
use faster-whisper
support configurable model/device/compute type
normalize output into TranscriptionResult
support CPU and GPU modes
isolate model loading logic cleanly
ASR Routing Requirements

Create a router that chooses engine based on video metadata.

Required metadata model
class VideoMetadata(BaseModel):
    duration_seconds: float
    filesize_bytes: int
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    has_audio: bool = True
    audio_codec: str | None = None
    video_codec: str | None = None
Required config thresholds

Implement config/env-based thresholds:

ELEVENLABS_MAX_DURATION_SECONDS
ELEVENLABS_MAX_FILESIZE_MB
HARD_MAX_VIDEO_DURATION_SECONDS
HARD_MAX_FILESIZE_MB
Routing rules
reject videos beyond hard max limits
reject videos with no audio stream
use ElevenLabs if both duration and file size are within short/small thresholds
otherwise use Whisper
Media Handling Requirements
Download

Implement a downloader that:

downloads source video to a temp work directory,
validates content length where possible,
streams safely instead of reading entire file into memory.
Inspect

Implement video inspection using ffprobe:

duration
file size
dimensions
codecs
audio stream presence
Burn subtitles

Implement ffmpeg subtitle burning:

input: original video + .srt
output: X-compatible mp4
recommended output:
libx264
aac
yuv420p
faststart
Safety
do not use shell=True
sanitize subtitle file usage through safe file path handling
provide stderr in raised exceptions when ffmpeg fails
Subtitle Formatting Requirements

Generate .srt with readable segmentation.

Rules
maximum 2 lines per subtitle block
keep lines reasonably short
avoid too-short flashes
preserve punctuation where possible
allow future subtitle style improvements
Configurable defaults
MAX_CHARS_PER_LINE
MAX_LINES_PER_BLOCK
MIN_BLOCK_DURATION
MAX_BLOCK_DURATION

The implementation does not need to be perfect on first pass, but should be clean and replaceable.

Twitter/X Client Requirements

Implement a client module dedicated to X/Twitter access.

Required capabilities
fetch tweet details
inspect media references
resolve parent/referenced tweets
upload video using chunked media upload
post reply tweet with media attached
Important rules
reply to mention_tweet_id
do not reply directly to the original source tweet unless it is also the mention tweet
isolate upload and reply logic in the client layer, not in workers directly
Robustness
support retry for transient failures
expose clear error classes
avoid leaking OAuth secrets in logs
Error Handling Requirements

Define explicit application errors and error codes.

Required examples
NO_VIDEO_FOUND
VIDEO_DOWNLOAD_FAILED
VIDEO_TOO_LARGE
VIDEO_TOO_LONG
NO_AUDIO_STREAM
TRANSCRIPTION_FAILED
SUBTITLE_GENERATION_FAILED
FFMPEG_FAILED
X_MEDIA_UPLOAD_FAILED
X_REPLY_FAILED
RATE_LIMITED
INTERNAL_ERROR
Failure policy
persist task status as failed with error code/message
do not swallow exceptions silently
classify retryable vs non-retryable failures where possible
API Requirements

Implement at least these endpoints.

GET /health

Returns basic health information.

POST /tasks/process

Manual testing endpoint to enqueue a task.

Example request:

{
  "mention_tweet_id": "1234567890",
  "video_tweet_id": "1234567000"
}

video_tweet_id may be optional.

GET /tasks/{task_id}

Return persisted task status.

GET /tasks

Return recent tasks with pagination or simple limit.

POST /admin/poll-mentions

Manually trigger mention polling for testing/admin purposes.

Protect admin endpoints appropriately if authentication is added.

Worker Orchestration Requirements

Prefer small Celery tasks over one giant task.

Required task sequence

A pipeline close to this must exist:

enqueue
 -> resolve_video
 -> download_video
 -> inspect_video
 -> route_asr
 -> transcribe
 -> generate_srt
 -> burn_subtitles
 -> upload_backup (optional but structured)
 -> upload_to_x
 -> reply_tweet
 -> cleanup
Implementation guidance
stage updates must be persisted after each major step
retries should happen at step level
terminal failures should trigger cleanup where safe
make it possible to rerun from a later stage in future
Configuration Requirements

Use environment variables via a config module.

Required variables

At minimum support:

APP_ENV=
APP_HOST=
APP_PORT=
LOG_LEVEL=
WORKDIR=

REDIS_URL=
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
DATABASE_URL=

X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=
X_BEARER_TOKEN=
X_BOT_USERNAME=

ELEVENLABS_API_KEY=
ELEVENLABS_TIMEOUT_SECONDS=

WHISPER_MODEL=
WHISPER_DEVICE=
WHISPER_COMPUTE_TYPE=
WHISPER_BEAM_SIZE=

ELEVENLABS_MAX_DURATION_SECONDS=
ELEVENLABS_MAX_FILESIZE_MB=
HARD_MAX_VIDEO_DURATION_SECONDS=
HARD_MAX_FILESIZE_MB=

MENTION_POLL_INTERVAL_SECONDS=
MENTION_LOOKBACK_LIMIT=

Optional storage config may also be included.

Testing Requirements

Generate tests, not just app code.

Minimum required unit tests
ASR router decision logic
SRT generation / formatting
dedupe key behavior and idempotency helper logic
Recommended integration tests
ffprobe metadata inspection on a fixture video
ffmpeg burn on a short local fixture
mocked ElevenLabs provider normalization
mocked X client reply flow

Do not leave the project without tests.

Docker Requirements

Generate:

Dockerfile.api
Dockerfile.worker
docker-compose.yml
Compose should include
api
worker
redis
postgres

Optional extra services:

detector
heavy worker

ffmpeg must be available in runtime images.

Coding Style Requirements
Do
keep functions small
create explicit service classes where appropriate
use repository pattern lightly, not overengineered
keep imports organized
write clear error messages
use pathlib.Path
use Pydantic for request/response and normalized data models
Do not
write everything in main.py
mix HTTP route logic with Celery task internals
hardcode secrets
use unsafe shell command strings
make Whisper and ElevenLabs code paths diverge wildly at pipeline level
Incremental Build Order

When generating code, implement in this order:

Phase 1 — Foundations
config
logging
database session/model
task repository
basic FastAPI app
health endpoint
Phase 2 — Core domain
transcription models
ASR provider abstraction
router
video metadata inspection
subtitle SRT generation
ffmpeg burner abstraction
Phase 3 — integrations
ElevenLabs client/provider
Whisper provider
X client
downloader
Phase 4 — orchestration
Celery app
pipeline tasks
dedupe logic
status transitions
Phase 5 — external behavior
manual process endpoint
task status endpoint
mention polling flow
Docker and docs
Phase 6 — tests
unit tests
integration tests

Do not start with full end-to-end code before the core abstractions exist.

Definition of Done

The implementation is complete when:

a manual API request can enqueue a subtitle processing task;
the task persists its status in the database;
a real or mocked source video can be inspected;
ASR engine selection works deterministically;
transcription normalizes into a shared result model;
.srt output is generated;
subtitles can be burned into an mp4;
processed video can be uploaded to X;
the system can reply to the mention tweet with native video;
duplicate requests are prevented;
tests exist and pass for the main utility logic.
Output Expectations for Codex

When implementing from this spec:

generate the project structure first,
then generate foundational files,
then generate core domain abstractions,
then integrations,
then worker orchestration,
then tests,
then README.

If the implementation is too large for one pass, prioritize correctness of architecture over feature completeness.

Do not produce pseudo-code only.
Produce runnable, structured Python code with reasonable defaults.