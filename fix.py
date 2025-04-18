#!/usr/bin/env python3
"""
Database Reset Script

This script resets the database by deleting all data without dropping tables.
It preserves the database structure but removes all records.
"""
import os
import sys
import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
script_dir = Path(__file__).resolve().parent
project_dir = script_dir
sys.path.append(str(project_dir))

# Import project settings
try:
    from config import DATABASE_URL
except ImportError:
    logger.error("Could not import DATABASE_URL from config. Using default path.")
    DATABASE_URL = "sqlite:///./chimeo.db"

def get_db_path():
    """Extract the SQLite database file path from DATABASE_URL."""
    # Parse the SQLite URL (e.g., "sqlite:///./chimeo.db" -> "./chimeo.db")
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL[10:]
        # Handle relative paths
        if db_path.startswith('./'):
            db_path = os.path.join(project_dir, db_path[2:])
        return db_path
    else:
        logger.error(f"Unsupported database URL: {DATABASE_URL}")
        logger.error("This script only supports SQLite databases.")
        sys.exit(1)

def reset_sqlite_database(db_path):
    """Reset SQLite database by deleting all data but preserving tables."""
    try:
        # Verify the database file exists
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return False

        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names (excluding SQLite system tables)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION;")
        
        # Disable foreign key constraints temporarily
        conn.execute("PRAGMA foreign_keys = OFF;")
        
        # Delete data from each table
        for table in tables:
            table_name = table[0]
            logger.info(f"Deleting all data from table: {table_name}")
            cursor.execute(f"DELETE FROM {table_name};")
        
        # Re-enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON;")
        
        # Commit changes
        conn.commit()
        logger.info("Database reset complete. All data has been deleted.")
        
        # Close the connection
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def main():
    logger.info("Starting database reset process...")
    
    # Get database path
    db_path = get_db_path()
    logger.info(f"Database path: {db_path}")
    
    # Confirm with user
    print("\n⚠️  WARNING: This will delete ALL DATA in your database! ⚠️")
    print(f"Database: {db_path}")
    choice = input("\nAre you sure you want to continue? (yes/no): ")
    
    if choice.lower() not in ['yes', 'y']:
        logger.info("Database reset cancelled by user.")
        return
    
    # Reset the database
    success = reset_sqlite_database(db_path)
    
    if success:
        logger.info("✅ Database reset successful. All data has been deleted.")
    else:
        logger.error("❌ Database reset failed.")

if __name__ == "__main__":
    main()
