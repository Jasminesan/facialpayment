import numpy as np
class FaceMatcher:
    def __init__(self, db_handler):
        self.db = db_handler
        self.known_users = []
        self.reload_users() 

    def reload_users(self):
        print("🔄 Loading users for face recognition...")
        self.known_users = self.db.get_all_active_users()
        print(f"✅ Loaded {len(self.known_users)} users.")

    def load_users_from_data(self, users_list):
        """โหลดข้อมูลผู้ใช้จาก list ที่รับเข้ามา (เช่นจาก listener)

        users_list: list of dicts, face_vector อาจจะเป็น numpy array หรือ list
        """
        print("🔄 Loading users from provided data into FaceMatcher...")
        self.known_users = []
        for data in users_list:
            # ensure face_vector is numpy array for internal use
            fv = data.get("face_vector")
            try:
                data["face_vector"] = np.array(fv, dtype=np.float32)
            except Exception:
                # leave as-is if cannot convert
                pass
            self.known_users.append(data)
        print(f"✅ Loaded {len(self.known_users)} users into matcher.")

    def find_match(self, input_vector, threshold=0.6):
        if not self.known_users:
            print("⚠️ ไม่มีข้อมูล User ในระบบเลย! (Known Users is empty)")
            return {"found": False}

        if hasattr(input_vector, 'tolist'):
            input_vector = input_vector.tolist()
        vec1 = np.array(input_vector, dtype=np.float64)

        best_match = None
        max_similarity = -1

        for user in self.known_users:
            vec2 = np.array(user["face_vector"], dtype=np.float64)
            
            if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0: continue
            
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

            if similarity > max_similarity:
                max_similarity = similarity
                best_match = user
                best_match['similarity'] = float(similarity)

        if best_match and max_similarity > threshold:
            best_match["found"] = True
            return best_match
        else:
            return {"found": False}