import firebase_admin
from firebase_admin import credentials, firestore
import os
import datetime
import numpy as np
from config.settings import Config

class DatabaseHandler:
    def __init__(self):
        self.db = None
        self.connect()

    def connect(self):
        try:
            # 1. เช็คไฟล์ Key
            if not os.path.exists(Config.FIREBASE_KEY_PATH):
                print(f"❌ [DB ERROR] Key not found at {Config.FIREBASE_KEY_PATH}")
                return

            # 2. เริ่มต้น Firebase App
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_KEY_PATH)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("✅ Firebase Firestore Connected! (Ready)")
            
        except Exception as e:
            print(f"❌ Connection Failed: {e}")

    def get_all_active_users(self):
        """ดึง User ทั้งหมด (สำหรับโหลดเข้า FaceMatcher)"""
        if self.db is None: return []
        try:
            docs = self.db.collection("users").where("is_active", "==", True).stream()
            users = []
            for doc in docs:
                data = doc.to_dict()
                # แปลง Vector เป็น Numpy Array ทันที เพื่อป้องกัน Error ทีหลัง
                if "face_vector" in data:
                    data["face_vector"] = np.array(data["face_vector"], dtype=np.float32)
                    users.append(data)
            return users
        except Exception as e:
            print(f"❌ Fetch Users Error: {e}")
            return []

    def get_user_by_id(self, user_id):
        """ดึงข้อมูล User รายคน"""
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
    # 💰 Payment Section (Transaction Logic)
    # ==========================================
    
    @staticmethod
    @firestore.transactional
    def _execute_payment(transaction, user_ref, txn_ref, amount, shop_id, items):
        """Logic การตัดเงินระดับ Database (Atomic Transaction)"""
        
        # 1. ดึงข้อมูลล่าสุดจาก DB
        snapshot = user_ref.get(transaction=transaction)
        
        if not snapshot.exists:
            # 🚨 จุดตาย: ถ้า User ID ผิด จะเด้งตรงนี้
            print(f"😱 [CRITICAL ERROR] ไม่พบ User ID: '{user_ref.id}' ใน Database!")
            raise Exception(f"User ID '{user_ref.id}' not found")

        user_data = snapshot.to_dict()
        
        # 2. แปลงค่าเงินเป็น Float เพื่อความชัวร์
        try:
            current_balance = float(user_data.get("balance", 0.0))
            amount = float(amount)
        except ValueError:
            raise Exception("ข้อมูลยอดเงินใน Database ผิดพลาด (ไม่ใช่ตัวเลข)")

        print(f"💰 [DEBUG] เงินที่มี: {current_balance:.2f} | ต้องจ่าย: {amount:.2f}")

        # 3. เช็คเงินพอไหม
        if current_balance < amount:
            raise Exception(f"ยอดเงินไม่พอ (มี: {current_balance}, จ่าย: {amount})")

        new_balance = current_balance - amount
        
        # 4. เตรียมข้อมูลใบเสร็จ
        txn_data = {
            "transaction_id": txn_ref.id,
            "user_id": user_data.get("user_id"),
            "user_name": user_data.get("name"),
            "amount": amount,
            "shop_id": shop_id,
            "items": items,
            "status": "SUCCESS",
            "timestamp": datetime.datetime.now(),
            "server_timestamp": firestore.SERVER_TIMESTAMP
        }

        # 5. เขียนลง Database (พร้อมกันทั้งคู่)
        transaction.update(user_ref, {"balance": new_balance})
        transaction.set(txn_ref, txn_data)

        # ส่งผลลัพธ์กลับเป็น Dictionary
        return {
            "success": True,
            "new_balance": new_balance,
            "receipt": txn_data
        }

    def process_payment(self, user_id, amount, items="Payment", shop_id="SHOP_01"):
        """ฟังก์ชันหลักที่หน้าจอ (UI) เรียกใช้"""
        if self.db is None: 
            return {"success": False, "error": "Database Disconnected"}

        # 🔍 DEBUG LOG: ดูว่าหน้าจอส่งอะไรมา
        print("\n" + "="*40)
        print(f"🚀 [START PAYMENT] User ID: {user_id}, Amount: {amount}")
        
        try:
            # แปลง ID เป็น String และลบช่องว่าง (กันเหนียว)
            clean_user_id = str(user_id).strip()
            
            user_ref = self.db.collection("users").document(clean_user_id)
            txn_ref = self.db.collection("transactions").document()

            # เรียก Transaction
            result_data = self._execute_payment(
                self.db.transaction(),
                user_ref,
                txn_ref,
                float(amount),
                shop_id,
                items
            )
            
            print(f"✅ [SUCCESS] ตัดเงินสำเร็จ! New Balance: {result_data['new_balance']}")
            print("="*40 + "\n")
            
            # ส่ง Dictionary กลับไปให้ UI (ห้ามส่ง Tuple)
            return result_data

        except Exception as e:
            print(f"❌ [FAILED] เกิดข้อผิดพลาด: {e}")
            print("="*40 + "\n")
            return {"success": False, "error": str(e)}