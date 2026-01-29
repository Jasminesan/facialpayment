import firebase_admin
from firebase_admin import credentials, firestore
import os
import datetime

key_path = "serviceAccountKey.json"

if not os.path.exists(key_path):
    print("❌ หาไฟล์ Key ไม่เจอ!")
    exit()

# Init Firebase
cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

print(f"🔥 กำลังทดสอบเขียนลง Project: {cred.project_id}")

# ลองเขียนข้อมูล
try:
    test_ref = db.collection("test_connection").document()
    test_ref.set({
        "message": "Hello Firestore",
        "timestamp": firestore.SERVER_TIMESTAMP,
        "local_time": str(datetime.datetime.now())
    })
    print("✅ เขียนข้อมูลสำเร็จ! ลองไปดูใน Collection 'test_connection'")
except Exception as e:
    print(f"❌ เขียนไม่เข้า: {e}")