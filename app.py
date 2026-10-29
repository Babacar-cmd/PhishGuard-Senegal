"""
PhishGuard Senegal - detection de phishing Orange Money & Wave
Babacar MBOW - ESTM Dakar 2026-2027
Variante coloree (bleu et vert ESTM). Design refait (CSS + affichage). La logique (auth, extraction, modele) est inchangee.
"""
import streamlit as st, sys, os, pickle, re, base64, io, json, hashlib, html, hmac, secrets, time
from urllib.parse import urlparse
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, '..', 'src'))
try:
    from feature_extraction import extract_features as extract_local, features_to_vector as fv_local
    import joblib
    LOCAL_MODE=True
except:
    LOCAL_MODE=False
import requests


st.set_page_config(page_title="PhishGuard Senegal - ESTM", page_icon="🛡️", layout="wide")

def get_b64(p):
    try:
        if os.path.exists(p):
            with open(p,"rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return ""
estm_b64=get_b64(os.path.join(BASE_DIR,"estm_logo.png")) or get_b64("estm_logo.png")
babacar_b64=get_b64(os.path.join(BASE_DIR,"Babacar_Mbow.jpg")) or get_b64("Babacar_Mbow.jpg")

# ===== AUTHENTIFICATION SECURISEE =====
# - mots de passe : PBKDF2-SHA256 avec sel (les anciens hash SHA-256 restent valides et sont migres a la connexion)
# - mot de passe oublie : code de recuperation donne a la creation du compte (plus d'email devinable)
# - blocage 60 s apres 5 echecs (par session)
USERS_FILE = os.path.join(BASE_DIR, "users.json")
PBKDF2_ITER = 200_000
MIN_PWD = 8
DEFAULT_PWD = "admin123"
MAX_FAILS = 5
LOCK_SECONDS = 60

def hash_pwd(p, salt=None):
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", p.encode("utf-8"), salt, PBKDF2_ITER)
    return f"pbkdf2${PBKDF2_ITER}${salt.hex()}${dk.hex()}"

def verify_pwd(p, stored):
    try:
        if stored.startswith("pbkdf2$"):
            _, it, salt, dk = stored.split("$")
            calc = hashlib.pbkdf2_hmac("sha256", p.encode("utf-8"), bytes.fromhex(salt), int(it)).hex()
            return hmac.compare_digest(calc, dk)
        return hmac.compare_digest(hashlib.sha256(p.encode("utf-8")).hexdigest(), stored)  # ancien format
    except Exception:
        return False

def new_recovery_code():
    return "-".join(secrets.token_hex(2).upper() for _ in range(4))

def save_users(u):
    try:
        json.dump(u, open(USERS_FILE, "w", encoding="utf-8"), indent=2)
    except Exception:
        pass

def load_users():
    if not os.path.exists(USERS_FILE):
        pwd = secrets.token_urlsafe(9)
        users = {"admin": {"email": "admin@estm.sn", "password": hash_pwd(pwd), "nom": "admin"}}
        save_users(users)
        print(f"[PhishGuard] Compte admin cree. Mot de passe : {pwd}")
        return users
    try:
        return json.load(open(USERS_FILE, "r", encoding="utf-8")) or {}
    except Exception:
        return {}

def register_user(username, email, password):
    username = username.strip(); email = email.strip()
    users = load_users()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", username): return False, "Nom d'utilisateur invalide (3 à 30 caractères : lettres, chiffres, _ . -)", None
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email): return False, "Email invalide", None
    if username in users: return False, "Ce nom d'utilisateur est déjà pris", None
    if len(password) < MIN_PWD: return False, f"Mot de passe trop court ({MIN_PWD} caractères minimum)", None
    code = new_recovery_code()
    users[username] = {"email": email, "password": hash_pwd(password), "nom": username, "recovery": hash_pwd(code)}
    save_users(users)
    return True, "Compte créé", code

def check_login(username, password):
    users = load_users()
    u = users.get(username)
    if not u or not verify_pwd(password, u.get("password", "")):
        return False, "Identifiants incorrects"
    changed = False
    if not u["password"].startswith("pbkdf2$"):           # migration de l'ancien SHA-256
        u["password"] = hash_pwd(password); changed = True
    if changed:
        save_users(users)
    return True, "Connexion réussie"

def reset_password(username, code, new_password):
    users = load_users()
    u = users.get(username.strip())
    code = code.strip().upper()
    if not u or not u.get("recovery") or not verify_pwd(code, u["recovery"]):
        return False, "Nom d'utilisateur ou code de récupération incorrect", None
    if len(new_password) < MIN_PWD: return False, f"Mot de passe trop court ({MIN_PWD} caractères minimum)", None
    new_code = new_recovery_code()
    u["password"] = hash_pwd(new_password); u["recovery"] = hash_pwd(new_code)
    save_users(users)
    return True, "Mot de passe réinitialisé", new_code

def change_password(username, old_password, new_password):
    users = load_users()
    u = users.get(username)
    if not u or not verify_pwd(old_password, u.get("password", "")): return False, "Mot de passe actuel incorrect"
    if len(new_password) < MIN_PWD: return False, f"Mot de passe trop court ({MIN_PWD} caractères minimum)"
    u["password"] = hash_pwd(new_password)
    save_users(users)
    return True, "Mot de passe modifié"

def regenerate_recovery(username, password):
    users = load_users()
    u = users.get(username)
    if not u or not verify_pwd(password, u.get("password", "")): return False, "Mot de passe incorrect", None
    code = new_recovery_code()
    u["recovery"] = hash_pwd(code)
    save_users(users)
    return True, "Nouveau code créé", code

def lock_remaining():
    return max(0, int(st.session_state.get("locked_until", 0) - time.time()))

def register_fail():
    st.session_state.fails = st.session_state.get("fails", 0) + 1
    if st.session_state.fails >= MAX_FAILS:
        st.session_state.locked_until = time.time() + LOCK_SECONDS
        st.session_state.fails = 0

for _k, _v in {"authenticated": False, "username": "", "url_input_key": "", "pending_code": "", "default_pwd": False, "fails": 0, "locked_until": 0}.items():
    if _k not in st.session_state: st.session_state[_k] = _v


# ==================== STYLE ====================
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --ink: #0E2238;
    --blue: #1B4F9C;
    --green: #0F8A55;
    --green-dark: #0B6B43;
    --red: #B3261E;
    --amber: #8A5200;
    --paper: #F2F5F8;
    --surface: #FFFFFF;
    --line: #D8DFE8;
    --line-strong: #BCC7D4;
    --muted: #54667B;
    --red-bg: #FDEEEC;
    --green-bg: #E8F5EE;
    --amber-bg: #FFF3DC;
    --blue-bg: #E9F0FA;
    --display: 'Bricolage Grotesque', 'IBM Plex Sans', system-ui, sans-serif;
    --body: 'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
    --mono: 'IBM Plex Mono', ui-monospace, 'SFMono-Regular', Menlo, monospace;
}

/* ---------- Base ---------- */
.stApp, [data-testid="stAppViewContainer"] { background: var(--paper); font-family: var(--body) !important; color: var(--ink); }
.stApp p, .stApp li, .stApp label, .stApp textarea, .stApp input, .stApp button { font-family: var(--body) !important; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding-top: 1.4rem !important; padding-bottom: 3rem !important; }
.stApp p { line-height: 1.55; }

