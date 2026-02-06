import time
import schedule
import logging
from app.harvest import harvest
from app.score import run_scoring
from app.extract import run_extraction
from app.moderate import run_moderation
from app.script_gen import run_script_gen
from app.tts_gen import run_tts
from app.render import run_render
from app.retention import run_retention
from app.subtitles import run_subtitles
from app.config import validate_config, ConfigError
from app.logging_utils import configure_logging, log_event

configure_logging()
logger = logging.getLogger("reelsmith")

def run_pipeline():
    log_event(logger, "pipeline_start")
    pipeline_start = time.monotonic()
    tts_duration = None
    subtitles_duration = None
    render_duration = None
    
    try:
        validate_config()
        log_event(logger, "step_start", step="harvest")
        harvest()
        
        log_event(logger, "step_start", step="score")
        run_scoring()
        
        log_event(logger, "step_start", step="extract")
        run_extraction()
        
        log_event(logger, "step_start", step="moderate")
        run_moderation()
        
        log_event(logger, "step_start", step="script_gen")
        run_script_gen()
        
        log_event(logger, "step_start", step="tts")
        tts_start = time.monotonic()
        run_tts()
        tts_duration = time.monotonic() - tts_start
        
        log_event(logger, "step_start", step="subtitles")
        subtitles_start = time.monotonic()
        run_subtitles()
        subtitles_duration = time.monotonic() - subtitles_start
        
        log_event(logger, "step_start", step="render")
        render_start = time.monotonic()
        run_render()
        render_duration = time.monotonic() - render_start
        
        log_event(logger, "step_start", step="retention")
        run_retention()
        
        log_event(logger, "pipeline_complete")
        log_event(
            logger,
            "pipeline_metrics",
            duration_total=time.monotonic() - pipeline_start,
            duration_tts=tts_duration,
            duration_subtitles=subtitles_duration,
            duration_render=render_duration,
        )
        
    except ConfigError as e:
        log_event(logger, "pipeline_failed", error=str(e), error_type="config")
    except Exception as e:
        log_event(logger, "pipeline_failed", error=str(e), error_type="runtime")

def start_worker():
    log_event(logger, "worker_started", schedule="1h")
    # Run once immediately
    run_pipeline()
    
    schedule.every(1).hours.do(run_pipeline)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    start_worker()
