import firebase_admin
from firebase_admin import credentials, firestore
import os
import numpy as np
from config.settings import Config

class DatabaseHandler:
    def __init__(self):
        self.db = None
        self.connect()

    def connect(self):
        try:
            if not os.path.exists(Config.FIREBASE_KEY_PATH):
                print(f"❌ Error: Key not found at {Config.FIREBASE_KEY_PATH}")
                return

            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_KEY_PATH)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("✅ Firebase Firestore Connected!")
        except Exception as e:
            print(f"❌ Connection Failed: {e}")

    def listen_for_updates(self, callback_function):
        if self.db is None: return

        def on_snapshot(col_snapshot, changes, read_time):
            print(f"♻️ Database Changed! Syncing RAM...")
            users_list = []
            for doc in col_snapshot:
                data = doc.to_dict()
                if "face_vector" in data:
                    # แปลง List เป็น Numpy Array เพื่อให้ Face Matcher ใช้งานได้
                    data["face_vector"] = np.array(data["face_vector"], dtype=np.float32)
                    users_list.append(data)
            
            # เรียก Callback ที่ส่งมาจาก MainWindow
            callback_function(users_list)

        # สั่งให้เฝ้า Collection "users" เฉพาะคนที่ active
        self.db.collection("users").where("is_active", "==", True).on_snapshot(on_snapshot)

    def get_all_active_users(self):
        """ดึง User ทั้งหมด (สำหรับโหลดครั้งแรก)"""
        if self.db is None: return []
        try:
            docs = self.db.collection("users").where("is_active", "==", True).stream()
            users = []
            for doc in docs:
                data = doc.to_dict()
                if "face_vector" in data:
                    data["face_vector"] = np.array(data["face_vector"], dtype=np.float32)
                    users.append(data)
            return users
        except Exception as e:
            print(f"❌ Fetch Users Error: {e}")
            return []

    def get_user_by_id(self, user_id):
        """ดึงข้อมูล User ตาม ID"""
        if self.db is None: return None
        try:
            doc = self.db.collection("users").document(str(user_id)).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            print(f"❌ Get User Error: {e}")
            return None