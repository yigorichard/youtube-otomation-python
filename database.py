import sqlite3
import hashlib
import os

class Database:
    def __init__(self):
        self.db_file = "users.db"
        self.create_tables()
    
    def create_tables(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Kullanıcılar tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
        ''')
        
        # Kanallar tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            channel_id TEXT NOT NULL,
            channel_title TEXT NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            token_expiry TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, channel_id)
        )
        ''')
        
        # Transkript tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_path TEXT NOT NULL,
                transcript TEXT NOT NULL,
                language TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password, email):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            hashed_password = self.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                (username, hashed_password, email)
            )
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def check_login(self, username, password):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        hashed_password = self.hash_password(password)
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hashed_password)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        return user is not None 

    def save_channel(self, username, channel_data, tokens):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Kullanıcı ID'sini al
            cursor.execute("SELECT id FROM users WHERE username=?", (username,))
            user_id = cursor.fetchone()[0]
            
            # Kanal bilgilerini kaydet/güncelle
            cursor.execute("""
                INSERT OR REPLACE INTO channels 
                (user_id, channel_id, channel_title, access_token, refresh_token, token_expiry)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                channel_data['id'],
                channel_data['title'],
                tokens['access_token'],
                tokens['refresh_token'],
                tokens['expiry']
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Kanal kaydetme hatası: {str(e)}")
            return False

    def get_user_channels(self, username):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.* FROM channels c
                JOIN users u ON u.id = c.user_id
                WHERE u.username = ?
            """, (username,))
            
            channels = cursor.fetchall()
            conn.close()
            
            return channels
        except Exception as e:
            print(f"Kanal bilgileri alınamadı: {str(e)}")
            return [] 

    def update_channel_token(self, username, channel_id, new_token):
        """Kanal token'ını güncelle"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE channels 
                SET access_token = ?
                WHERE channel_id = ? AND user_id = (
                    SELECT id FROM users WHERE username = ?
                )
            """, (new_token, channel_id, username))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Token güncelleme hatası: {str(e)}")
            return False 

    def save_transcript(self, video_path, transcript, language):
        """Transkripti veritabanına kaydet"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transcripts (video_path, transcript, language)
                VALUES (?, ?, ?)
            ''', (video_path, transcript, language))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Transkript kaydetme hatası: {str(e)}")
            return False

    def get_transcript(self, video_path):
        """Video için kaydedilmiş transkripti getir"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT transcript, language FROM transcripts
                WHERE video_path = ?
            ''', (video_path,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result
        except Exception as e:
            print(f"Transkript getirme hatası: {str(e)}")
            return None

    def delete_transcript(self, video_path):
        """Video transkriptini sil"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM transcripts WHERE video_path = ?
            ''', (video_path,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Transkript silme hatası: {str(e)}")
            return False 