# utils/style.py

APP_STYLE = """
/* =========================
   Global
========================= */
QWidget {
    background-color: #F7F8FA;
    color: #111827;
    font-family: "Pretendard";
    font-size: 13px;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollArea > QWidget {
    background: transparent;
}

/* =========================
   Typography helpers
   (setObjectName으로 적용)
========================= */
QLabel#Title {
    font-size: 22px;
    font-weight: 900;
    letter-spacing: -0.2px;
}

QLabel#H1 {
    font-size: 18px;
    font-weight: 900;
    letter-spacing: -0.2px;
}

QLabel#H2 {
    font-size: 15px;
    font-weight: 800;
}

QLabel#Muted {
    color: #6B7280;
    font-size: 12px;
}

QLabel#Mono {
    font-family: "Consolas";
    font-size: 12px;
    color: #111827;
}

/* =========================
   Status badges (Label)
========================= */
QLabel#Badge {
    background: #EEF2FF;
    color: #3730A3;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 800;
}

QLabel#BadgeSuccess {
    background: #ECFDF5;
    color: #065F46;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 900;
}

QLabel#BadgeWarn {
    background: #FFFBEB;
    color: #92400E;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 900;
}

QLabel#BadgeDanger {
    background: #FEF2F2;
    color: #991B1B;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 900;
}

/* =========================
   Buttons
========================= */
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 10px;
    padding: 8px 12px;
    font-weight: 700;
}

QPushButton:hover {
    background-color: #F3F4F6;
}

QPushButton:pressed {
    background-color: #E5E7EB;
}

QPushButton:disabled {
    color: #9CA3AF;
    background: #F9FAFB;
    border-color: #E5E7EB;
}

/* Primary / Danger 버튼은 objectName으로 */
QPushButton#PrimaryButton {
    background-color: #111827;
    color: #FFFFFF;
    border: 1px solid #111827;
    border-radius: 10px;
    padding: 9px 14px;
    font-weight: 900;
}

QPushButton#PrimaryButton:hover {
    background-color: #0B1220;
}

QPushButton#DangerButton {
    background-color: #B91C1C;
    color: #FFFFFF;
    border: 1px solid #B91C1C;
    border-radius: 10px;
    padding: 9px 14px;
    font-weight: 900;
}

/* =========================
   Inputs
========================= */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 10px;
    padding: 8px 10px;
    selection-background-color: #111827;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #111827;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox::down-arrow {
    image: none;
}

/* =========================
   Card / Panel
   - ResultCard가 QFrame이면 이 스타일이 바로 먹음
========================= */
QFrame#Card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
}

QFrame#Card:hover {
    border: 1px solid #D1D5DB;
}

QLabel#CardTitle {
    font-size: 14px;
    font-weight: 900;
}

QLabel#CardBody {
    color: #111827;
    line-height: 1.35;
}

/* =========================
   Divider
========================= */
QFrame#Divider {
    background: #E5E7EB;
    max-height: 1px;
    min-height: 1px;
}

/* =========================
   Simple table-like label
========================= */
QLabel#Key {
    color: #6B7280;
    font-weight: 800;
}

QLabel#Value {
    color: #111827;
    font-weight: 800;
}

/* =========================
   Analysis text (Detail page)
========================= */
QLabel#AnalysisText {
    background: transparent;        /*  배경 제거 */
    font-size: 14px;                
    line-height: 1.55;              /*  가독성*/
    color: #374151;
    padding: 2px 0px;               /* 줄 간 여백만 살짝 */
}

"""
