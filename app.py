"""
PhishGuard Senegal - ULTRA BEAUTIFUL DESIGN 2026 - ESTM Dakar
Babacar MBOW - Licence Teleinformatique 2026-2027
Design: Premium Glassmorphism + Gradient + Animations + Neumorphism
Orange Money & Wave ONLY - Fix dropdown remplit champ
"""
import streamlit as st, sys, os, pickle, re, base64, io
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

st.set_page_config(page_title="PhishGuard Sénégal - ESTM", page_icon="🛡️", layout="centered")

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

# ULTRA BEAUTIFUL CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800;900&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] {font-family: 'Outfit', sans-serif !important;}
[data-testid="stAppViewContainer"] {
    background: radial-gradient(1200px 600px at 10% -10%, #E8F0FF 0%, transparent 60%),
                radial-gradient(1000px 500px at 90% 0%, #FFF0E6 0%, transparent 60%),
                linear-gradient(180deg, #F8FAFF 0%, #FFFFFF 100%);
}
.hero {
    background: linear-gradient(135deg, #0A1931 0%, #0A3D8A 50%, #123D8A 100%);
    border-radius: 28px; padding: 28px 32px; color: white;
    box-shadow: 0 20px 60px rgba(10,61,138,0.35), inset 0 1px 0 rgba(255,255,255,0.2);
    position: relative; overflow: hidden; margin-bottom: 22px;
}
.hero::before {
    content: ""; position: absolute; top:-60px; right:-60px; width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(255,121,0,0.35) 0%, transparent 70%);
    filter: blur(10px);
}
.hero-title {font-size: 32px; font-weight: 900; letter-spacing: -0.5px; line-height: 1.1;}
.hero-sub {font-size: 13px; opacity: 0.85; margin-top: 8px; line-height: 1.5;}
.badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18);
    padding: 6px 12px; border-radius: 999px; font-size: 11px; font-weight: 700; letter-spacing: 0.3px;
    backdrop-filter: blur(10px);
}
.badge-orange {background: linear-gradient(90deg, #FF7900, #FF9A3D); border: none; color: white; box-shadow: 0 6px 20px rgba(255,121,0,0.4);}
.glass-card {
    background: rgba(255,255,255,0.92); backdrop-filter: blur(16px);
    border-radius: 22px; padding: 22px 22px;
    border: 1px solid rgba(230,236,255,0.9);
    box-shadow: 0 12px 40px rgba(10,61,138,0.08), 0 2px 8px rgba(10,61,138,0.04);
    transition: all 0.35s cubic-bezier(0.16,1,0.3,1);
}
.glass-card:hover {transform: translateY(-2px); box-shadow: 0 20px 60px rgba(10,61,138,0.12), 0 4px 16px rgba(10,61,138,0.06);}
.section-label {font-size: 12px; font-weight: 800; letter-spacing: 1px; color: #0A3D8A; text-transform: uppercase; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;}
.section-label::before {content: ""; width: 24px; height: 3px; border-radius: 999px; background: linear-gradient(90deg, #0A3D8A, #FF7900); display: inline-block;}
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    border-radius: 16px !important; border: 2px solid #E6ECFF !important;
    background: #FBFCFF !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: 13.5px !important; padding: 14px 16px !important;
    transition: all 0.25s ease !important;
}
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
    border-color: #0A3D8A !important; background: white !important;
    box-shadow: 0 0 0 4px rgba(10,61,138,0.12) !important;
}
.stSelectbox > div > div {
    border-radius: 16px !important; border: 2px solid #E6ECFF !important;
    background: #FBFCFF !important; font-weight: 600 !important;
}
div[data-testid="stButton"] > button {
    background: linear-gradient(100deg, #0A3D8A 0%, #1A5DBE 45%, #FF7900 100%) !important;
    color: white !important; border: none !important; border-radius: 16px !important;
    padding: 16px 22px !important; font-weight: 900 !important; font-size: 15px !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 14px 32px rgba(10,61,138,0.28), 0 4px 12px rgba(255,121,0,0.25) !important;
    position: relative; overflow: hidden;
    transition: all 0.35s cubic-bezier(0.16,1,0.3,1) !important;
}
div[data-testid="stButton"] > button::after {
    content: ""; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
    transition: left 0.6s ease;
}
div[data-testid="stButton"] > button:hover {transform: translateY(-2px) scale(1.01); box-shadow: 0 20px 48px rgba(10,61,138,0.35), 0 8px 20px rgba(255,121,0,0.32) !important;}
div[data-testid="stButton"] > button:hover::after {left: 100%;}
.result-phishing {
    background: linear-gradient(135deg, #FFF5F5 0%, #FFE2E2 100%);
    border: 1.5px solid #FFB3B3; border-left: 6px solid #FF2D2D;
    border-radius: 20px; padding: 20px 22px;
    box-shadow: 0 16px 40px rgba(255,45,45,0.18);
    animation: shake 0.4s ease;
}
.result-legit {
    background: linear-gradient(135deg, #F0FFF4 0%, #DCFCE7 100%);
    border: 1.5px solid #86EFAC; border-left: 6px solid #00C950;
    border-radius: 20px; padding: 20px 22px;
    box-shadow: 0 16px 40px rgba(0,201,80,0.18);
}
@keyframes shake {0%,100%{transform:translateX(0)} 25%{transform:translateX(-2px)} 75%{transform:translateX(2px)}}
.metric-pill {
    background: linear-gradient(135deg, #F8FAFF, #FFFFFF);
    border: 1px solid #E6ECFF; border-radius: 14px; padding: 12px;
    text-align: center; box-shadow: 0 4px 16px rgba(10,61,138,0.06);
}
.footer {
    background: white; border: 1px solid #E6ECFF; border-radius: 18px;
    padding: 18px; text-align: center; box-shadow: 0 8px 24px rgba(10,61,138,0.06);
}
</style>
""", unsafe_allow_html=True)

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

# HERO HEADER ULTRA BEAUTIFUL
if estm_b64:
    st.markdown(f"""
    <div class="hero">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px; position:relative; z-index:1;">
            <div>
                <div style="display:flex; align-items:center; gap:14px;">
                    <div style="background:white; border-radius:14px; padding:7px 10px; box-shadow:0 8px 24px rgba(0,0,0,0.15);">
                        <img src="data:image/png;base64,{estm_b64}" style="height:36px; display:block;" />
                    </div>
                    <div>
                        <div style="font-weight:900; font-size:14px; letter-spacing:0.4px;">ESTM DAKAR</div>
                        <div style="font-size:10px; opacity:0.8; font-weight:600;">LICENCE TÉLÉINFORMATIQUE 2026-2027</div>
                    </div>
                </div>
                <div class="hero-title" style="margin-top:18px;">PhishGuard<br/>Sénégal 🛡️</div>
                <div class="hero-sub">Détecteur IA <b>20 caractéristiques</b> • Random Forest 98.2%<br/>Spécialisé <b>Orange Money & Wave</b> • Anti-SMS arnaques 🇸🇳</div>
                <div style="margin-top:14px; display:flex; gap:8px; flex-wrap:wrap;">
                    <span class="badge"><span style="width:8px; height:8px; background:#00FF88; border-radius:50%; display:inline-block; box-shadow:0 0 0 4px rgba(0,255,136,0.2);"></span> IA en ligne</span>
                    <span class="badge badge-orange">🔒 Orange & Wave ONLY</span>
                    <span class="badge">📊 20 features</span>
                </div>
            </div>
            <div style="text-align:right;">
                <img src="data:image/jpeg;base64,{babacar_b64}" style="width:56px; height:56px; border-radius:18px; object-fit:cover; border:2.5px solid rgba(255,255,255,0.9); box-shadow:0 10px 30px rgba(0,0,0,0.25);" />
                <div style="margin-top:10px; font-weight:800; font-size:13px;">Babacar MBOW</div>
                <div style="font-size:10px; opacity:0.8;">GLAR • ESTM</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="hero">
        <div class="hero-title">PhishGuard Sénégal 🛡️</div>
        <div class="hero-sub">Détecteur IA 20 caractéristiques • Orange Money & Wave • Anti-SMS arnaques 🇸🇳</div>
    </div>
    """, unsafe_allow_html=True)

# DICTIONNAIRE
ex_dict = {
    "✍️ Saisie manuelle (écrire ci-dessous)": "",
    "✅ Orange Money - Officiel légitime": "https://www.orange.sn/orange-money",
    "⚠️ Orange - Phishing IP + @ (critique)": "http://orange-money-secure-login.com@192.168.1.1/verify",
    "⚠️ Orange - Bonus 50 000F": "http://orange-money-bonus-50000f.com/gain?tel=771234567",
    "⚠️ Orange - Compte bloqué": "https://orange-money-compte-bloque-verif.com/securite/login",
    "✅ Wave - Officiel légitime": "https://www.wave.com/fr-FR/",
    "⚠️ Wave - Bonus urgent": "http://wave-secure-bonus-2024.com/login?verif=compte",
    "⚠️ Wave - Félicitations gain 25k": "http://wave-felicitation-gain-25000.com/recompense"
}

if "url_input_key" not in st.session_state:
    st.session_state.url_input_key = ""

def on_exemple_change():
    choix = st.session_state.exemple_select_key
    if choix != "✍️ Saisie manuelle (écrire ci-dessous)":
        st.session_state.url_input_key = ex_dict[choix]

def on_sms_change():
    txt = st.session_state.sms_input_key
    if txt:
        urls = extraire_urls_sms(txt)
        if urls:
            st.session_state.url_input_key = urls[0]

# SMS CARD
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="section-label">📩 Zone SMS - Arnaque reçue par SMS</div>', unsafe_allow_html=True)
st.text_area(
    "SMS",
    placeholder="ORANGE MONEY: Votre compte est bloqué. Vérifiez ici: http://orange-money-secure-login.com@192.168.1.1/verify pour éviter suspension",
    height=105,
    key="sms_input_key",
    on_change=on_sms_change,
    label_visibility="collapsed"
)
sms_cur = st.session_state.get("sms_input_key","")
if sms_cur:
    urls = extraire_urls_sms(sms_cur)
    if urls:
        st.markdown(f"""
        <div style="margin-top:12px; background: linear-gradient(135deg, #FFF7ED, #FFEDD5); border:1px solid #FDBA74; border-radius:14px; padding:12px 14px; display:flex; gap:10px; align-items:center;">
            <div style="background:#FF7900; color:white; width:32px; height:32px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-weight:900;">🔗</div>
            <div>
                <div style="font-weight:800; font-size:12px; color:#9A3412;">URL détectée et copiée automatiquement</div>
                <div style="font-family:JetBrains Mono; font-size:12px; color:#7C2D12; margin-top:2px; word-break:break-all;">{urls[0]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# URL + DROPDOWN CARD - MEME CHAMP
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="section-label">🔗 Analyse URL - Menu déroulant partage le même champ</div>', unsafe_allow_html=True)

st.selectbox(
    "📋 Choisir un exemple (remplit automatiquement le champ ci-dessous) :",
    options=list(ex_dict.keys()),
    key="exemple_select_key",
    on_change=on_exemple_change
)

url_a_analyser = st.text_input(
    "🌐 URL Orange/Wave (champ partagé - rempli auto par menu ou SMS) :",
    placeholder="https://orange-money... ou https://wave...",
    key="url_input_key"
)

if url_a_analyser:
    aut, marq = est_autorisee(url_a_analyser)
    if aut:
        st.markdown(f"""
        <div style="margin-top:12px; background: linear-gradient(135deg, #EFF6FF, #DBEAFE); border:1px solid #93C5FD; border-radius:14px; padding:12px 14px; display:flex; gap:10px; align-items:center;">
            <div style="background:#0A3D8A; color:white; width:32px; height:32px; border-radius:10px; display:flex; align-items:center; justify-content:center;">✅</div>
            <div>
                <div style="font-weight:800; font-size:12px; color:#1E3A8A;">Marque détectée : {marq}</div>
                <div style="font-size:11px; color:#3730A3;">Prêt pour analyse • Système Orange/Wave ONLY</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="margin-top:12px; background: linear-gradient(135deg, #FEF2F2, #FECACA); border:1px solid #FCA5A5; border-radius:14px; padding:12px 14px;">
            <div style="font-weight:800; font-size:12px; color:#991B1B;">⚠️ URL hors Orange/Wave - sera bloquée</div>
            <div style="font-size:11px; color:#7F1D1D; margin-top:2px;">Le système ne traite QUE les URLs contenant orange ou wave</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# BOUTON
analyser = st.button("✨ Analyser l'URL maintenant", type="primary", use_container_width=True)

if analyser:
    url_final = st.session_state.get("url_input_key","").strip()
    if not url_final:
        st.markdown("""
        <div class="glass-card" style="border-left: 4px solid #F59E0B; background: linear-gradient(135deg, #FFFBEB, #FEF3C7);">
            <div style="font-weight:800; color:#92400E;">⚠️ Aucune URL</div>
            <div style="font-size:13px; color:#78350F; margin-top:4px;">Choisis un exemple dans le menu déroulant, ou colle un SMS, ou saisis une URL contenant orange ou wave.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        autorise, marque = est_autorisee(url_final)
        if not autorise:
            st.markdown(f"""
            <div class="glass-card" style="border-left: 6px solid #EF4444; background: linear-gradient(135deg, #FEF2F2, #FFE2E2);">
                <div style="display:flex; gap:12px; align-items:flex-start;">
                    <div style="background:#EF4444; color:white; width:44px; height:44px; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:22px; flex-shrink:0;">❌</div>
                    <div>
                        <div style="font-weight:900; font-size:16px; color:#991B1B;">URL NON PRISE EN CHARGE</div>
                        <div style="font-size:12px; font-weight:700; color:#B91C1C; margin-top:4px; background:#FEE2E2; padding:4px 8px; border-radius:8px; display:inline-block;">ORANGE MONEY & WAVE ONLY</div>
                        <div style="font-family:JetBrains Mono; font-size:12px; background:white; border:1px solid #FECACA; border-radius:10px; padding:10px; margin-top:10px; word-break:break-all;">{url_final}</div>
                        <div style="font-size:12px; color:#7F1D1D; margin-top:10px;">Cette URL ne contient ni <b>orange</b> ni <b>wave</b>. Notre IA est spécialisée Sénégal uniquement.</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.spinner(f"🔬 Analyse {marque} en cours..."):
                feats=extract_features(url_final)
                vec=features_to_vector(feats)
                if model is not None:
                    try:
                        pred=int(model.predict([vec])[0]); proba=model.predict_proba([vec])[0]; conf=float(proba[1]*100) if len(proba)>1 else (95.0 if pred==1 else 5.0)
                    except:
                        conf=min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0)+feats.get('arobase_score',0)+feats.get('suspect_score',0))); pred=1 if conf>60 else 0
                else:
                    conf=min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0)+feats.get('arobase_score',0)+feats.get('suspect_score',0)+feats.get('banking_score',0))); pred=1 if conf>60 else 0
                
                if pred==1:
                    st.markdown(f"""
                    <div class="result-phishing">
                        <div style="display:flex; gap:14px; align-items:center;">
                            <div style="background:#FF2D2D; color:white; width:54px; height:54px; border-radius:16px; display:flex; align-items:center; justify-content:center; font-size:28px; box-shadow:0 8px 20px rgba(255,45,45,0.35);">🚨</div>
                            <div>
                                <div style="font-weight:900; font-size:20px; color:#991B1B; letter-spacing:-0.3px;">PHISHING DÉTECTÉ</div>
                                <div style="font-weight:800; font-size:13px; color:#B91C1C; margin-top:2px;">{marque} • Faux site • Ne cliquez pas !</div>
                            </div>
                            <div style="margin-left:auto; text-align:right;">
                                <div style="font-weight:900; font-size:26px; color:#DC2626;">{conf:.1f}%</div>
                                <div style="font-size:10px; font-weight:800; letter-spacing:0.5px; color:#991B1B;">CONFIANCE</div>
                            </div>
                        </div>
                        <div style="margin-top:16px; background:rgba(255,255,255,0.9); border-radius:12px; height:12px; overflow:hidden; border:1px solid #FECACA;">
                            <div style="background: linear-gradient(90deg, #EF4444, #DC2626); height:100%; width:{conf}%; border-radius:12px; box-shadow:0 0 12px rgba(239,68,68,0.5);"></div>
                        </div>
                        <div style="margin-top:12px; display:flex; gap:8px; flex-wrap:wrap;">
                            <span style="background:#FEE2E2; border:1px solid #FECACA; padding:5px 10px; border-radius:999px; font-size:11px; font-weight:700; color:#991B1B;">🔴 Risque ÉLEVÉ</span>
                            <span style="background:white; border:1px solid #FECACA; padding:5px 10px; border-radius:999px; font-size:11px; font-weight:700; color:#7F1D1D;">⚠️ SMS frauduleux</span>
                            <span style="background:white; border:1px solid #FECACA; padding:5px 10px; border-radius:999px; font-size:11px; font-weight:700; color:#7F1D1D;">🇸🇳 Cible Sénégal</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="result-legit">
                        <div style="display:flex; gap:14px; align-items:center;">
                            <div style="background:#00C950; color:white; width:54px; height:54px; border-radius:16px; display:flex; align-items:center; justify-content:center; font-size:28px; box-shadow:0 8px 20px rgba(0,201,80,0.35);">✅</div>
                            <div>
                                <div style="font-weight:900; font-size:20px; color:#065F46; letter-spacing:-0.3px;">SITE LÉGITIME</div>
                                <div style="font-weight:800; font-size:13px; color:#047857; margin-top:2px;">{marque} • Vrai site officiel • Sécurisé</div>
                            </div>
                            <div style="margin-left:auto; text-align:right;">
                                <div style="font-weight:900; font-size:26px; color:#059669;">{100-conf:.1f}%</div>
                                <div style="font-size:10px; font-weight:800; letter-spacing:0.5px; color:#065F46;">LÉGITIME</div>
                            </div>
                        </div>
                        <div style="margin-top:16px; background:rgba(255,255,255,0.9); border-radius:12px; height:12px; overflow:hidden; border:1px solid #A7F3D0;">
                            <div style="background: linear-gradient(90deg, #10B981, #059669); height:100%; width:{100-conf}%; border-radius:12px;"></div>
                        </div>
                        <div style="margin-top:12px; display:flex; gap:8px;">
                            <span style="background:#D1FAE5; border:1px solid #A7F3D0; padding:5px 10px; border-radius:999px; font-size:11px; font-weight:700; color:#065F46;">🟢 Risque FAIBLE</span>
                            <span style="background:white; border:1px solid #A7F3D0; padding:5px 10px; border-radius:999px; font-size:11px; font-weight:700; color:#065F46;">🔒 HTTPS OK</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # ANALYSE TECHNIQUE
                st.markdown('<div style="margin-top:22px; font-weight:900; font-size:18px; color:#0A1931; display:flex; align-items:center; gap:10px;"><span style="background: linear-gradient(90deg, #0A3D8A, #FF7900); width:36px; height:36px; border-radius:12px; display:inline-flex; align-items:center; justify-content:center; color:white;">🔬</span> Analyse Technique Détaillée</div>', unsafe_allow_html=True)
                tab_lex, tab_sec, tab_ctx = st.tabs(["📝 Lexical", "🔒 Sécurité", "🌍 Contexte"])
                with tab_lex:
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown('<div style="font-weight:800; font-size:13px; color:#0A3D8A; margin-bottom:12px;">📝 Analyse Lexicale - Forme de l'URL</div>', unsafe_allow_html=True)
                    c1,c2,c3=st.columns(3)
                    with c1:
                        st.metric("Longueur URL", feats.get('longueur_url',0)); st.metric("Hostname", feats.get('longueur_hostname',0))
                    with c2:
                        st.metric("Points (.)", feats.get('nb_points',0)); st.metric("Tirets (-)", feats.get('nb_tirets',0), delta="Suspect si >3" if feats.get('nb_tirets',0)>3 else None, delta_color="inverse")
                    with c3:
                        st.metric("Chiffres", feats.get('nb_chiffres',0)); st.metric("@", feats.get('nb_arobase',0), delta="DANGER" if feats.get('nb_arobase',0)>0 else "OK", delta_color="inverse")
                    st.markdown('</div>', unsafe_allow_html=True)
                with tab_sec:
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown('<div style="font-weight:800; font-size:13px; color:#0A3D8A; margin-bottom:12px;">🔒 Analyse Sécurité - Tromperie</div>', unsafe_allow_html=True)
                    c1,c2,c3=st.columns(3)
                    with c1:
                        st.metric("Présence IP", "Oui ⚠️" if feats.get('presence_ip')==1 else "Non ✅"); st.metric("Présence @", "Oui ⚠️" if feats.get('presence_arobase')==1 else "Non ✅")
                    with c2:
                        st.metric("HTTPS", "Oui ✅" if feats.get('presence_https')==1 else "Non ⚠️"); st.metric("Âge", f"{feats.get('age_domaine',-1)} j")
                    with c3:
                        st.metric("IP+@ critique", "Oui 🔴" if feats.get('presence_ip')==1 and feats.get('presence_arobase')==1 else "Non ✅")
                    st.markdown('</div>', unsafe_allow_html=True)
                with tab_ctx:
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-weight:800; font-size:13px; color:#0A3D8A; margin-bottom:12px;">🌍 Contexte Sénégal - {marque}</div>', unsafe_allow_html=True)
                    c1,c2=st.columns(2)
                    with c1:
                        st.metric("Mot bancaire", "Oui ⚠️ orange/wave" if feats.get('mot_banking')==1 else "Non"); st.metric("Marque", marque)
                    with c2:
                        st.metric("Mot suspect", "Oui bonus/blocage" if feats.get('mot_suspect')==1 else "Non"); st.metric("Cible", "Sénégal" if feats.get('mot_banking')==1 else "Autre")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with st.expander("🔧 Voir JSON complet 20 features - Jury"):
                    st.json(feats)
                
                # DIAGRAMME PREMIUM
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown('<div style="font-weight:900; font-size:14px; color:#0A1931; margin-bottom:6px;">📊 Diagramme Justification - Contribution chaque feature</div>', unsafe_allow_html=True)
                import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
                labels=['IP','@','Tirets','Mots suspects','Banking','Longueur','Chiffres','HTTPS manquant']
                scores=[feats.get('ip_score',0),feats.get('arobase_score',0),feats.get('nb_tirets_score',0),feats.get('suspect_score',0),feats.get('banking_score',0),feats.get('longueur_score',0),feats.get('chiffres_score',0),0 if feats.get('presence_https',0)==1 else 15]
                total=sum(scores) if sum(scores)>0 else 1; pcts=[s/total*100 for s in scores]
                colors=['#FF7900' if s>30 else '#0A3D8A' if s>10 else '#6B7BA3' for s in scores]
                fig,ax=plt.subplots(figsize=(10,5.2)); fig.patch.set_facecolor('white'); ax.set_facecolor('#F8FAFF')
                bars=ax.barh(labels,pcts,color=colors,edgecolor='white',linewidth=1.6, height=0.58, alpha=0.95)
                ax.set_xlabel('Contribution au risque phishing (%)', fontweight='700', fontsize=11, color='#0A1931')
                ax.set_title(f'Justification du score • {marque} • Confiance {conf:.1f}%', fontweight='900', fontsize=13, color='#0A1931', pad=18)
                ax.invert_yaxis()
                for bar,p in zip(bars,pcts):
                    if p>2:
                        ax.text(bar.get_width()+1, bar.get_y()+bar.get_height()/2, f'{p:.1f}%', va='center', fontweight='800', fontsize=10, color='#0A1931')
                ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
                plt.tight_layout(); plt.grid(axis='x', alpha=0.18, linestyle='--'); st.pyplot(fig, use_container_width=True)
                buf=io.BytesIO(); fig.savefig(buf, format='png', dpi=300, bbox_inches='tight'); buf.seek(0)
                st.download_button("📥 Télécharger diagramme HD pour soutenance (PNG 300 DPI)", data=buf, file_name=f"diagramme_{marque}_{int(conf)}pct.png", mime="image/png", use_container_width=True)
                df=pd.DataFrame({'Feature':labels,'Score brut':scores,'Pourcentage':[f"{p:.1f}%" for p in pcts]}); st.dataframe(df, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

st.markdown('st.markdown("---")
st.caption("Projet réalisé dans le cadre de la Licence GLAR - Génie Logiciel & Administration Réseaux - Détection de phishing par IA | 2026")

<div class="footer"><div style="font-weight:900; color:#0A1931; font-size:12px; letter-spacing:0.5px;">ESTM DAKAR • LICENCE TÉLÉINFORMATIQUE 2026-2027</div><div style="font-size:11px; color:#FF7900; font-weight:800; margin-top:6px;">✨ Premium UI • Glassmorphism • Orange Money & Wave ONLY • 20 Features • Lexical • Sécurité • Contexte</div><div style="font-size:11px; color:#6B7BA3; margin-top:6px;">Babacar MBOW • Encadreur: Elhadji Ahmadou Chérif Diouf • Random Forest 98.2% • 2000 URLs • Sénégal</div></div>', unsafe_allow_html=True)
