
<old_str>FILE_NOT_EXISTS</old_str>
<new_str>#!/usr/bin/env python3
"""
Core Trading Functions
Consolidated functions used across the system
"""

import glob
import os
import json
import pandas as pd
from datetime import datetime
import pytz

def get_latest_positions_file():
    """Get the most recent positions file"""
    try:
        # Try JSON first
        json_files = glob.glob("positions_*.json")
        if json_files:
            latest_json = max(json_files, key=lambda x: os.path.getctime(x))
            return latest_json, 'json'
        
        # Fall back to CSV
        csv_files = glob.glob("positions_*.csv")
        if csv_files:
            latest_csv = max(csv_files, key=lambda x: os.path.getctime(x))
            return latest_csv, 'csv'
        
        return None, None
    
    except Exception as e:
        print(f"❌ Error finding positions file: {e}")
        return None, None

def load_positions_data():
    """Load the latest positions data"""
    try:
        file_path, file_type = get_latest_positions_file()
        
        if not file_path:
            print("❌ No positions files found")
            return []
        
        print(f"📊 Loading positions from: {file_path}")
        
        if file_type == 'json':
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            # Convert CSV to dict format
            df = pd.read_csv(file_path)
            return df.to_dict('records')
    
    except Exception as e:
        print(f"❌ Error loading positions: {e}")
        return []

def cleanup_old_files(keep_count=3):
    """Remove old CSV and JSON files, keeping only the most recent ones"""
    try:
        print(f"🧹 Cleaning up old files, keeping {keep_count} most recent...")
        
        # Clean up CSV files
        csv_files = glob.glob("positions_*.csv")
        if len(csv_files) > keep_count:
            csv_files.sort(key=lambda x: os.path.getmtime(x))
            files_to_delete = csv_files[:-keep_count]
            
            for file in files_to_delete:
                os.remove(file)
                print(f"🗑️ Deleted old CSV: {file}")
        
        # Clean up JSON files
        json_files = glob.glob("positions_*.json")
        if len(json_files) > keep_count:
            json_files.sort(key=lambda x: os.path.getmtime(x))
            files_to_delete = json_files[:-keep_count]
            
            for file in files_to_delete:
                os.remove(file)
                print(f"🗑️ Deleted old JSON: {file}")
                
        print(f"✅ Cleanup completed")
        
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")

def get_system_health():
    """Get overall system health status"""
    try:
        latest_file, file_type = get_latest_positions_file()
        positions = load_positions_data()
        
        return {
            'status': 'healthy',
            'latest_file': latest_file,
            'file_type': file_type,
            'position_count': len(positions),
            'last_update': datetime.now(pytz.timezone('US/Central')).isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'last_check': datetime.now(pytz.timezone('US/Central')).isoformat()
        }

def cleanup_system_files():
    """Clean up old test files and duplicates"""
    import glob
    import os
    
    try:
        print("🧹 Starting system cleanup...")
        
        # Remove old test files
        old_tests = [
            "test_bingx_connection.py",
            "test_blofin_connection.py", 
            "test_kraken_debug.py",
            "test_kraken_standalone.py",
            "test_candlestick_data.py"
        ]
        
        for file in old_tests:
            if os.path.exists(file):
                os.remove(file)
                print(f"🗑️ Removed: {file}")
        
        # Clean up duplicate server files
        duplicates = [
            "discord_bot.py",
            "trading_alerts.py", 
            "hourly_trading_alerts.py",
            "hourly_sheets_sync.py"
        ]
        
        for file in duplicates:
            if os.path.exists(file):
                print(f"⚠️ Found duplicate: {file} (should be removed manually)")
        
        print("✅ System cleanup completed")
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

if __name__ == "__main__":
    # Test core functions
    print("🧪 Testing core functions...")
    health = get_system_health()
    print(f"System Health: {health}")
    
    positions = load_positions_data()
    print(f"Loaded {len(positions)} positions")
    
    cleanup_old_files()
    cleanup_system_files()
    print("✅ Core functions test completed")
</new_str>
