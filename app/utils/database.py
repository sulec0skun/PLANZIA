import sqlite3
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "app/data/planzia.db")

# Veritabanı bağlantısını sağlayan yeni fonksiyon
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row # Kolay erişim için sütun adlarını kullanırız
    return conn

def init_database():
    conn = get_db_connection()
    c = conn.cursor()

    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create events table
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_username TEXT NOT NULL,
            event_code TEXT UNIQUE NOT NULL,
            suggestion TEXT,
            is_approved INTEGER DEFAULT 0 -- Yeni eklendi: 0 = hayır, 1 = evet
        )
    ''')

    # Create preferences table
    c.execute('''
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_code TEXT NOT NULL,
            username TEXT NOT NULL,
            budget TEXT,
            location TEXT,
            activity_level TEXT,
            available_days TEXT, -- Yeni eklendi
            FOREIGN KEY (event_code) REFERENCES events (event_code),
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')

    conn.commit()
    conn.close()

def create_user(username, hashed_password):
    """Yeni bir kullanıcıyı veritabanına ekler."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Kullanıcı zaten varsa
        return False
    finally:
        conn.close()

def authenticate_user(username):
    """Kullanıcıyı veritabanında doğrular. Sadece kullanıcıyı çeker, parola karşılaştırması auth.py'de yapılır."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return user['password'] # Doğru hashlenmiş parolayı döner
    return None

def create_event(creator_username, event_code):
    """Yeni bir etkinlik oluşturur ve veritabanına kaydeder."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO events (creator_username, event_code) VALUES (?, ?)", (creator_username, event_code))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Etkinlik kodu zaten varsa (çok düşük bir ihtimal ama handle edelim)
        return False
    finally:
        conn.close()

def get_event_by_code(event_code):
    """Etkinlik koduna göre etkinliği veritabanından çeker."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE event_code = ?", (event_code,))
    event = c.fetchone()
    conn.close()
    return event

def save_preferences(event_code, username, budget, location, activity_level, available_days):
    """Kullanıcı tercihlerini veritabanına kaydeder veya günceller."""
    print(f"DEBUG (DB): save_preferences çağrıldı. Event: {event_code}, User: {username}")
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Mevcut tercihleri kontrol et ve güncelle veya yeni ekle
        c.execute("SELECT * FROM preferences WHERE event_code = ? AND username = ?", (event_code, username))
        existing_pref = c.fetchone()

        if existing_pref:
            print(f"DEBUG (DB): Mevcut tercih bulundu, güncelleniyor. Event: {event_code}, User: {username}")
            c.execute("""
                UPDATE preferences
                SET budget = ?, location = ?, activity_level = ?, available_days = ?
                WHERE event_code = ? AND username = ?
            """, (budget, location, activity_level, available_days, event_code, username))
        else:
            print(f"DEBUG (DB): Yeni tercih ekleniyor. Event: {event_code}, User: {username}")
            c.execute("""
                INSERT INTO preferences (event_code, username, budget, location, activity_level, available_days)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event_code, username, budget, location, activity_level, available_days))
        conn.commit()
        print(f"DEBUG (DB): Tercihler başarıyla kaydedildi/güncellendi. Event: {event_code}, User: {username}")
        return True
    except sqlite3.IntegrityError as e:
        print(f"DEBUG (DB) HATA: Database Integrity Error saving preferences: {e}. Event Code: {event_code}, Username: {username}")
        return False
    except Exception as e:
        print(f"DEBUG (DB) HATA: General Error saving preferences: {e}")
        return False
    finally:
        conn.close()

def get_event_preferences(event_code):
    """Bir etkinliğe ait tüm kullanıcı tercihlerini çeker."""
    print(f"DEBUG (DB): get_event_preferences fonksiyonu çağrıldı. Event: {event_code}") # Fonksiyonun çağrıldığını görmek için
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username, budget, location, activity_level, available_days FROM preferences WHERE event_code = ?", (event_code,))
    preferences = c.fetchall()
    print(f"DEBUG (DB): {event_code} için çekilen tercihler: {preferences}")
    conn.close()
    return [dict(row) for row in preferences]

def update_event_suggestion(event_code, suggestion):
    """Bir etkinliğin AI tarafından oluşturulan önerisini günceller."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE events SET suggestion = ? WHERE event_code = ?", (suggestion, event_code))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating event suggestion: {e}")
        return False
    finally:
        conn.close()

def mark_event_as_approved(event_code):
    """Bir etkinliği onaylandı olarak işaretler."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE events SET is_approved = 1 WHERE event_code = ?", (event_code,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error marking event as approved: {e}")
        return False
    finally:
        conn.close()

def get_event_creator(event_code):
    """Bir etkinliğin yaratıcısını döndürür."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT creator_username FROM events WHERE event_code = ?", (event_code,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_approved_events_for_user(username):
    """Bir kullanıcıya ait onaylanmış tüm etkinlikleri çeker."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT e.* FROM events e
        LEFT JOIN preferences p ON e.event_code = p.event_code
        WHERE e.is_approved = 1 AND (e.creator_username = ? OR p.username = ?)
        ORDER BY e.id DESC
    """, (username, username))
    approved_events = c.fetchall()
    conn.close()
    return [dict(row) for row in approved_events]

# get_event_preferences, update_event_suggestion
# fonksiyonları daha sonra eklenecek.

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!")
