#!/usr/bin/env python3
"""
Script to manually clear the groups table and remove orphaned groups.
Use this when testing group creation to clean up after failed attempts.

WARNING: This will delete ALL device groups for ALL users!
Only use this in development/testing environments.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_db_session
from models.device_group import DeviceGroup
from sqlalchemy import text
from utils.logging_config import get_logger

logger = get_logger('clear_groups_script')

def clear_groups_table():
    """Clear all device groups and their associations"""
    try:
        with get_db_session() as session:
            # First, let's see what we're about to delete
            total_groups = session.query(DeviceGroup).count()
            logger.info(f"Found {total_groups} device groups to delete")
            
            if total_groups == 0:
                logger.info("No groups to delete. Table is already empty.")
                return
            
            # Show details of groups before deletion
            groups = session.query(DeviceGroup).all()
            logger.info("Groups to be deleted:")
            for group in groups:
                logger.info(f"  - ID: {group.id}, Name: '{group.name}', User: {group.user_id}, Router: {group.router_id}")
            
            # Clear the association table first (device_group_devices)
            logger.info("Clearing device_group_devices association table...")
            result = session.execute(text("DELETE FROM device_group_devices"))
            logger.info(f"Deleted {result.rowcount} device-group associations")
            
            # Clear the main groups table
            logger.info("Clearing device_groups table...")
            result = session.execute(text("DELETE FROM device_groups"))
            logger.info(f"Deleted {result.rowcount} device groups")
            
            # Commit the changes
            session.commit()
            logger.info("✅ Successfully cleared all device groups and associations!")
            
            # Verify the tables are empty
            remaining_groups = session.query(DeviceGroup).count()
            logger.info(f"Remaining groups: {remaining_groups}")
            
    except Exception as e:
        logger.error(f"Failed to clear groups table: {str(e)}")
        raise

def clear_groups_for_user(user_id):
    """Clear device groups for a specific user only"""
    try:
        with get_db_session() as session:
            # Count groups for this user
            user_groups = session.query(DeviceGroup).filter(DeviceGroup.user_id == user_id).all()
            total_groups = len(user_groups)
            
            if total_groups == 0:
                logger.info(f"No groups found for user {user_id}")
                return
            
            logger.info(f"Found {total_groups} device groups for user {user_id}")
            
            # Show details
            for group in user_groups:
                logger.info(f"  - ID: {group.id}, Name: '{group.name}', Router: {group.router_id}")
            
            # Clear associations for this user's groups
            group_ids = [str(group.id) for group in user_groups]
            if group_ids:
                placeholders = ','.join(['%s'] * len(group_ids))
                result = session.execute(
                    text(f"DELETE FROM device_group_devices WHERE group_id IN ({placeholders})"),
                    group_ids
                )
                logger.info(f"Deleted {result.rowcount} device-group associations")
            
            # Delete the groups
            result = session.query(DeviceGroup).filter(DeviceGroup.user_id == user_id).delete()
            logger.info(f"Deleted {result} device groups for user {user_id}")
            
            session.commit()
            logger.info(f"✅ Successfully cleared all device groups for user {user_id}")
            
    except Exception as e:
        logger.error(f"Failed to clear groups for user {user_id}: {str(e)}")
        raise

def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clear device groups table')
    parser.add_argument('--user-id', help='Clear groups for specific user only')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if args.user_id:
        logger.info(f"Clearing groups for user: {args.user_id}")
        if not args.confirm:
            response = input(f"Are you sure you want to delete ALL device groups for user {args.user_id}? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Operation cancelled.")
                return
        clear_groups_for_user(args.user_id)
    else:
        logger.info("Clearing ALL device groups for ALL users!")
        if not args.confirm:
            response = input("Are you sure you want to delete ALL device groups? This cannot be undone! (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Operation cancelled.")
                return
        clear_groups_table()

if __name__ == "__main__":
    main()
