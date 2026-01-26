import numpy as np

class FaceMatcher:
    def __init__(self, db_handler):
        self.db = db_handler
        self.known_users = []
        self._load_users()

    def _load_users(self):
        print("🔄 Loading users for face recognition...")
        self.known_users = self.db.get_all_active_users()
        print(f"✅ Loaded {len(self.known_users)} users.")

    def refresh_users(self):
        """โหลดข้อมูลผู้ใช้ใหม่ทั้งหมดจาก Database"""
        print("🔄 Refreshing Face Database...")
        new_users = self.db.get_all_active_users()
        
        if new_users:
            self.known_users = new_users
            print(f"✅ Database Updated! Total Users: {len(self.known_users)}")
        else:
            print("⚠️ Refresh failed or no users found. Keeping old data.")

    def find_match(self, input_vector, threshold=0.45):
        if not self.known_users:
            return {"found": False}

        best_match = None
        max_similarity = -1.0

        # แปลง input_vector เป็น numpy array ครั้งเดียว
        target_emb = np.array(input_vector)
        target_norm = np.linalg.norm(target_emb)

        for user in self.known_users:
            try:
                db_emb = np.array(user['face_vector'])
                db_norm = np.linalg.norm(db_emb)

                dot_product = np.dot(target_emb, db_emb)
                similarity = dot_product / (target_norm * db_norm)

                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = user
            except Exception:
                continue

        if max_similarity > threshold and best_match:
            return {
                "found": True,
                "user_id": best_match['user_id'],
                "name": best_match['name'],
                "balance": best_match.get('balance', 0.0),
                "similarity": float(max_similarity)
            }
        
        return {"found": False, "similarity": float(max_similarity)}