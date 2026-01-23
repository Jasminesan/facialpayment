import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np
import os
from config.settings import Config
import datetime
import time

class DatabaseHandler:
    def __init__(self):
        self.db = None
        self.connect()

    def connect(self):
        try:
            if not os.path.exists(Config.FIREBASE_KEY_PATH):
                print(f"❌ Error: Not Found Key at: {Config.FIREBASE_KEY_PATH}")
                print("(Check .env file or location of serviceAccountKey.json)")
                return

            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_KEY_PATH)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("✅ Firebase Firestore Connected!")
            
        except Exception as e:
            print(f"❌ Firebase Connection Failed: {e}")
            self.db = None

    def register_user(self, user_id, name, balance, vector, consent_pdpa):
        if self.db is None: return False

        try:
            # Ensure vector is a list of floats
            if hasattr(vector, 'tolist'):
                vector = vector.tolist()
            vector = [float(x) for x in vector]

            user_data = {
                "user_id": str(user_id),
                "name": str(name),
                "balance": float(balance),
                "face_vector": vector,
                "consent_pdpa": bool(consent_pdpa),
                "is_active": True,
                "created_at": firestore.SERVER_TIMESTAMP
            }

            #   Save as Collection 'users'  ID Name Document
            self.db.collection("users").document(str(user_id)).set(user_data)
            
            print(f"✅ Saved user '{name}' to Firestore!")
            return True

        except Exception as e:
            print(f"❌ REGISTER ERROR: {e}")
            return False

    # Process payment by deducting amount from user's balance    
        
    def process_payment(self, user_id, amount):
        if self.db is None: "No COnnection"
        try:
            user_ref = self.db.collection("users").document(str(user_id))
            user_doc = user_ref.get()

            if not user_doc.exists:
                print(f"❌ User ID {user_id} not found.")
                return False

            user_data = user_doc.to_dict()
            current_balance = user_data.get("balance", 0.0)

            if current_balance < amount:
                print(f"❌ Insufficient balance for User ID {user_id}.")
                return False

            new_balance = current_balance - amount
            user_ref.update({"balance": new_balance})

            print(f"✅ Payment of {amount} processed for User ID {user_id}. New balance: {new_balance}")
            return True

        except Exception as e:
            print(f"❌ PAYMENT ERROR: {e}")
            return False
    
    def save_transaction(self, user_id, amount, status):
        try:
            txn_id = int(time.time()) 
            timestamp = datetime.datetime.now().isoformat()
            
            txn_data = {
                "TXN_ID": txn_id,
                "USER_ID": int(user_id),
                "SHOP_ID": "SHOP_IPC_01", 
                "AMOUNT": float(amount),
                "STATUS": status,
                "TIMESTAMP": timestamp
            }
            
            self.db.collection("transactions").document(str(txn_id)).set(txn_data)
            print(f"📝 Transaction Saved: {status}")
            
        except Exception as e:
            print(f"❌ Save Transaction Error: {e}")

    def get_user_by_face(self, input_vector, threshold=0.6):
        if self.db is None: return {"found": False}

        try:
            if hasattr(input_vector, 'tolist'):
                input_vector = input_vector.tolist()
            
            vec1 = np.array(input_vector, dtype=np.float64)
            best_match = None
            max_similarity = -1

            docs = self.db.collection("users").stream()

            for doc in docs:
                data = doc.to_dict()
                if "face_vector" not in data: continue

                vec2 = np.array(data["face_vector"], dtype=np.float64)

                if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
                    continue
                    
                similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = {
                        "id": data.get("id"),
                        "name": data.get("name"), 
                        "balance": data.get("balance"),
                        "similarity": float(similarity)
                    }

            if best_match and max_similarity > threshold:
                best_match["found"] = True
                return best_match
            else:
                return {"found": False}

        except Exception as e:
          print(f"❌ Search Error: {e}")
          return {"found": False}