/* ---------- Top bar ---------- */
.pg-bar { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 4px 0 18px; margin-bottom: 26px; border-bottom: 1px solid var(--line); }
.pg-brand { display: flex; align-items: center; gap: 10px; }
.pg-mark { display: inline-flex; width: 34px; height: 34px; align-items: center; justify-content: center; background: var(--ink); border-radius: 9px; }
.pg-mark svg { width: 20px; height: 20px; }
.pg-word { font-family: var(--display); font-weight: 700; font-size: 21px; letter-spacing: -0.01em; color: var(--ink); }
.pg-school { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--muted); font-weight: 500; }
.pg-school img { height: 32px; display: block; background: #fff; border-radius: 8px; padding: 3px 7px; border: 1px solid var(--line); }
.pg-user { text-align: right; font-size: 13.5px; color: var(--muted); }
.pg-user b { color: var(--ink); font-weight: 600; }
.st-key-bar { border-bottom: 1px solid var(--line); padding-bottom: 14px; margin-bottom: 26px; }
.st-key-bar [data-testid="stHorizontalBlock"] { align-items: center; }

/* ---------- Auth hero ---------- */
.pg-hero { background: var(--ink); color: #fff; border-radius: 16px; padding: 44px 44px 36px; min-height: 560px; display: flex; flex-direction: column; }
.pg-h1 { font-family: var(--display); font-weight: 800; font-size: clamp(32px, 4.2vw, 50px); line-height: 1.02; letter-spacing: -0.025em; margin: 0 0 16px; color: #fff; }
.pg-lead { font-size: 17px; line-height: 1.5; color: #C3D1E2; max-width: 44ch; margin: 0 0 30px; }
.pg-sms { background: #fff; color: var(--ink); border-radius: 14px; padding: 16px 18px 18px; max-width: 520px; }
.pg-sms-from { font-size: 12.5px; color: var(--muted); font-weight: 600; margin-bottom: 8px; }
.pg-sms-body { font-size: 14.5px; line-height: 1.55; }
.pg-sms-body code { font-family: var(--mono); font-size: 12.5px; background: transparent; color: var(--ink); overflow-wrap: anywhere; padding: 0; display: block; margin-top: 8px; }
.pg-anat { margin: 18px 0 0; padding: 0; list-style: none; max-width: 520px; }
.pg-anat li { display: flex; gap: 12px; align-items: flex-start; font-size: 14px; line-height: 1.5; color: #D6E0EC; padding: 7px 0; }
.pg-anat li span.sw { flex: none; margin-top: 3px; min-width: 16px; height: 16px; border-radius: 4px; }
.pg-anat li b { color: #fff; font-weight: 600; font-family: var(--mono); font-size: 12.5px; }
.pg-hero-foot { margin-top: auto; padding-top: 28px; font-size: 13.5px; color: #9FB2C8; line-height: 1.6; }
.pg-hero-foot .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin: 0 6px 0 2px; vertical-align: baseline; }

/* URL highlighting (shared by SMS example and results) */
.u-fake { background: #FFE6B8; color: #5F3800; text-decoration: line-through; text-decoration-color: #A86400; text-decoration-thickness: 1.5px; border-radius: 3px; padding: 0 2px; }
.u-ip { background: #F8CFCB; color: #7C1812; font-weight: 600; border-radius: 3px; padding: 0 2px; }
.u-warn { text-decoration: underline wavy #B3261E; text-underline-offset: 4px; text-decoration-thickness: 1.5px; }

/* ---------- Form card ---------- */
[data-testid="stVerticalBlockBorderWrapper"], .st-key-authcard, .st-key-inputcard { background: var(--surface); border: 1px solid var(--line) !important; border-radius: 16px !important; box-shadow: none !important; }
.st-key-authcard, .st-key-inputcard { padding: 22px 24px 20px !important; }
.st-key-authcard { padding: 22px 20px 20px !important; }
.fh { font-family: var(--display); font-weight: 700; font-size: 24px; letter-spacing: -0.015em; color: var(--ink); margin: 2px 0 2px; }
.fs { font-size: 14px; color: var(--muted); margin-bottom: 14px; }

[role="tablist"] { gap: 18px !important; border-bottom: 1px solid var(--line) !important; }
[role="tab"] { padding: 10px 0 12px !important; height: auto !important; background: transparent !important; color: var(--muted) !important; }
[role="tab"] p { font-weight: 600 !important; font-size: 14px !important; white-space: nowrap; color: var(--muted) !important; }
[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] p { color: var(--ink) !important; }
[role="tab"]:hover p { color: var(--ink) !important; }
[role="tab"] .react-aria-SelectionIndicator, [data-baseweb="tab-highlight"] { background: var(--ink) !important; height: 2px !important; }
[data-baseweb="tab-border"] { display: none; }
[role="tabpanel"] { padding-top: 18px; }

[data-testid="stWidgetLabel"] p { font-size: 13.5px; font-weight: 600; color: var(--ink); }
[data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"], div[data-baseweb="input"], div[data-baseweb="textarea"], [data-testid="stSelectbox"] div[data-baseweb="select"] > div, [data-testid="stSelectbox"] div[role="group"] {
    border-radius: 8px !important; border: 1px solid var(--line-strong) !important; background: #fff !important;
}
[data-testid="stTextInputRootElement"]:focus-within, [data-testid="stTextAreaRootElement"]:focus-within, div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within, [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within, [data-testid="stSelectbox"] div[role="group"]:focus-within {
    border-color: var(--blue) !important; box-shadow: 0 0 0 3px rgba(27,79,156,0.18) !important;
}
.stTextInput input, .stTextArea textarea { font-size: 14.5px !important; color: var(--ink) !important; }
.stTextArea textarea, .st-key-url_input_key input { font-family: var(--mono) !important; font-size: 13.5px !important; }
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: #8695A7 !important; }

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button {
    background: var(--ink) !important; color: #fff !important; border: 1px solid var(--ink) !important; border-radius: 8px !important;
    padding: 11px 20px !important; min-height: 46px; font-weight: 600 !important; font-size: 15px !important; box-shadow: none !important;
    transition: background 0.15s ease, border-color 0.15s ease;
}
.stButton > button p, .stDownloadButton > button p { color: #fff !important; font-weight: 600 !important; font-size: 15px !important; }
.stButton > button:hover, .stDownloadButton > button:hover { background: var(--blue) !important; border-color: var(--blue) !important; }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible { outline: 3px solid rgba(27,79,156,0.4) !important; outline-offset: 2px; }
.st-key-logout button, .stDownloadButton > button { background: transparent !important; color: var(--ink) !important; border: 1px solid var(--line-strong) !important; }
.st-key-logout button p, .stDownloadButton > button p { color: var(--ink) !important; }
.st-key-logout button:hover, .stDownloadButton > button:hover { background: var(--ink) !important; border-color: var(--ink) !important; }
.st-key-logout button:hover p, .stDownloadButton > button:hover p { color: #fff !important; }

/* ---------- Notes ---------- */
.pg-note { display: flex; gap: 10px; align-items: flex-start; border-radius: 8px; padding: 10px 14px; font-size: 13.5px; line-height: 1.5; border-left: 3px solid var(--blue); background: var(--blue-bg); color: #163764; margin: 4px 0 10px; }
.pg-note b { font-weight: 600; }
.pg-note.warn { border-left-color: #C77700; background: var(--amber-bg); color: #5C3700; }
.pg-note code { font-family: var(--mono); font-size: 12.5px; word-break: break-all; background: transparent; padding: 0; color: inherit; }

/* ---------- Page title ---------- */
.pg-title { font-family: var(--display); font-weight: 800; font-size: clamp(28px, 3.6vw, 38px); letter-spacing: -0.025em; line-height: 1.05; margin: 0 0 8px; color: var(--ink); }
.pg-intro { color: var(--muted); font-size: 16px; margin: 0 0 22px; max-width: 60ch; }

/* ---------- Verdict ---------- */
.vd { border-radius: 16px; overflow: hidden; background: var(--surface); border: 1px solid var(--line); margin: 22px 0 14px; }
.vd-top { display: flex; align-items: center; gap: 16px; padding: 20px 24px; color: #fff; }
.vd-bad .vd-top { background: var(--red); }
.vd-ok .vd-top { background: var(--green-dark); }
.vd-icon { flex: none; width: 48px; height: 48px; border-radius: 12px; background: rgba(255,255,255,0.18); display: flex; align-items: center; justify-content: center; }
.vd-icon svg { width: 26px; height: 26px; }
.vd-text { flex: 1; min-width: 0; }
.vd-title { font-family: var(--display); font-weight: 800; font-size: clamp(24px, 3vw, 32px); letter-spacing: -0.02em; line-height: 1.05; }
.vd-sub { font-size: 14.5px; opacity: 0.92; margin-top: 4px; }
.vd-score { text-align: right; flex: none; }
.vd-num { font-family: var(--display); font-weight: 800; font-size: 34px; letter-spacing: -0.02em; line-height: 1; }
.vd-cap { font-size: 12.5px; opacity: 0.9; margin-top: 4px; }
.vd-meter { margin: 18px 24px 0; height: 8px; border-radius: 99px; background: #E5EAF0; overflow: hidden; }
.vd-meter span { display: block; height: 100%; border-radius: 99px; transform-origin: left; animation: fillbar 0.9s cubic-bezier(0.2, 0.8, 0.2, 1) both; }
.vd-bad .vd-meter span { background: var(--red); }
.vd-ok .vd-meter span { background: var(--green); }
@keyframes fillbar { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.vd-meter-cap { display: flex; justify-content: space-between; margin: 6px 24px 0; font-size: 12px; color: var(--muted); }
.vd-url { margin: 16px 24px 20px; padding: 14px 16px; background: var(--paper); border-radius: 10px; }
.vd-url-label { font-size: 12.5px; font-weight: 600; color: var(--muted); margin-bottom: 6px; }
.vd-url code { font-family: var(--mono); font-size: 14px; color: var(--ink); word-break: break-all; background: transparent; padding: 0; line-height: 1.7; }
.vd-legend { display: flex; flex-wrap: wrap; gap: 6px 18px; margin-top: 10px; font-size: 12.5px; color: var(--muted); }
.vd-legend span.k { display: inline-block; min-width: 14px; height: 12px; margin-right: 6px; vertical-align: -1px; border-radius: 3px; }

/* ---------- Actions + contacts ---------- */
.pg-card { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 20px 22px; margin-bottom: 14px; }
.pg-card h3, .sec-h { font-family: var(--display); font-weight: 700; font-size: 20px; letter-spacing: -0.015em; margin: 0 0 12px; color: var(--ink); padding: 0; }
.pg-steps { margin: 0; padding: 0; list-style: none; counter-reset: s; }
.pg-steps li { counter-increment: s; display: flex; gap: 14px; padding: 9px 0; font-size: 15px; line-height: 1.5; border-top: 1px solid var(--line); }
.pg-steps li:first-child { border-top: 0; padding-top: 2px; }
.pg-steps li::before { content: counter(s); flex: none; width: 24px; height: 24px; border-radius: 50%; background: var(--ink); color: #fff; font-weight: 600; font-size: 13px; display: flex; align-items: center; justify-content: center; margin-top: 1px; }
.pg-steps li b { font-weight: 600; }
.pg-contacts { display: grid; grid-template-columns: 1fr 1fr; gap: 0 28px; }
.pg-contact { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; padding: 10px 0; border-top: 1px solid var(--line); font-size: 14.5px; }
.pg-contact small { display: block; color: var(--muted); font-size: 12.5px; }
.pg-contact .num { font-family: var(--mono); font-weight: 500; font-size: 14px; color: var(--ink); text-align: right; word-break: break-all; }
.pg-share { display: flex; align-items: center; justify-content: center; gap: 10px; background: var(--green-dark); color: #fff !important; text-decoration: none !important; border-radius: 8px; padding: 13px 18px; font-weight: 600; font-size: 15px; transition: background 0.15s ease; }
.pg-share:hover { background: var(--green); }
.pg-share:focus-visible { outline: 3px solid rgba(15,138,85,0.4); outline-offset: 2px; }
.pg-share svg { width: 18px; height: 18px; }
.pg-share-help { font-size: 13.5px; color: var(--muted); margin: 0 0 10px; }

/* ---------- Technical analysis ---------- */
.sec-h { margin-top: 36px; font-size: 24px; }
.sec-sub { color: var(--muted); font-size: 14.5px; margin: -6px 0 14px; }
[data-testid="stMetric"] { background: var(--paper); border-radius: 10px; padding: 12px 14px; margin-bottom: 8px; }
[data-testid="stMetricLabel"] p { font-size: 12.5px !important; color: var(--muted) !important; font-weight: 500 !important; }
[data-testid="stMetricValue"] { font-family: var(--display) !important; font-weight: 700 !important; font-size: 24px !important; color: var(--ink); }
[data-testid="stMetricDelta"] { font-size: 12.5px; }
[data-testid="stExpander"] { border: 1px solid var(--line) !important; border-radius: 12px !important; background: var(--surface); }
[data-testid="stExpander"] summary p { font-weight: 600; font-size: 14.5px; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }

/* ---------- Footer ---------- */
.pg-foot { display: flex; align-items: center; gap: 14px; margin-top: 52px; padding-top: 20px; border-top: 1px solid var(--line); font-size: 13px; color: var(--muted); line-height: 1.55; }
.pg-foot img.av { width: 38px; height: 38px; border-radius: 50%; object-fit: cover; object-position: top; flex: none; }
.pg-foot b { color: var(--ink); font-weight: 600; }

/* ---------- Small screens ---------- */
@media (max-width: 720px) {
    .pg-hero { padding: 28px 22px; min-height: 0; }
    .vd-top { flex-wrap: wrap; padding: 18px; }
    .vd-score { text-align: left; width: 100%; }
    .vd-meter, .vd-meter-cap, .vd-url { margin-left: 18px; margin-right: 18px; }
    .pg-contacts { grid-template-columns: 1fr; }
    .pg-school span { display: none; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
}

/* ===== Variante colorée (couleurs ESTM : bleu et vert) ===== */
:root { --blue: #1B4F9C; --green: #12935A; --paper: #E9F1FB; --blue-bg: #E3EDFB; --line: #CBD9EC; --line-strong: #A9BED8; }
.stApp, [data-testid="stAppViewContainer"] { background: linear-gradient(170deg, #DDEBFB 0%, #EEF5FC 45%, #E7F5EE 100%) fixed; }
.pg-bar { border-bottom: 0; position: relative; }
.pg-bar::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 3px; border-radius: 3px; background: linear-gradient(90deg, #1B4F9C, #12935A); }
.st-key-bar { border-bottom: 3px solid transparent; border-image: linear-gradient(90deg, #1B4F9C, #12935A) 1; }
.pg-mark { background: linear-gradient(135deg, #1B4F9C, #12935A); }
.pg-word, .pg-title { color: #123D7E; }
.pg-hero { background: linear-gradient(155deg, #123F8C 0%, #1B4F9C 55%, #12935A 135%); box-shadow: 0 18px 40px rgba(27,79,156,0.25); }
.pg-lead { color: #DCE8FA; }
.pg-anat li { color: #E6EEFA; }
.pg-hero-foot { color: #C9DAF2; }
.st-key-authcard, .st-key-inputcard { border-top: 4px solid #1B4F9C !important; box-shadow: 0 10px 30px rgba(27,79,156,0.10) !important; }
.st-key-inputcard { border-top-color: #12935A !important; }
.fh { color: #123D7E; }
[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] p { color: #1B4F9C !important; }
[role="tab"] .react-aria-SelectionIndicator, [data-baseweb="tab-highlight"] { background: #12935A !important; height: 3px !important; }
.stButton > button { background: linear-gradient(100deg, #1B4F9C 0%, #1F6BBF 55%, #12935A 130%) !important; border-color: #1B4F9C !important; }
.stButton > button:hover { background: linear-gradient(100deg, #153F7E, #12935A) !important; border-color: #153F7E !important; }
.st-key-logout button, .stDownloadButton > button { background: #fff !important; color: #1B4F9C !important; border: 1.5px solid #1B4F9C !important; }
.st-key-logout button p, .stDownloadButton > button p { color: #1B4F9C !important; }
.st-key-logout button:hover, .stDownloadButton > button:hover { background: #1B4F9C !important; }
.pg-note { border-left-color: #12935A; background: #E3F4EB; color: #0B5A39; }
.pg-note.warn { border-left-color: #C77700; background: var(--amber-bg); color: #5C3700; }
.pg-card { border-top: 4px solid #1B4F9C; box-shadow: 0 6px 20px rgba(27,79,156,0.07); }
.pg-card h3 { color: #123D7E; }
.pg-steps li::before { background: #1B4F9C; }
.pg-contact .num { color: #1B4F9C; font-weight: 600; }
.sec-h { color: #123D7E; position: relative; padding-bottom: 10px; }
.sec-h::after { content: ""; position: absolute; left: 0; bottom: 0; width: 56px; height: 4px; border-radius: 4px; background: linear-gradient(90deg, #1B4F9C, #12935A); }
.sec-sub { margin-top: 6px; }
[data-testid="stMetric"] { background: #fff; border: 1px solid var(--line); border-left: 4px solid #1B4F9C; }
[data-testid="stMetricValue"] { color: #1B4F9C; }
[data-testid="stExpander"] { border-color: var(--line) !important; }
.pg-foot { border-top: 3px solid transparent; border-image: linear-gradient(90deg, #1B4F9C, #12935A) 1; }
.pg-school img { border-color: var(--line); }
.vd { box-shadow: 0 14px 34px rgba(14,34,56,0.12); border: 0; }

"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

MARQUES=["orange","orangemoney","orange-money","wave","wave.com"]
def est_autorisee(url):
    l=url.lower()
    for m in MARQUES:
        if m in l:
            return True, "Orange Money" if "orange" in m else "Wave"
    return False, None
def extraire_urls_sms(txt):
    pat=r'(https?://[^\s\n]+|www\.[^\s\n]+|[a-zA-Z0-9.-]+\.(?:com|sn|net|org)/[^\s\n]*|(?:orange|wave)[^\s\n]*\.[^\s\n]+)'
    urls=re.findall(pat, txt, re.IGNORECASE)
    clean=[u.strip().rstrip('.,!?)') for u in urls if len(u.strip())>5]
    if not clean and any(m in txt.lower() for m in MARQUES):
        m=re.search(r'((?:https?://)?[^\s]*?(?:orange|wave)[^\s]*)', txt, re.IGNORECASE)
        if m:
            clean=[m.group(1)]
    return clean
def extract_features(url):
    if LOCAL_MODE:
        try:
            return extract_local(url)
        except:
            pass
    try:
        parsed=urlparse(url if url.startswith('http') else 'http://'+url)
        host=parsed.netloc or parsed.path.split('/')[0]
        d={}
        d['longueur_url']=len(url); d['longueur_hostname']=len(host); d['nb_points']=url.count("."); d['nb_tirets']=url.count("-")
        d['nb_chiffres']=sum(c.isdigit() for c in url); d['nb_symboles']=url.count("@")+url.count("?")+url.count("&")+url.count("=")
        d['presence_ip']=1 if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", url) else 0
        d['presence_arobase']=1 if "@" in url else 0; d['nb_arobase']=url.count("@")
        d['presence_https']=1 if parsed.scheme=="https" else 0; d['nb_sous_domaines']=host.count(".")-1 if host.count(".")>1 else 0
        d['mot_banking']=1 if any(w in url.lower() for w in ["orange","wave","money"]) else 0
        d['mot_suspect']=1 if any(w in url.lower() for w in ["securite","verif","bonus","login","urgent","blocage","gain","recompense","felicitation"]) else 0
        d['age_domaine']=5 if d['presence_ip']==1 else (10 if d['nb_tirets']>=2 and d['mot_suspect']==1 else 4000)
        d['nb_tirets_score']=d['nb_tirets']*10; d['ip_score']=d['presence_ip']*50; d['arobase_score']=d['nb_arobase']*40; d['suspect_score']=d['mot_suspect']*25; d['banking_score']=d['mot_banking']*15; d['longueur_score']=10 if d['longueur_url']>75 else 0; d['chiffres_score']=min(20, d['nb_chiffres']*2)
        return d
    except:
        return {'longueur_url':len(url),'longueur_hostname':0,'nb_points':0,'nb_tirets':0,'nb_chiffres':0,'nb_symboles':0,'presence_ip':0,'presence_arobase':0,'nb_arobase':0,'presence_https':0,'nb_sous_domaines':0,'mot_banking':0,'mot_suspect':0,'age_domaine':-1,'nb_tirets_score':0,'ip_score':0,'arobase_score':0,'suspect_score':0,'banking_score':0,'longueur_score':0,'chiffres_score':0}
def features_to_vector(fd):
    if LOCAL_MODE:
        try:
            return fv_local(fd)
        except:
            pass
    try:
        f1=fd.get('longueur_url',0); f2=fd.get('longueur_hostname',0); f3=fd.get('nb_points',0); f4=fd.get('nb_tirets',0); f5=fd.get('nb_chiffres',0); f6=fd.get('nb_symboles',0); f7=fd.get('presence_ip',0); f8=fd.get('presence_arobase',0); f9=fd.get('presence_https',0); f10=fd.get('nb_sous_domaines',0); f11=fd.get('mot_banking',0); f12=fd.get('mot_suspect',0); f13=fd.get('age_domaine',4000); f14=30 if f13<100 else 365; f15=0 if f7==1 else (1 if f9==1 and f13>1000 else 0); f16=2 if f8==1 else 0; f17=1 if f13>1000 else 0; f18=1; f19=0; f20=(f4*2+f11*3+f12*2+f7*5)
        return [f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f19,f20]
    except:
        return [0]*20
def load_model():
    try:
        import sklearn
    except:
        return None
    for p in [os.path.join(BASE_DIR,"model_rf.pkl"), os.path.join(BASE_DIR,"modele_rf.pkl"), "model.pkl", "model_rf.pkl"]:
        if os.path.exists(p):
            try:
                with open(p,"rb") as f:
                    return pickle.load(f)
            except:
                try:
                    import joblib
                    return joblib.load(p)
                except:
                    continue
    return None
model=load_model()


# ==================== EXEMPLES (menu de démonstration) ====================
MANUAL = "Saisie manuelle"
ex_dict = {
    MANUAL: "",
    "Orange Money - site officiel (légitime)": "https://www.orange.sn/orange-money",
    "Orange - IP + @ (critique)": "http://orange-money-secure-login.com@192.168.1.1/verify",
    "Orange - faux bonus de 50 000 F": "http://orange-money-bonus-50000f.com/gain?tel=771234567",
    "Orange - faux compte bloqué": "https://orange-money-compte-bloque-verif.com/securite/login",
    "Wave - site officiel (légitime)": "https://www.wave.com/fr-FR/",
    "Wave - faux bonus urgent": "http://wave-secure-bonus-2024.com/login?verif=compte",
    "Wave - faux gain de 25 000 F": "http://wave-felicitation-gain-25000.com/recompense"
}

def on_exemple_change():
    choix = st.session_state.exemple_select_key
    if choix != MANUAL:
        st.session_state.url_input_key = ex_dict[choix]

def on_sms_change():
    txt = st.session_state.sms_input_key
    if txt:
        urls = extraire_urls_sms(txt)
        if urls:
            st.session_state.url_input_key = urls[0]

# ==================== OUTILS D'AFFICHAGE ====================
ICON_SHIELD = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.5 4.5 5.5v5.8c0 4.7 3.2 8.7 7.5 10.2 4.3-1.5 7.5-5.5 7.5-10.2V5.5L12 2.5z"/><path d="m8.6 12.2 2.4 2.4 4.5-4.8" stroke="#5BD99B"/></svg>'
ICON_ALERT = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.3 3.9 2.4 17.6A2 2 0 0 0 4.1 20.6h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9.5v4.2M12 17h.01"/></svg>'
ICON_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9.5"/><path d="m7.8 12.4 2.7 2.7 5.7-6"/></svg>'
ICON_SEND = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21.5 3.5 10.8 14.2M21.5 3.5 14.6 21l-3.8-6.8L4 10.4l17.5-6.9z"/></svg>'

def fmt_pct(x):
    return f"{x:.1f}".replace(".", ",")

URL_LEGEND = {
    "u-fake": ("#FFE6B8", "Partie que le navigateur ignore (avant le @)"),
    "u-ip": ("#F8CFCB", "Adresse IP à la place d'un nom de site"),
    "u-warn": ("#FFFFFF", "Mot qui pousse à agir vite"),
}

def annotate_url(url):
    """Surligne les éléments suspects d'une URL (affichage seulement). Retourne (html, classes_utilisées)."""
    suspects = ["securite", "verif", "bonus", "login", "urgent", "blocage", "gain", "recompense", "felicitation"]
    segs = []
    m = re.match(r'^((?:https?://)?)([^/?#\s]*@)(.*)$', url, re.S)
    if m:
        segs += [(m.group(1), ""), (m.group(2), "u-fake")]
        rest = m.group(3)
    else:
        rest = url
    pat = re.compile(r'(?P<ip>\b(?:\d{1,3}\.){3}\d{1,3}\b)|(?P<w>' + '|'.join(suspects) + ')', re.I)
    pos = 0
    for mm in pat.finditer(rest):
        if mm.start() > pos:
            segs.append((rest[pos:mm.start()], ""))
        segs.append((mm.group(0), "u-ip" if mm.group("ip") else "u-warn"))
        pos = mm.end()
    if pos < len(rest):
        segs.append((rest[pos:], ""))
    used = {c for _, c in segs if c}
    out = "".join(f'<span class="{c}">{html.escape(t)}</span>' if c else html.escape(t) for t, c in segs).replace("@", "@<wbr>").replace("/verify", "<wbr>/verify")
    return out, used

def legend_html(used):
    items = [f'<span><span class="k" style="background:{URL_LEGEND[c][0]};{"border:1px solid #B3261E;" if c=="u-warn" else ""}"></span>{URL_LEGEND[c][1]}</span>' for c in ("u-fake", "u-ip", "u-warn") if c in used]
    return f'<div class="vd-legend">{"".join(items)}</div>' if items else ""

def header_bar_html():
    logo = f'<img src="data:image/png;base64,{estm_b64}" alt="Logo ESTM" />' if estm_b64 else ""
    return f'''<div class="pg-bar">
        <div class="pg-brand"><span class="pg-mark">{ICON_SHIELD}</span><span class="pg-word">PhishGuard Sénégal</span></div>
        <div class="pg-school">{logo}<span>ESTM Dakar</span></div>
    </div>'''

def footer_html():
    av = f'<img class="av" src="data:image/jpeg;base64,{babacar_b64}" alt="Babacar Mbow" />' if babacar_b64 else ""
    return f'''<div class="pg-foot">{av}
        <div><b>Babacar Mbow</b>, encadreur : Elhadji Ahmadou Chérif Diouf<br/>
        Projet de licence Téléinformatique (GLAR), ESTM Dakar, 2026-2027</div>
    </div>'''

CONTACTS = {
    "Orange Money": [
        ("Orange Money", "Code *144# officiel", "121"),
        ("Service client", "Appel gratuit, 24h/24", "144"),
        ("Fraude Orange", "Signaler une arnaque", "800 00 00 10"),
        ("Police cybercriminalité", "Signaler une infraction", "800 00 00 11"),
    ],
    "Wave": [
        ("Wave Sénégal", "Application officielle", "*200#"),
        ("Service Wave", "24h/24", "200 600"),
        ("Fraude Wave", "Signaler une arnaque", "signal@wave.com"),
        ("Police cybercriminalité", "Signaler une infraction", "800 00 00 11"),
    ],
}


# ==================== PAGE D'ACCUEIL AVEC AUTH ====================
if not st.session_state.authenticated:
    st.markdown("<style>.block-container, [data-testid='stMainBlockContainer']{max-width:1120px !important;}</style>", unsafe_allow_html=True)
    st.markdown(header_bar_html(), unsafe_allow_html=True)

    demo_url_html, _ = annotate_url("http://orange-money-secure-login.com@192.168.1.1/verify")
    col_hero, col_form = st.columns([1.05, 1], gap="large")

    with col_hero:
        st.markdown(f"""
        <div class="pg-hero">
            <h1 class="pg-h1">Vérifiez le lien avant de cliquer.</h1>
            <p class="pg-lead">Collez le SMS que vous venez de recevoir. PhishGuard repère les faux sites qui imitent Orange Money et Wave.</p>
            <div class="pg-sms">
                <div class="pg-sms-from">Message reçu de ORANGE MONEY</div>
                <div class="pg-sms-body">Votre compte est bloqué. Vérifiez ici pour éviter la suspension : <code>{demo_url_html}</code></div>
            </div>
            <ul class="pg-anat">
                <li><span class="sw" style="background:#FFE6B8"></span><div><b>orange-money-secure-login.com@</b> ressemble à une adresse Orange, mais le navigateur ignore tout ce qui précède le @.</div></li>
                <li><span class="sw" style="background:#F8CFCB"></span><div><b>192.168.1.1</b> est l'endroit où le lien vous envoie réellement : une adresse IP, pas un site officiel.</div></li>
            </ul>
            <div class="pg-hero-foot">
                Liens pris en charge : <span class="dot" style="background:#FF7900"></span>Orange Money <span class="dot" style="background:#1DC8FF; margin-left:10px"></span>Wave<br/>
                Un modèle Random Forest analyse 20 caractéristiques du lien (précision de 98,2 %).
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_form:
        with st.container(border=True, key="authcard"):
            tab_login, tab_signup, tab_forgot = st.tabs(["Connexion", "Créer un compte", "Mot de passe oublié"])

            with tab_login:
                st.markdown('<div class="fh">Connexion</div><div class="fs">Connectez-vous pour analyser un lien.</div>', unsafe_allow_html=True)
                login_user = st.text_input("Nom d'utilisateur", placeholder="Votre nom d'utilisateur", key="login_user")
                login_pwd = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe", key="login_pwd")
                if st.button("Se connecter", key="btn_login", use_container_width=True):
                    if lock_remaining():
                        st.error(f"Trop de tentatives. Réessayez dans {lock_remaining()} secondes.")
                    elif not login_user or not login_pwd:
                        st.warning("Remplissez tous les champs.")
                    else:
                        ok, msg = check_login(login_user.strip(), login_pwd)
                        if ok:
                            st.session_state.authenticated = True
                            st.session_state.username = login_user.strip()
                            st.rerun()
                        else:
                            register_fail()
                            st.error(msg)

            with tab_signup:
                st.markdown('<div class="fh">Créer un compte</div><div class="fs">Quelques secondes suffisent.</div>', unsafe_allow_html=True)
                signup_user = st.text_input("Nom d'utilisateur", placeholder="Choisissez un nom", key="signup_user")
                signup_email = st.text_input("Email", placeholder="vous@exemple.com", key="signup_email")
                signup_pwd = st.text_input("Mot de passe", type="password", placeholder=f"{MIN_PWD} caractères minimum", key="signup_pwd")
                signup_pwd2 = st.text_input("Confirmer le mot de passe", type="password", placeholder="Saisissez-le à nouveau", key="signup_pwd2")
                if st.button("Créer mon compte", key="btn_signup", use_container_width=True):
                    if not signup_user or not signup_email or not signup_pwd:
                        st.warning("Remplissez tous les champs.")
                    elif signup_pwd != signup_pwd2:
                        st.error("Les mots de passe ne correspondent pas.")
                    else:
                        ok, msg, code = register_user(signup_user, signup_email, signup_pwd)
                        if ok:
                            st.success(msg + ". Vous pouvez maintenant vous connecter.")
                            st.warning("Notez ce code de récupération. Il sert à changer votre mot de passe si vous l'oubliez et ne sera plus affiché.")
                            st.code(code, language=None)
                        else:
                            st.error(msg)

            with tab_forgot:
                st.markdown('<div class="fh">Mot de passe oublié</div><div class="fs">Entrez le code de récupération reçu à la création du compte.</div>', unsafe_allow_html=True)
                forgot_user = st.text_input("Nom d'utilisateur", placeholder="Votre nom d'utilisateur", key="forgot_user")
                forgot_code = st.text_input("Code de récupération", placeholder="XXXX-XXXX-XXXX-XXXX", key="forgot_code")
                forgot_new_pwd = st.text_input("Nouveau mot de passe", type="password", placeholder=f"{MIN_PWD} caractères minimum", key="forgot_new_pwd")
                forgot_new_pwd2 = st.text_input("Confirmer le nouveau mot de passe", type="password", placeholder="Saisissez-le à nouveau", key="forgot_new_pwd2")
                if st.button("Réinitialiser le mot de passe", key="btn_forgot", use_container_width=True):
                    if lock_remaining():
                        st.error(f"Trop de tentatives. Réessayez dans {lock_remaining()} secondes.")
                    elif not forgot_user or not forgot_code or not forgot_new_pwd:
                        st.warning("Remplissez tous les champs.")
                    elif forgot_new_pwd != forgot_new_pwd2:
                        st.error("Les mots de passe ne correspondent pas.")
                    else:
                        ok, msg, code = reset_password(forgot_user, forgot_code, forgot_new_pwd)
                        if ok:
                            st.success(msg + ". Vous pouvez vous connecter.")
                            st.warning("Voici votre nouveau code de récupération. L'ancien ne fonctionne plus.")
                            st.code(code, language=None)
                        else:
                            register_fail()
                            st.error(msg)


    st.markdown(footer_html(), unsafe_allow_html=True)

else:
    # ==================== PAGE SYSTEME (analyse) ====================
    st.markdown("<style>.block-container, [data-testid='stMainBlockContainer']{max-width:820px !important;}</style>", unsafe_allow_html=True)

    with st.container(key="bar"):
        c_brand, c_user, c_out = st.columns([4.2, 2.6, 2.6])
        with c_brand:
            st.markdown(f'<div class="pg-brand"><span class="pg-mark">{ICON_SHIELD}</span><span class="pg-word">PhishGuard Sénégal</span></div>', unsafe_allow_html=True)
        with c_user:
            st.markdown(f'<div class="pg-user">Connecté : <b>{html.escape(st.session_state.username)}</b></div>', unsafe_allow_html=True)
        with c_out:
            if st.button("Déconnexion", key="logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.rerun()

    with st.expander("Mon compte", expanded=False):
        st.markdown("**Changer le mot de passe**")
        acc_old = st.text_input("Mot de passe actuel", type="password", key="acc_old")
        acc_new = st.text_input("Nouveau mot de passe", type="password", placeholder=f"{MIN_PWD} caractères minimum", key="acc_new")
        acc_new2 = st.text_input("Confirmer le nouveau mot de passe", type="password", key="acc_new2")
        if st.button("Changer le mot de passe", key="btn_change_pwd"):
            if not acc_old or not acc_new:
                st.warning("Remplissez tous les champs.")
            elif acc_new != acc_new2:
                st.error("Les mots de passe ne correspondent pas.")
            else:
                ok, msg = change_password(st.session_state.username, acc_old, acc_new)
                (st.success if ok else st.error)(msg + ".")
        st.markdown("**Code de récupération**")
        st.caption("Le code sert à réinitialiser le mot de passe si vous l'oubliez. Créer un nouveau code remplace l'ancien.")
        acc_pwd_code = st.text_input("Mot de passe actuel", type="password", key="acc_pwd_code")
        if st.button("Créer un nouveau code de récupération", key="btn_new_code"):
            ok, msg, code = regenerate_recovery(st.session_state.username, acc_pwd_code)
            if ok:
                st.warning("Notez ce code maintenant. Il ne sera plus affiché.")
                st.code(code, language=None)
            else:
                st.error(msg + ".")

    st.markdown('<h1 class="pg-title">Ce lien est-il sûr ?</h1><p class="pg-intro">Collez le SMS reçu ou saisissez le lien. PhishGuard vérifie les liens Orange Money et Wave.</p>', unsafe_allow_html=True)

    with st.container(border=True, key="inputcard"):
        st.text_area(
            "Message reçu par SMS (facultatif)",
            placeholder="ORANGE MONEY : Votre compte est bloqué. Vérifiez ici : http://orange-money-secure-login.com@192.168.1.1/verify pour éviter la suspension",
            height=105,
            key="sms_input_key",
            on_change=on_sms_change,
        )
        sms_cur = st.session_state.get("sms_input_key", "")
        if sms_cur:
            urls = extraire_urls_sms(sms_cur)
            if urls:
                st.markdown(f'<div class="pg-note"><div><b>Lien trouvé dans le message et copié ci-dessous.</b><br/><code>{html.escape(urls[0])}</code></div></div>', unsafe_allow_html=True)

        st.selectbox(
            "Ou choisissez un exemple de démonstration",
            options=list(ex_dict.keys()),
            key="exemple_select_key",
            on_change=on_exemple_change
        )

        url_a_analyser = st.text_input(
            "Lien à vérifier",
            placeholder="https://orange-money... ou https://wave...",
            key="url_input_key"
        )

        if url_a_analyser:
            aut, marq = est_autorisee(url_a_analyser)
            if aut:
                st.markdown(f'<div class="pg-note"><div><b>{marq} reconnu.</b> Le lien est prêt à être analysé.</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="pg-note warn"><div><b>Lien non pris en charge.</b> PhishGuard ne traite que les liens qui contiennent « orange » ou « wave ».</div></div>', unsafe_allow_html=True)

        analyser = st.button("Analyser le lien", type="primary", use_container_width=True)

    if analyser:
        url_final = st.session_state.get("url_input_key", "").strip()
        if not url_final:
            st.markdown('<div class="pg-note warn" style="margin-top:14px"><div><b>Aucun lien à analyser.</b> Choisissez un exemple, collez un SMS ou saisissez un lien qui contient « orange » ou « wave ».</div></div>', unsafe_allow_html=True)
        else:
            autorise, marque = est_autorisee(url_final)
            if not autorise:
                url_h, used = annotate_url(url_final)
                st.markdown(f"""
                <div class="vd" style="border-color:#E3C48F">
                    <div class="vd-top" style="background:var(--amber-bg); color:var(--ink)">
                        <div class="vd-text">
                            <div class="vd-title" style="font-size:24px">Lien non pris en charge</div>
                            <div class="vd-sub" style="opacity:1; color:#5C3700">Ce lien ne contient ni « orange » ni « wave ». PhishGuard est spécialisé dans les arnaques Orange Money et Wave au Sénégal.</div>
                        </div>
                    </div>
                    <div class="vd-url"><div class="vd-url-label">Lien saisi</div><code>{html.escape(url_final)}</code></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                with st.spinner(f"Analyse du lien {marque} en cours..."):
                    feats=extract_features(url_final)
                    vec=features_to_vector(feats)
                    if model is not None:
                        try:
                            pred=int(model.predict([vec])[0]); proba=model.predict_proba([vec])[0]; conf=float(proba[1]*100) if len(proba)>1 else (95.0 if pred==1 else 5.0)
                        except:
                            conf=min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0)+feats.get('arobase_score',0)+feats.get('suspect_score',0))); pred=1 if conf>60 else 0
                    else:
                        conf=min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0)+feats.get('arobase_score',0)+feats.get('suspect_score',0)+feats.get('banking_score',0))); pred=1 if conf>60 else 0

                    url_h, used = annotate_url(url_final)

                    if pred==1:
                        st.markdown(f"""
                        <div class="vd vd-bad" role="alert">
                            <div class="vd-top">
                                <div class="vd-icon">{ICON_ALERT}</div>
                                <div class="vd-text">
                                    <div class="vd-title">Phishing détecté</div>
                                    <div class="vd-sub">Faux site qui imite {marque}. Ne cliquez pas sur ce lien.</div>
                                </div>
                                <div class="vd-score"><div class="vd-num">{fmt_pct(conf)} %</div><div class="vd-cap">probabilité de phishing</div></div>
                            </div>
                            <div class="vd-meter"><span style="width:{conf:.1f}%"></span></div>
                            <div class="vd-meter-cap"><span>0 %</span><span>100 %</span></div>
                            <div class="vd-url"><div class="vd-url-label">Lien analysé</div><code>{url_h}</code>{legend_html(used)}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        if marque == "Orange Money":
                            code_nom = "code secret Orange Money"
                            reset_how = "changez-le tout de suite avec *144# ou dans l'application officielle"
                        else:
                            code_nom = "code secret Wave"
                            reset_how = "changez-le tout de suite dans l'application officielle Wave"

                        st.markdown(f"""
                        <div class="pg-card">
                            <h3>Que faire maintenant</h3>
                            <ol class="pg-steps">
                                <li><div><b>Ne donnez jamais votre {code_nom}.</b> {marque} ne le demande jamais par SMS ni par lien.</div></li>
                                <li><div>Si vous l'avez déjà saisi sur ce faux site, {reset_how}.</div></li>
                                <li><div>Ne transférez pas d'argent sous la menace d'un blocage de compte.</div></li>
                                <li><div>Signalez l'arnaque à {marque} et à la police (numéros ci-dessous).</div></li>
                            </ol>
                        </div>
                        """, unsafe_allow_html=True)

                        rows = "".join(f'<div class="pg-contact"><div>{html.escape(a)}<small>{html.escape(b)}</small></div><div class="num">{html.escape(c)}</div></div>' for a,b,c in CONTACTS[marque])
                        st.markdown(f'<div class="pg-card"><h3>Numéros pour signaler</h3><div class="pg-contacts">{rows}</div></div>', unsafe_allow_html=True)

                        import urllib.parse
                        whatsapp_msg = f"ALERTE PHISHING - PhishGuard Sénégal a détecté un faux site {marque} !\n\nLien frauduleux : {url_final}\nProbabilité de phishing : {conf:.1f} %\n\nNe cliquez pas ! Ne donnez jamais votre code secret {marque}.\n\nSignalez : {'121 / 144 Orange' if marque == 'Orange Money' else '200 600 Wave'}\n\nPhishGuard, ESTM Dakar"
                        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(whatsapp_msg)}"
                        st.markdown(f"""
                        <div class="pg-card">
                            <h3>Prévenir vos proches</h3>
                            <p class="pg-share-help">Envoyez l'alerte à vos contacts pour qu'ils n'ouvrent pas ce lien.</p>
                            <a class="pg-share" href="{whatsapp_url}" target="_blank" rel="noopener">{ICON_SEND}Partager l'alerte sur WhatsApp</a>
                        </div>
                        """, unsafe_allow_html=True)

                    else:
                        st.markdown(f"""
                        <div class="vd vd-ok">
                            <div class="vd-top">
                                <div class="vd-icon">{ICON_CHECK}</div>
                                <div class="vd-text">
                                    <div class="vd-title">Aucun signe de phishing</div>
                                    <div class="vd-sub">Le modèle juge ce lien {marque} légitime. Restez prudent avec les liens reçus par SMS.</div>
                                </div>
                                <div class="vd-score"><div class="vd-num">{fmt_pct(100-conf)} %</div><div class="vd-cap">probabilité de légitimité</div></div>
                            </div>
                            <div class="vd-meter"><span style="width:{100-conf:.1f}%"></span></div>
                            <div class="vd-meter-cap"><span>0 %</span><span>100 %</span></div>
                            <div class="vd-url"><div class="vd-url-label">Lien analysé</div><code>{url_h}</code>{legend_html(used)}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # ANALYSE TECHNIQUE
                    st.markdown('<h2 class="sec-h">Pourquoi ce résultat</h2><p class="sec-sub">Les mesures extraites du lien et utilisées par le modèle.</p>', unsafe_allow_html=True)
                    tab_lex, tab_sec, tab_ctx = st.tabs(["Forme du lien", "Sécurité", "Contexte"])
                    with tab_lex:
                        c1,c2,c3=st.columns(3)
                        with c1:
                            st.metric("Longueur de l'URL", feats.get('longueur_url',0)); st.metric("Longueur du nom de site", feats.get('longueur_hostname',0))
                        with c2:
                            st.metric("Points (.)", feats.get('nb_points',0)); st.metric("Tirets (-)", feats.get('nb_tirets',0), delta="Suspect si > 3" if feats.get('nb_tirets',0)>3 else None, delta_color="inverse")
                        with c3:
                            st.metric("Chiffres", feats.get('nb_chiffres',0)); st.metric("Arobase (@)", feats.get('nb_arobase',0), delta="Danger" if feats.get('nb_arobase',0)>0 else None, delta_color="inverse")
                    with tab_sec:
                        c1,c2,c3=st.columns(3)
                        with c1:
                            st.metric("Adresse IP", "Oui, suspect" if feats.get('presence_ip')==1 else "Non"); st.metric("Présence de @", "Oui, suspect" if feats.get('presence_arobase')==1 else "Non")
                        with c2:
                            st.metric("HTTPS", "Oui" if feats.get('presence_https')==1 else "Non, suspect"); st.metric("Âge du domaine", f"{feats.get('age_domaine',-1)} j")
                        with c3:
                            st.metric("IP et @ ensemble", "Oui, critique" if feats.get('presence_ip')==1 and feats.get('presence_arobase')==1 else "Non")
                    with tab_ctx:
                        c1,c2=st.columns(2)
                        with c1:
                            st.metric("Nom de marque dans le lien", "Oui (orange ou wave)" if feats.get('mot_banking')==1 else "Non"); st.metric("Marque", marque)
                        with c2:
                            st.metric("Mot suspect", "Oui (bonus, blocage...)" if feats.get('mot_suspect')==1 else "Non"); st.metric("Cible", "Sénégal" if feats.get('mot_banking')==1 else "Autre")

                    with st.expander("Voir les 20 caractéristiques (JSON)"):
                        st.json(feats)

                    # DIAGRAMME
                    st.markdown('<h2 class="sec-h">Contribution de chaque indice</h2><p class="sec-sub">Part de chaque indice dans le score de risque du lien.</p>', unsafe_allow_html=True)
                    try:
                        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
                        labels=['Adresse IP','Arobase (@)','Tirets','Mots suspects','Nom de marque','Longueur','Chiffres','HTTPS manquant']
                        scores=[feats.get('ip_score',0),feats.get('arobase_score',0),feats.get('nb_tirets_score',0),feats.get('suspect_score',0),feats.get('banking_score',0),feats.get('longueur_score',0),feats.get('chiffres_score',0),0 if feats.get('presence_https',0)==1 else 15]
                        total=sum(scores) if sum(scores)>0 else 1; pcts=[s/total*100 for s in scores]
                        order=sorted(range(len(labels)), key=lambda i: pcts[i], reverse=True)
                        labels_s=[labels[i] for i in order]; pcts_s=[pcts[i] for i in order]
                        top_color='#B3261E' if pred==1 else '#12935A'
                        colors=[top_color if p>30 else '#7FA3D6' for p in pcts_s]
                        fig,ax=plt.subplots(figsize=(8.6,4.4)); fig.patch.set_facecolor('white'); ax.set_facecolor('white')
                        bars=ax.barh(labels_s,pcts_s,color=colors,height=0.6)
                        ax.invert_yaxis()
                        ax.set_xlim(0, max(100, max(pcts_s)+12) if max(pcts_s)>88 else 100)
                        ax.set_xlabel('Contribution au risque (%)', fontsize=10.5, color='#54667B')
                        for bar,p in zip(bars,pcts_s):
                            if p>0.5:
                                ax.text(bar.get_width()+1.2, bar.get_y()+bar.get_height()/2, f'{p:.0f} %', va='center', fontweight='600', fontsize=10.5, color='#0E2238')
                        for s in ('top','right','left'): ax.spines[s].set_visible(False)
                        ax.spines['bottom'].set_color('#D8DFE8'); ax.tick_params(axis='y', length=0, labelsize=11, colors='#0E2238'); ax.tick_params(axis='x', colors='#54667B', labelsize=10)
                        ax.grid(axis='x', color='#E5EAF0', linewidth=0.8); ax.set_axisbelow(True)
                        plt.tight_layout(); st.pyplot(fig, use_container_width=True)
                        buf=io.BytesIO(); fig.savefig(buf, format='png', dpi=300, bbox_inches='tight'); buf.seek(0)
                        st.download_button("Télécharger le diagramme (PNG, 300 DPI)", data=buf, file_name=f"diagramme_{marque}_{int(conf)}pct.png", mime="image/png", use_container_width=True)
                    except ImportError:
                        st.info("Le graphique avancé nécessite matplotlib (pip install matplotlib). Version simplifiée ci-dessous.")
                        _labels=['Adresse IP','Arobase (@)','Tirets','Mots suspects','Nom de marque','Longueur','Chiffres','HTTPS manquant']
                        _sc=[feats.get('ip_score',0),feats.get('arobase_score',0),feats.get('nb_tirets_score',0),feats.get('suspect_score',0),feats.get('banking_score',0),feats.get('longueur_score',0),feats.get('chiffres_score',0),0 if feats.get('presence_https',0)==1 else 15]
                        st.bar_chart(pd.DataFrame({'Score brut':_sc}, index=_labels))
                        labels, scores = _labels, _sc
                        total=sum(scores) if sum(scores)>0 else 1; pcts=[x/total*100 for x in scores]
                    df=pd.DataFrame({'Indice':labels,'Score brut':scores,'Part':[f"{p:.1f} %" for p in pcts]}); st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown(footer_html(), unsafe_allow_html=True)
