import numpy as np
from scipy.spatial.distance import cosine

class FaceMatcher:
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    def match(self, input_embedding, database_vectors):
        """
        input_embedding: list/array ของ vector หน้าปัจจุบัน
        database_vectors: list ของ dict [{"user_id": "...", "embedding": [...]}]
        """
        best_score = float("inf") # สำหรับ Cosine distance ยิ่งน้อยยิ่งดี (0=เหมือนเป๊ะ)
        best_match = None

        if input_embedding is None:
            return {"matched": False}

        for entry in database_vectors:
            db_emb = entry["embedding"]
            # คำนวณ Cosine Distance
            score = cosine(input_embedding, db_emb)
            
            if score < best_score:
                best_score = score
                best_match = entry["user_id"]

        # ตรวจสอบ Threshold
        # หมายเหตุ: Cosine Distance < threshold แปลว่าเหมือน
        if best_score < self.threshold:
            return {
                "matched": True,
                "user_id": best_match,
                "score": best_score
            }
        
        return {"matched": False, "score": best_score}