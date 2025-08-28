#!/usr/bin/env python3
"""
Debug script to print scheduled tasks table contents.
Run this script to see the current state of scheduled tasks in the database.

Usage: python debug_scheduled_tasks.py
"""

import sys
import os
from datetime import datetime
import pytz

# Add the backend2 directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import db
from models.scheduled_task import ScheduledTask
from decouple import config


def print_scheduled_tasks():
    """Print all scheduled tasks in a formatted table."""
    try:
        # Get database session
        session = db.get_session()
        
        # Get scheduler timezone
        tz_name = config('SCHEDULER_TIMEZONE', default='Asia/Jerusalem')
        tz = pytz.timezone(tz_name)
        current_time = datetime.now(tz)
        
        print(f"🕐 Current time ({tz_name}): {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("=" * 120)
        
        # Query all scheduled tasks
        tasks = session.query(ScheduledTask).order_by(ScheduledTask.created_at.desc()).all()
        
        if not tasks:
            print("No scheduled tasks found.")
            return
        
        print(f"Found {len(tasks)} scheduled task(s):")
        print("=" * 120)
        
        # Print header
        header = f"{'ID':<36} {'Service.Task':<25} {'Type':<8} {'Enabled':<7} {'Interval':<8} {'Hour:Min':<8} {'Last Run':<19} {'Status':<8} {'User ID':<36}"
        print(header)
        print("-" * 120)
        
        # Print each task
        for task in tasks:
            # Format task ID (first 8 chars)
            task_id = str(task.id)[:8] + "..."
            
            # Format service.task
            service_task = f"{task.service}.{task.task}"
            if len(service_task) > 24:
                service_task = service_task[:21] + "..."
            
            # Format task type
            task_type = task.task_type or "fixed"
            
            # Format enabled status
            enabled = "✓" if task.enabled else "✗"
            
            # Format interval
            interval = f"{task.interval_minutes}m" if task.interval_minutes else "-"
            
            # Format hour:minute
            if task.hour is not None and task.minute is not None:
                hour_min = f"{task.hour:02d}:{task.minute:02d}"
            else:
                hour_min = "-"
            
            # Format last run time
            if task.last_run_at:
                # Convert to scheduler timezone for display
                if task.last_run_at.tzinfo is None:
                    # Database timestamp is timezone-naive UTC, convert to scheduler timezone
                    last_run_utc = pytz.UTC.localize(task.last_run_at)
                    last_run_display = last_run_utc.astimezone(tz)
                else:
                    # Already timezone-aware, convert to scheduler timezone
                    last_run_display = task.last_run_at.astimezone(tz)
                last_run = last_run_display.strftime('%m-%d %H:%M:%S')
            else:
                last_run = "Never"
            
            # Format status
            status = task.last_status or "-"
            
            # Format user ID (first 8 chars)
            user_id = str(task.user_id)[:8] + "..."
            
            print(f"{task_id:<36} {service_task:<25} {task_type:<8} {enabled:<7} {interval:<8} {hour_min:<8} {last_run:<19} {status:<8} {user_id:<36}")
        
        print("=" * 120)
        
        # Print detailed info for interval tasks
        interval_tasks = [t for t in tasks if t.task_type == 'interval']
        if interval_tasks:
            print(f"\n📊 Interval Task Analysis:")
            print("-" * 60)
            for task in interval_tasks:
                print(f"Task: {task.service}.{task.task}")
                print(f"  ID: {task.id}")
                print(f"  Enabled: {task.enabled}")
                print(f"  Interval: {task.interval_minutes} minutes")
                print(f"  Created: {task.created_at}")
                print(f"  Last run (DB): {task.last_run_at}")
                if task.last_run_at and task.last_run_at.tzinfo is None:
                    last_run_utc = pytz.UTC.localize(task.last_run_at)
                    last_run_display = last_run_utc.astimezone(tz)
                    print(f"  Last run (Scheduler TZ): {last_run_display.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                print(f"  Last status: {task.last_status}")
                print(f"  Last error: {task.last_error}")
                
                if task.last_run_at:
                    # Calculate time since last run
                    if task.last_run_at.tzinfo is None:
                        # Database timestamp is timezone-naive UTC, convert to scheduler timezone
                        last_run_utc = pytz.UTC.localize(task.last_run_at)
                        last_run_tz_aware = last_run_utc.astimezone(tz)
                    else:
                        # Already timezone-aware, convert to scheduler timezone
                        last_run_tz_aware = task.last_run_at.astimezone(tz)
                    
                    time_since_last = (current_time - last_run_tz_aware).total_seconds()
                    minutes_since_last = time_since_last / 60
                    
                    print(f"  Time since last run: {minutes_since_last:.1f} minutes")
                    
                    if task.interval_minutes:
                        if minutes_since_last >= task.interval_minutes:
                            print(f"  ⚠️  DUE NOW: {minutes_since_last:.1f} >= {task.interval_minutes} minutes")
                        else:
                            next_run_minutes = task.interval_minutes - minutes_since_last
                            print(f"  ⏰ Next run in: {next_run_minutes:.1f} minutes")
                else:
                    print(f"  ⚠️  WILL RUN IMMEDIATELY: Never run before")
                
                print()
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error querying scheduled tasks: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🔍 Scheduled Tasks Debug Report")
    print("=" * 120)
    print_scheduled_tasks()

