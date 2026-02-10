class AppConfig:
    # --- Color Palette ---
    COLOR_BG_MAIN = "#FFFFFF"       # พื้นหลังหลัก (ขาว)
    COLOR_TEXT_MAIN = "#000000"     # สีตัวหนังสือ (ดำ)
    COLOR_BG_GRAY = "#FFFFFF"       # พื้นหลังสีเทา

    
    COLOR_BTN_GREEN = "#8BC34A"     # สีเขียว (ปุ่ม OK)
    COLOR_BTN_RED = "#F44336"       # สีแดง (ปุ่ม Cancel)
    COLOR_BTN_TEXT = "#FFFFFF"      # สีตัวหนังสือปุ่ม (ขาว)

    # --- Font Settings ---
    FONT_FAMILY = "Arial"
    # --- Admin PIN (default) ---
    # Change this value in production or read from secure storage.
    ADMIN_PIN = "6767"


# ============================================================
# ระบบสองภาษา (TH / EN)
# ============================================================
_CURRENT_LANG = "ENG"

TEXTS = {
    # ---- Home ----
    "home.settings":        {"THA": "⚙  ตั้งค่า",            "ENG": "⚙  Settings"},
    "home.waiting":         {"THA": "📡  รอรับค่าจาก POS เพื่อชำระเงิน",
                             "ENG": "📡  Waiting for POS to process payment"},
    "home.register":        {"THA": "📝\nลงทะเบียน",         "ENG": "📝\nRegister"},
    "home.topup":           {"THA": "💰\nเติมเงิน",          "ENG": "💰\nTop Up"},

    # ---- Scan ----
    "scan.waiting":         {"THA": "กรุณารอสักครู่...",       "ENG": "Please wait..."},
    "scan.scanning":        {"THA": "กำลังสแกน...",           "ENG": "Scanning..."},
    "scan.look_camera":     {"THA": "กรุณามองที่กล้อง...",     "ENG": "Please look at the camera..."},
    "scan.checking":        {"THA": "กำลังตรวจสอบ...",        "ENG": "Checking..."},
    "scan.success":         {"THA": "สำเร็จ! (หน้าชัดเจน)",  "ENG": "Success! (Face clear)"},
    "scan.move_closer":     {"THA": "ขยับเข้ามาอีกนิด",      "ENG": "Move a bit closer"},
    "scan.come_closer":     {"THA": "เข้ามาใกล้ๆ หน่อย",     "ENG": "Come closer"},
    "scan.not_clear":       {"THA": "หน้าไม่ชัด",            "ENG": "Face not clear"},
    "scan.no_match":        {"THA": "ไม่พบข้อมูลที่ตรงกัน",   "ENG": "No match found"},

    # ---- Confirm ----
    "confirm.loading":      {"THA": "กำลังโหลด...",          "ENG": "Loading..."},
    "confirm.balance":      {"THA": "ยอดเงินคงเหลือ",        "ENG": "Total Balance"},
    "confirm.amount":       {"THA": "ยอดที่ต้องชำระ",         "ENG": "Payment Amount"},
    "confirm.ok":           {"THA": "✅  ยืนยันชำระเงิน",     "ENG": "✅  Confirm Pay"},
    "confirm.cancel":       {"THA": "❌  ยกเลิก",            "ENG": "❌  Cancel"},
    "confirm.processing":   {"THA": "⏳  กำลังดำเนินการ...",  "ENG": "⏳  Processing..."},
    "confirm.fail_title":   {"THA": "ชำระเงินล้มเหลว",       "ENG": "Payment Failed"},

    # ---- Success ----
    "success.title":        {"THA": "ชำระเงินสำเร็จ",        "ENG": "Payment Successful"},
    "success.balance":      {"THA": "ยอดคงเหลือ: {bal} บาท", "ENG": "Balance: {bal} THB"},

    # ---- No result ----
    "noresult.title":       {"THA": "ไม่พบข้อมูลผู้ใช้",      "ENG": "User Not Found"},

    # ---- Settings ----
    "settings.title":       {"THA": "⚙  ตั้งค่า",            "ENG": "⚙  Settings"},
    "settings.language":    {"THA": "ภาษา",                  "ENG": "Language"},
    "settings.back":        {"THA": "◀  กลับ",               "ENG": "◀  Back"},

    # ---- Register ----
    "reg.title":            {"THA": "📝  ลงทะเบียนผู้ใช้ใหม่", "ENG": "📝  Register New User"},
    "reg.back":             {"THA": "◀  กลับ",               "ENG": "◀  Back"},
    "reg.cam_group":        {"THA": "📷  สแกนใบหน้า",         "ENG": "📷  Face Scan"},
    "reg.cam_wait":         {"THA": "กำลังเชื่อมต่อกล้อง...",   "ENG": "Connecting camera..."},
    "reg.searching":        {"THA": "🔍  กำลังค้นหาใบหน้า...", "ENG": "🔍  Searching for face..."},
    "reg.found":            {"THA": "✅  ตรวจพบใบหน้าแล้ว — พร้อมบันทึก",
                             "ENG": "✅  Face detected — Ready to save"},
    "reg.form_group":       {"THA": "📋  ข้อมูลผู้ใช้",        "ENG": "📋  User Info"},
    "reg.uid":              {"THA": "รหัสผู้ใช้ :",             "ENG": "User ID :"},
    "reg.name":             {"THA": "ชื่อ :",                  "ENG": "Name :"},
    "reg.balance":          {"THA": "ยอดเงินเริ่มต้น :",       "ENG": "Initial Balance :"},
    "reg.pdpa_group":       {"THA": "🔒  ความยินยอม PDPA",    "ENG": "🔒  PDPA Consent"},
    "reg.pdpa_info":        {"THA": "ระบบจะจัดเก็บเฉพาะเวกเตอร์ตัวเลขของใบหน้า (Face Embedding)\n"
                                    "ไม่มีการบันทึกรูปภาพใบหน้า  ข้อมูลใช้เพื่อยืนยันตัวตนในการชำระเงินเท่านั้น\n"
                                    "ท่านสามารถขอลบข้อมูลได้ตลอดเวลา",
                             "ENG": "The system stores only facial numerical vectors (Face Embedding).\n"
                                    "No facial images are saved. Data is used solely for payment verification.\n"
                                    "You may request data deletion at any time."},
    "reg.pdpa_check":       {"THA": "ข้าพเจ้ายินยอมให้จัดเก็บข้อมูลใบหน้าตาม พ.ร.บ. คุ้มครองข้อมูลส่วนบุคคล",
                             "ENG": "I consent to facial data collection under the PDPA"},
    "reg.save":             {"THA": "✅  บันทึก",             "ENG": "✅  Save"},
    "reg.clear":            {"THA": "🔄  ล้างข้อมูล",         "ENG": "🔄  Clear"},

    # ---- Top-up ----
    "topup.title":          {"THA": "💰  เติมเงิน",           "ENG": "💰  Top Up"},
    "topup.back":           {"THA": "◀  กลับ",               "ENG": "◀  Back"},
    "topup.search_group":   {"THA": "🔎  ค้นหาผู้ใช้",        "ENG": "🔎  Search User"},
    "topup.search_hint":    {"THA": "กรอกรหัสผู้ใช้ (User ID)","ENG": "Enter User ID"},
    "topup.search_btn":     {"THA": "🔍  ค้นหา",             "ENG": "🔍  Search"},
    "topup.info_group":     {"THA": "👤  ข้อมูลผู้ใช้",        "ENG": "👤  User Info"},
    "topup.name":           {"THA": "ชื่อ :",                  "ENG": "Name :"},
    "topup.uid":            {"THA": "รหัสผู้ใช้ :",             "ENG": "User ID :"},
    "topup.balance":        {"THA": "ยอดเงินคงเหลือ :",       "ENG": "Current Balance :"},
    "topup.amount_group":   {"THA": "💳  เติมเงิน",           "ENG": "💳  Top Up"},
    "topup.quick":          {"THA": "เลือกจำนวนเงินด่วน :",   "ENG": "Quick amounts :"},
    "topup.custom":         {"THA": "หรือกรอกจำนวนเอง :",     "ENG": "Or enter amount :"},
    "topup.do":             {"THA": "💰  เติมเงิน",           "ENG": "💰  Top Up"},
}


def get_lang():
    """คืนค่าภาษาปัจจุบัน"""
    return _CURRENT_LANG


def set_lang(lang: str):
    """ตั้งค่าภาษา ('THA' หรือ 'ENG')"""
    global _CURRENT_LANG
    _CURRENT_LANG = lang


def t(key: str, **kwargs) -> str:
    """ดึงข้อความตามภาษาปัจจุบัน  ใช้ t('home.settings')"""
    entry = TEXTS.get(key, {})
    txt = entry.get(_CURRENT_LANG, entry.get("THA", key))
    if kwargs:
        txt = txt.format(**kwargs)
    return txt