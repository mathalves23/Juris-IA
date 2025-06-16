#!/usr/bin/env python3
import sqlite3
import os

def test_database():
    db_path = 'instance/jurisia.db'
    print(f'Testing database at: {os.path.abspath(db_path)}')
    print(f'File exists: {os.path.exists(db_path)}')
    print(f'File size: {os.path.getsize(db_path) if os.path.exists(db_path) else "N/A"} bytes')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table";')
        tables = cursor.fetchall()
        print(f'Tables found: {tables}')
        
        # Testar uma query simples
        cursor.execute('SELECT COUNT(*) FROM usuarios;')
        user_count = cursor.fetchone()[0]
        print(f'User count: {user_count}')
        
        conn.close()
        print('✅ Connection successful!')
        return True
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == '__main__':
    test_database() 