import os
import sys

# Ensure app modules can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()

from app.services.cleanup_service import CleanupService

def run():
    print("Forcing cleanup of stale processing jobs...")
    service = CleanupService()
    # timeout_seconds=0 will force everything currently processing to be marked as failed
    stats = service.run_cleanup(timeout_seconds=0)
    print("Cleanup Complete!")
    print(stats)

if __name__ == "__main__":
    run()
