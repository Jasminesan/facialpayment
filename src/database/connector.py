import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import transaction
import os
import datetime
from config.settings import Config

# ✅ ต้อง import numpy ด้วย เพราะฟังก์ชัน get_user_by_face อาจจะถูกเรียกใช้แบบฉุกเฉิน
import numpy as np 

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

    def get_all_active_users(self):
        """ดึง User ทั้งหมดส่งให้ FaceMatcher"""
        if self.db is None: return []
        try:
            docs = self.db.collection("users").where("is_active", "==", True).stream()
            users = []
            for doc in docs:
                data = doc.to_dict()
                if "face_vector" in data:
                    users.append(data)
            return users
        except Exception as e:
            print(f"❌ Fetch Users Error: {e}")
            return []

    # ✅ ฟังก์ชันที่หายไป (เพิ่มกลับมาแล้ว)
    def get_user_by_id(self, user_id):
        """ดึงข้อมูล User ตาม ID"""
        if self.db is None: return None
        try:
            doc = self.db.collection("users").document(str(user_id)).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"❌ Get User Error: {e}")
            return None

    # ==========================================
    # 💰 Payment Section
    # ==========================================
    
    @firestore.transactional
    def _execute_payment(transaction, user_ref, txn_ref, amount, shop_id, items):
        snapshot = user_ref.get(transaction=transaction)
        
        if not snapshot.exists:
            raise Exception("User not found")

        user_data = snapshot.to_dict()
        current_balance = user_data.get("balance", 0.0)

        if current_balance < amount:
            raise Exception(f"ยอดเงินไม่พอ (มี: {current_balance}, จ่าย: {amount})")

        new_balance = current_balance - amount
        
        txn_data = {
            "transaction_id": txn_ref.id,
            "user_id": user_data.get("user_id"),
            "user_name": user_data.get("name"),
            "amount": float(amount),
            "shop_id": shop_id,
            "items": items,
            "status": "SUCCESS",
            "timestamp": datetime.datetime.now(),
            "server_timestamp": firestore.SERVER_TIMESTAMP
        }

        transaction.update(user_ref, {"balance": new_balance})
        transaction.set(txn_ref, txn_data)

        return {
            "success": True,
            "new_balance": new_balance,
            "receipt": txn_data
        }

    def process_payment(self, user_id, amount, items="Payment", shop_id="SHOP_01"):
        if self.db is None: return False, "Database Disconnected"

        try:
            user_ref = self.db.collection("users").document(str(user_id))
            txn_ref = self.db.collection("transactions").document()

            result = self._execute_payment(
                self.db.transaction(),
                user_ref,
                txn_ref,
                float(amount),
                shop_id,
                items
            )
            
            print(f"✅ ตัดเงินสำเร็จ! บิลเลขที่: {result['receipt']['transaction_id']}")
            return True, result

        except Exception as e:
            print(f"❌ ตัดเงินล้มเหลว: {e}")
            return False, str(e)