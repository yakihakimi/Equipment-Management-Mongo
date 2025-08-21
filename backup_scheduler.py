#!/usr/bin/env python3
"""
Automatic Backup Scheduler Script
This script runs automatic backups at specified intervals.
Can be executed by cron job, Windows Task Scheduler, or any other scheduler.

Usage:
    python backup_scheduler.py

To set up as a cron job (Linux/Mac):
    # Run every hour
    0 * * * * /path/to/python /path/to/backup_scheduler.py
    
    # Run every 30 minutes
    */30 * * * * /path/to/python /path/to/backup_scheduler.py

To set up as Windows Task Scheduler:
    1. Open Task Scheduler
    2. Create Basic Task
    3. Set trigger (e.g., every 1 hour)
    4. Action: Start a program
    5. Program: python
    6. Arguments: backup_scheduler.py
"""

import sys
import os
import traceback
import time

# Add the current directory to Python path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from backup_csv_for_db_restore import run_background_automatic_backup
from datetime import datetime

def main():
    """Main function to run the backup process."""
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting automatic backup check...")
        time.sleep(5)  # Add delay to see the print
        
        # Get absolute paths to avoid permission issues
        current_dir = os.path.dirname(os.path.abspath(__file__))
        log_file_path = os.path.join(current_dir, "backup_scheduler.log")
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Working directory: {current_dir}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Log file path: {log_file_path}")
        time.sleep(5)  # Add delay to see the print
        
        # Run the background backup
        backup_created, message = run_background_automatic_backup(
            backup_interval_hours=0.02,  # Changed to 1 hour for normal operation
            log_file=log_file_path
        )
        
        if backup_created:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Backup created successfully!")
            time.sleep(5)  # Add delay to see the print
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ℹ️ {message}")
            time.sleep(5)  # Add delay to see the print
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Backup check completed.")
        time.sleep(5)  # Add delay to see the print
        
    except Exception as e:
        error_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ ERROR: {str(e)}"
        print(error_msg)
        time.sleep(5)  # Add delay to see the print
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Traceback: {traceback.format_exc()}")
        time.sleep(5)  # Add delay to see the print
        
        # Also log the error to the log file with better error handling
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            log_file_path = os.path.join(current_dir, "backup_scheduler.log")
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"{error_msg}\n")
        except Exception as log_error:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to write to log file: {log_error}")
            time.sleep(5)  # Add delay to see the print

# Execute the main function immediately when script is run
# This ensures it runs regardless of how the script is called
if __name__ == "__main__":
    main()
else:
    # Also run when imported (for Task Scheduler compatibility)
    main()
