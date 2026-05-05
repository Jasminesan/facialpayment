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
            if not os.path.exists(Config.FIREBASE_KEY_PATH):
                print(f"[DB ERROR] Key not found at {Config.FIREBASE_KEY_PATH}")
                return

            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_KEY_PATH)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("Firebase Firestore Connected! (Ready)")
            
        except Exception as e:
            print(f"Connection Failed: {e}")

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
            print(f"Fetch Users Error: {e}")
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
            print(f"Get User Error: {e}")
            return None

    def register_user(self, user_id, name, balance, face_vector, pdpa_consent=False, role='user'):
        """ลงทะเบียนผู้ใช้ใหม่ หรืออัพเดตข้อมูลผู้ใช้เดิม

        Parameters:
            user_id (str|int): รหัสผู้ใช้ (จะถูกแปลงเป็น string)
            name (str)
            balance (float|str)
            face_vector (list|np.array): เวกเตอร์หน้า (จะเก็บเป็น list ลง Firestore)
            pdpa_consent (bool)
            role (str)

        Returns:
            bool: True ถ้าสำเร็จ, False ถ้ามีข้อผิดพลาด
        """
        if self.db is None:
            print("[DB] Not connected")
            return False

        try:
            doc_id = str(user_id).strip()
            user_ref = self.db.collection("users").document(doc_id)
            
            # ดึงข้อมูล existing ก่อน (ถ้ามี)
            existing_doc = user_ref.get()
            
            # เตรียมข้อมูลที่จะอัพเดต (รักษา fields เดิมไว้)
            update_data = {
                "user_id": doc_id,
                "name": name,
                "balance": float(balance),
                "face_vector": (np.array(face_vector).tolist() if hasattr(face_vector, 'tolist') else list(face_vector)),
                "is_active": True,
                "face_enrolled": True,
                "pdpa_consent": bool(pdpa_consent),
                "role": role,
            }
            
            # ถ้าเป็นครั้งแรก ให้เพิ่ม created_at
            if not existing_doc.exists:
                update_data["created_at"] = firestore.SERVER_TIMESTAMP
            
            # ใช้ update ไม่ใช่ set เพื่อรักษา fields เดิม (เช่น password)
            user_ref.update(update_data)
            print(f"User {doc_id} registered/updated successfully.")
            return True
            
        except Exception as e:
            print(f"Register User Error: {e}")
            return False

    def listen_for_updates(self, callback):
        """ตั้ง Listener แบบ realtime บน collection users (is_active==True)

        จะเรียก callback(users_list) เมื่อมีการเปลี่ยนแปลง
        คืนค่า listener registration (callable) ถ้าต้องการยกเลิก
        """
        if self.db is None:
            print("[DB] Not connected - cannot listen for updates")
            return None

        try:
            col_ref = self.db.collection("users").where("is_active", "==", True)

            def _on_snapshot(col_snapshot, changes, read_time):
                users = []
                for doc in col_snapshot:
                    data = doc.to_dict()
                    if "face_vector" in data:
                        try:
                            data["face_vector"] = np.array(data["face_vector"], dtype=np.float32)
                        except Exception:
                            # เก็บเป็น list ก็ได้
                            pass
                    users.append(data)

                try:
                    callback(users)
                except Exception as e:
                    print(f"Callback Error in listen_for_updates: {e}")

            # ลงทะเบียน listener
            listener = col_ref.on_snapshot(_on_snapshot)
            print("Listening for user updates (Firestore)")
            return listener
        except Exception as e:
            print(f"listen_for_updates Error: {e}")
            return None

    # ==========================================
    # 💰 Top-Up Section (เติมเงิน)
    # ==========================================

    def top_up_balance(self, user_id, amount):
        """เติมเงินให้ผู้ใช้

        Parameters:
            user_id (str|int): รหัสผู้ใช้
            amount (float): จำนวนเงินที่ต้องการเติม

        Returns:
            dict: {"success": True, "new_balance": ...} หรือ {"success": False, "error": ...}
        """
        if self.db is None:
            return {"success": False, "error": "ไม่ได้เชื่อมต่อฐานข้อมูล"}

        try:
            clean_id = str(user_id).strip()
            amount = float(amount)

            if amount <= 0:
                return {"success": False, "error": "จำนวนเงินต้องมากกว่า 0"}

            user_ref = self.db.collection("users").document(clean_id)
            snapshot = user_ref.get()

            if not snapshot.exists:
                return {"success": False, "error": f"ไม่พบผู้ใช้รหัส '{clean_id}'"}

            user_data = snapshot.to_dict()
            current_balance = float(user_data.get("balance", 0.0))
            new_balance = current_balance + amount

            user_ref.update({"balance": new_balance})

            # บันทึก transaction log
            self.db.collection("transactions").add({
                "user_id": clean_id,
                "user_name": user_data.get("name", ""),
                "type": "TOP_UP",
                "amount": amount,
                "old_balance": current_balance,
                "new_balance": new_balance,
                "status": "SUCCESS",
                "timestamp": datetime.datetime.now(),
                "server_timestamp": firestore.SERVER_TIMESTAMP,
            })

            print(f"เติมเงิน {amount:.2f} ให้ user {clean_id} สำเร็จ  ยอดใหม่: {new_balance:.2f}")
            return {"success": True, "new_balance": new_balance}

        except Exception as e:
            print(f"Top-up Error: {e}")
            return {"success": False, "error": str(e)}

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
            print(f"[CRITICAL ERROR] ไม่พบ User ID: '{user_ref.id}' ใน Database!")
            raise Exception(f"User ID '{user_ref.id}' not found")

        user_data = snapshot.to_dict()
        
        # 2. แปลงค่าเงินเป็น Float เพื่อความชัวร์
        try:
            current_balance = float(user_data.get("balance", 0.0))
            amount = float(amount)
        except ValueError:
            raise Exception("ข้อมูลยอดเงินใน Database ผิดพลาด (ไม่ใช่ตัวเลข)")

        print(f"[DEBUG] เงินที่มี: {current_balance:.2f} | ต้องจ่าย: {amount:.2f}")

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
        print(f"[START PAYMENT] User ID: {user_id}, Amount: {amount}")
        
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
            
            print(f"[SUCCESS] ตัดเงินสำเร็จ! New Balance: {result_data['new_balance']}")
            print("="*40 + "\n")
            
            # ส่ง Dictionary กลับไปให้ UI (ห้ามส่ง Tuple)
            return result_data

        except Exception as e:
            print(f"[FAILED] เกิดข้อผิดพลาด: {e}")
            print("="*40 + "\n")
            return {"success": False, "error": str(e)}