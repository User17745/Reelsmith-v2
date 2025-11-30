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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def run_pipeline():
    logging.info("Starting pipeline run...")
    
    try:
        logging.info("Step 1: Harvest")
        harvest()
        
        logging.info("Step 2: Score")
        run_scoring()
        
        logging.info("Step 3: Extract")
        run_extraction()
        
        logging.info("Step 4: Moderate")
        run_moderation()
        
        logging.info("Step 5: Script Gen")
        run_script_gen()
        
        logging.info("Step 6: TTS")
        run_tts()
        
        logging.info("Step 7: Render")
        run_render()
        
        logging.info("Pipeline run complete.")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")

def start_worker():
    logging.info("Worker started. Scheduling pipeline every 1 hour.")
    # Run once immediately
    run_pipeline()
    
    schedule.every(1).hours.do(run_pipeline)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    start_worker()
