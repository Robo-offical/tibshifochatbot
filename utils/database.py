import sqlite3
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)

def get_connection():
    """DB ulanishini olish"""
    return sqlite3.connect(config.DATABASE_NAME, check_same_thread=False)

def init_db():
    """Ma'lumotlar bazasini ishga tushurish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # So'rovlar jadvali
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        admin_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # Adminlar jadvali (guruh adminlari uchun)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        added_by INTEGER,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (added_by) REFERENCES users (user_id)
    )
    ''')
    
    # Javoblar jadvali
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        admin_id INTEGER NOT NULL,
        reply_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (request_id) REFERENCES requests (id),
        FOREIGN KEY (admin_id) REFERENCES users (user_id)
    )
    ''')
    
    # Dastlabki asosiy adminni qo'shish
    try:
        cursor.execute("INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, ?)", 
                      (config.ADMIN_ID, config.ADMIN_ID))
    except Exception as e:
        logger.error(f"Dastlabki admin qo'shishda xatolik: {e}")
    
    conn.commit()
    conn.close()
    logger.info("✅ Ma'lumotlar bazasi ishga tushdi")

def add_user(user_id, username, first_name, last_name):
    """Yangi foydalanuvchi qo'shish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_active)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def add_request(user_id, message):
    """Yangi so'rov qo'shish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO requests (user_id, message, status, created_at)
    VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
    ''', (user_id, message))
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return request_id

def add_reply(request_id, admin_id, reply_text):
    """Admin javobini qo'shish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Javobni saqlash
    cursor.execute('''
    INSERT INTO replies (request_id, admin_id, reply_text)
    VALUES (?, ?, ?)
    ''', (request_id, admin_id, reply_text))
    
    # So'rov statusini yangilash
    cursor.execute('''
    UPDATE requests 
    SET status = 'completed', admin_id = ?, 
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (admin_id, request_id))
    
    conn.commit()
    conn.close()

def get_statistics():
    """Statistika olish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM requests")
    total_requests = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM requests WHERE status='pending'")
    pending_requests = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM requests WHERE status='in_progress'")
    in_progress_requests = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM requests WHERE status='completed'")
    completed_requests = cursor.fetchone()[0]
    
    # Bugungi so'rovlar
    cursor.execute("SELECT COUNT(*) FROM requests WHERE DATE(created_at) = DATE('now')")
    today_requests = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_users': total_users,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'in_progress_requests': in_progress_requests,
        'completed_requests': completed_requests,
        'today_requests': today_requests
    }

def search_user(query):
    """Foydalanuvchini qidirish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM users 
    WHERE user_id LIKE ? OR username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
    LIMIT 50
    ''', (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_requests_by_status(status):
    """Status bo'yicha so'rovlarni olish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.*, u.username, u.first_name 
    FROM requests r 
    LEFT JOIN users u ON r.user_id = u.user_id 
    WHERE r.status = ?
    ORDER BY r.created_at DESC
    ''', (status,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_request_details(request_id):
    """So'rov tafsilotlarini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.*, u.username, u.first_name, u.user_id
    FROM requests r 
    LEFT JOIN users u ON r.user_id = u.user_id 
    WHERE r.id = ?
    ''', (request_id,))
    
    result = cursor.fetchone()
    conn.close()
    return result

def update_request_status(request_id, status, admin_id=None):
    """So'rov statusini yangilash"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE requests 
    SET status = ?, admin_id = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (status, admin_id, request_id))
    
    conn.commit()
    conn.close()

def get_all_users():
    """Barcha foydalanuvchilarni olish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return users

def get_user_requests(user_id):
    """Foydalanuvchi so'rovlarini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.*, u.username, u.first_name 
    FROM requests r 
    LEFT JOIN users u ON r.user_id = u.user_id 
    WHERE r.user_id = ? 
    ORDER BY r.created_at DESC
    LIMIT 10
    ''', (user_id,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_all_requests(limit=20):
    """Barcha so'rovlarni olish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.id, r.status, u.first_name, u.username, r.message, r.created_at
    FROM requests r 
    LEFT JOIN users u ON r.user_id = u.user_id 
    ORDER BY r.created_at DESC 
    LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def is_group_member_admin(user_id):
    """Foydalanuvchi guruh admini yoki ekanligini tekshirish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Adminlar jadvalidan tekshirish
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ? AND is_active = 1", (user_id,))
    is_admin = cursor.fetchone() is not None
    
    conn.close()
    return is_admin

def add_group_admin(user_id, added_by=None):
    """Yangi guruh adminini qo'shish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT OR REPLACE INTO admins (user_id, added_by, is_active)
        VALUES (?, ?, 1)
        ''', (user_id, added_by or user_id))
        
        conn.commit()
        result = True
    except Exception as e:
        logger.error(f"Admin qo'shishda xatolik: {e}")
        result = False
    
    conn.close()
    return result

def get_group_admins():
    """Guruh adminlarini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT a.user_id, u.username, u.first_name, a.added_at, a.added_by
    FROM admins a
    LEFT JOIN users u ON a.user_id = u.user_id
    WHERE a.is_active = 1
    ORDER BY a.added_at DESC
    ''')
    
    admins = cursor.fetchall()
    conn.close()
    return admins

def remove_group_admin(user_id):
    """Guruh adminini o'chirish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE admins SET is_active = 0 WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0

def get_recent_requests(count=10):
    """Oxirgi so'rovlarni olish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.id, r.status, u.username, u.first_name, r.message, r.created_at,
           (SELECT COUNT(*) FROM replies WHERE request_id = r.id) as reply_count
    FROM requests r
    LEFT JOIN users u ON r.user_id = u.user_id
    ORDER BY r.created_at DESC
    LIMIT ?
    ''', (count,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_request_replies(request_id):
    """So'rovga berilgan javoblarni olish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.reply_text, r.created_at, u.username, u.first_name
    FROM replies r
    LEFT JOIN users u ON r.admin_id = u.user_id
    WHERE r.request_id = ?
    ORDER BY r.created_at ASC
    ''', (request_id,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def update_user_activity(user_id):
    """Foydalanuvchi faolligini yangilash"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE users 
    SET last_active = CURRENT_TIMESTAMP
    WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()

def get_user_by_id(user_id):
    """Foydalanuvchini ID bo'yicha olish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM users WHERE user_id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    return result

def get_daily_stats():
    """Kunlik statistika"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bugungi so'rovlar
    cursor.execute("SELECT COUNT(*) FROM requests WHERE DATE(created_at) = DATE('now')")
    today_requests = cursor.fetchone()[0]
    
    # Bugungi foydalanuvchilar
    cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(joined_date) = DATE('now')")
    today_users = cursor.fetchone()[0]
    
    # Haftalik statistika
    cursor.execute("""
    SELECT 
        DATE(created_at) as day,
        COUNT(*) as request_count
    FROM requests 
    WHERE created_at >= DATE('now', '-7 days')
    GROUP BY DATE(created_at)
    ORDER BY day DESC
    """)
    
    weekly_stats = cursor.fetchall()
    
    conn.close()
    
    return {
        'today_requests': today_requests,
        'today_users': today_users,
        'weekly_stats': weekly_stats
    }

def backup_database():
    """Ma'lumotlar bazasini backup qilish"""
    import shutil
    import os
    from datetime import datetime
    
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"tibshifo_support_{timestamp}.db")
    
    try:
        shutil.copy2(config.DATABASE_NAME, backup_file)
        logger.info(f"✅ Backup yaratildi: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"❌ Backup yaratishda xatolik: {e}")
        return None

def cleanup_old_data(days=30):
    """Eski ma'lumotlarni tozalash"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 30 kundan oldingi tugatilgan so'rovlarni o'chirish
        cursor.execute('''
        DELETE FROM requests 
        WHERE status = 'completed' 
        AND created_at < DATE('now', ?)
        ''', (f'-{days} days',))
        
        deleted_requests = cursor.rowcount
        
        # Javoblarni ham o'chirish
        cursor.execute('''
        DELETE FROM replies 
        WHERE created_at < DATE('now', ?)
        ''', (f'-{days} days',))
        
        deleted_replies = cursor.rowcount
        
        conn.commit()
        logger.info(f"✅ Eski ma'lumotlar tozalandi: {deleted_requests} so'rov, {deleted_replies} javob")
        
        return {
            'deleted_requests': deleted_requests,
            'deleted_replies': deleted_replies
        }
        
    except Exception as e:
        logger.error(f"❌ Ma'lumotlarni tozalashda xatolik: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

# Test funksiyasi
def test_database():
    """Database test"""
    try:
        init_db()
        
        # Test qilish
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        logger.info("📊 Database jadvallari:")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        conn.close()
        logger.info("✅ Database test muvaffaqiyatli!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test xatosi: {e}")
        return False

if __name__ == "__main__":
    # Test uchun
    test_database()