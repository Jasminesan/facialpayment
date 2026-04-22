import datetime
from firebase_admin import firestore

class PaymentService:
    def __init__(self, db_handler):
        self.db_handler = db_handler
        self.db = db_handler.db

    def process_payment(self, user_id, amount, items="Payment", shop_id="SHOP_01"):
        if self.db is None: return False, "Database Disconnected"

        try:
            user_ref = self.db.collection("users").document(str(user_id))
            txn_ref = self.db.collection("transactions").document()

            result = self._execute_payment_transaction(
                self.db.transaction(),
                user_ref,
                txn_ref,
                float(amount),
                shop_id,
                items
            )
            
            print(f"Payment Success! Txn ID: {result['receipt']['transaction_id']}")
            return True, result

        except Exception as e:
            print(f"Payment Failed: {e}")
            return False, str(e)

    @staticmethod
    @firestore.transactional
    def _execute_payment_transaction(transaction, user_ref, txn_ref, amount, shop_id, items):
        """Logic การตัดเงิน (Atomicity) - ยกมาจากโค้ดเดิมของคุณ"""
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