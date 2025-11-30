import os
import time
import logging

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")

def cleanup_workspace(max_age_hours=168):
    """
    Deletes files in workspace subdirectories older than max_age_hours.
    Default is 7 days (168 hours).
    """
    logging.info(f"Starting workspace cleanup (max age: {max_age_hours} hours)...")
    
    subdirs = ["raw", "canonical", "scripts", "frames", "output"]
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    
    deleted_count = 0
    
    for subdir in subdirs:
        dir_path = os.path.join(WORKSPACE_DIR, subdir)
        if not os.path.exists(dir_path):
            continue
            
        # Walk through directory (handles nested frames dirs)
        for root, dirs, files in os.walk(dir_path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    if os.path.getmtime(file_path) < cutoff:
                        os.remove(file_path)
                        logging.info(f"Deleted old file: {file_path}")
                        deleted_count += 1
                except Exception as e:
                    logging.error(f"Error deleting {file_path}: {e}")
            
            # Remove empty directories (except the root subdir itself)
            for name in dirs:
                dir_to_remove = os.path.join(root, name)
                try:
                    if not os.listdir(dir_to_remove):
                        os.rmdir(dir_to_remove)
                        logging.info(f"Removed empty dir: {dir_to_remove}")
                except Exception as e:
                    logging.error(f"Error removing dir {dir_to_remove}: {e}")

    logging.info(f"Cleanup complete. Deleted {deleted_count} files.")

def run_retention():
    # Default to 7 days
    cleanup_workspace(max_age_hours=168)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_retention()
