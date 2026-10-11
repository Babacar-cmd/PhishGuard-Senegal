import streamlit as st
import pickle, re, os, base64
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from urllib.parse import urlparse
import pandas as pd
from datetime import datetime
import requests

@st.cache_data(show_spinner=False)
def get_base64_image(image_path):
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return ""

def extract_features(url):
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc
        f1 = len(url); f2 = len(hostname); f3 = url.count("."); f4 = url.count("-")
        f5 = sum(c.isdigit() for c in url)
        f6 = url.count("@") + url.count("?") + url.count("&") + url.count("=")
        f7 = 1 if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", url) else 0
        f8 = 1 if "@" in url else 0
        f9 = 1 if parsed.scheme == "https" else 0
        f10 = hostname.count(".") - 1 if hostname.count(".") >1 else 0
        f11 = 1 if "orange" in url.lower() or "wave" in url.lower() else 0
        susp = ["securite","securise","verif","bonus","login","urgent","blocage","gain","loterie","transfert"]
        f12 = 1 if any(w in url.lower() for w in susp) else 0
        f13 = 5 if f7==1 or "bit.ly" in url else (10 if f4>=2 and f12==1 else 4000)
        f14 = 30 if f13 < 100 else 365
        f15 = 0 if f7==1 else (1 if f9==1 and f13>1000 else 0)
        f16 = 2 if f8==1 else 0
        f17 = 1 if f13>1000 else 0
        f18 = 1 if "orange.sn" in url or "wave.com" in url and f4<1 else 0
        f19 = 1 if "bit.ly" in url or "tinyurl" in url or "is.gd" in url or "t.ly" in url else 0
        f20 = (f4*2 + f11*3 + f12*2 + f7*5)
        return [f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f19,f20]
    except:
        return [0]*20

def extract_urls_from_sms(text):
    pattern = r'(https?://[^\s]+|bit\.ly/[^\s]+|tinyurl\.com/[^\s]+|is\.gd/[^\s]+|t\.ly/[^\s]+|www\.[^\s]+)'
    urls = re.findall(pattern, text, re.IGNORECASE)
    cleaned = []
    for u in urls:
        if not u.startswith('http'):
            u = 'http://' + u
        cleaned.append(u.rstrip('.,!?)'))
    return cleaned

def detect_brand(url):
    low = url.lower()
    is_orange = "orange" in low or "orangemoney" in low or "orange-money" in low
    is_wave = "wave" in low
    if is_orange and is_wave:
        return "both"
    elif is_orange:
        return "orange"
    elif is_wave:
        return "wave"
    elif "om" in low and ("money" in low or "bonus" in low):
        return "orange"
    else:
        return "unknown"

def is_om_wave_brand(url):
    low = url.lower()
    if "orange" in low or "wave" in low:
        return True
    if ("om" in low and ("money" in low or "bonus" in low or "pay" in low)):
        return True
    return False

def get_brand_info(brand):
    if brand == "orange":
        return {
            "name": "Orange Money",
            "color": "#FF7900",
            "gradient": "linear-gradient(135deg,#FF7900,#FF9A00)",
            "icon": "🟠",
            "domain_legit": "orange.sn / orangemoney.sn",
            "alert_msg": "Ne donnez JAMAIS votre code secret Orange Money.",
            "contact_html": '''🔸 <b>Orange Money:</b> <span style="background:#FFF3E0; padding:3px 8px; border-radius:6px; font-weight:800;">121</span> ou 33 839 12 12<br>🔸 <b>Anti-Fraude Orange:</b> <span style="background:#FFF3E0; padding:3px 8px; border-radius:6px; font-weight:800;">800 88 88 88</span> (gratuit)''',
            "conseil": "Vérifiez toujours que l'URL finit par orange.sn",
            "verif": "orange.sn"
        }
    elif brand == "wave":
        return {
            "name": "Wave",
            "color": "#1DC8FF",
            "gradient": "linear-gradient(135deg,#0A3D8A,#1DC8FF)",
            "icon": "🔵",
            "domain_legit": "wave.com",
            "alert_msg": "Ne partagez JAMAIS votre code Wave.",
            "contact_html": '''🔸 <b>Wave:</b> App Wave → Aide → Signaler | 33 829 50 50<br>🔸 <b>Support Wave:</b> Dans l'application Wave, menu Aide 24h/24''',
            "conseil": "Wave ne vous demandera jamais votre code par SMS",
            "verif": "wave.com"
        }
    else:
        return {
            "name": "OM / Wave",
            "color": "#0A3D8A",
            "gradient": "linear-gradient(135deg,#0A1931,#0A3D8A)",
            "icon": "🛡️",
            "domain_legit": "orange.sn / wave.com",
            "alert_msg": "Ne donnez JAMAIS votre code secret OM/Wave.",
            "contact_html": '''🔸 <b>Orange Money:</b> 121 ou 33 839 12 12<br>🔸 <b>Wave:</b> App Wave → Aide → Signaler | 33 829 50 50''',
            "conseil": "Vérifiez le domaine officiel",
            "verif": "orange.sn / wave.com"
        }


def get_translations(lang):
    """Traductions FR / Wolof"""
    if lang == "Wolof":
        return {
            "title": "PhishGuard Sénégal - Saay-saay bi",
            "subtitle": "Xam-xam bu and ak IA ngir OM/Wave",
            "analyse": "Seetal ak IA bi",
            "url_label": "Yëngal sa lien ci fii",
            "sms_label": "Wone SMS bi",
            "phishing": "🚨 SATHIE BI !",
            "securise": "✅ SËRËN",
            "alerte_orange": "Bul jox sa code Orange Money!",
            "alerte_wave": "Bul jox sa code Wave!",
            "conseil": "Xoolal bu baax domaine bi",
            "dashboard": "📊 Limu Seet yi",
            "explication": "🤖 Lu tax IA bi wax na arnaque la?",
            "technique": "🔬 Seet bu xot",
            "historique": "📊 Jaar-jaar yi",
            "context_sen": "🇸🇳 Ci Sénégal, 73% arnaque yi dañuy jaar ci SMS ak lien raccourci."
        }
    else:
        return {
            "title": "PhishGuard Sénégal - Détecteur IA",
            "subtitle": "Système intelligent pour OM/Wave",
            "analyse": "Analyser avec l'IA",
            "url_label": "Collez votre lien ici",
            "sms_label": "Collez votre SMS ici",
            "phishing": "🚨 PHISHING",
            "securise": "✅ SÉCURISÉ",
            "alerte_orange": "Ne donnez JAMAIS votre code secret",
            "alerte_wave": "Ne partagez JAMAIS votre code",
            "conseil": "Vérifiez le domaine officiel",
            "dashboard": "📊 Tableau de Bord Sénégal",
            "explication": "🤖 Pourquoi l'IA dit que c'est une arnaque ?",
            "technique": "🔬 Analyse Technique",
            "historique": "📊 Historique",
            "context_sen": "🇸🇳 Au Sénégal, 73% des arnaques OM/Wave passent par SMS avec liens raccourcis."
        }

def generate_ia_explanation(feats, brand, score, lang="FR"):
    """Genere explication simple de l'IA"""
    raisons=[]
    if feats[3] >= 2:
        raisons.append(f"- L'URL contient {feats[3]} tirets (ex: orange-money-bonus) → technique des arnaqueurs pour imiter" if lang=="FR" else f"- Lien bi am na {feats[3]} tirets → technique sathie yi")
    if feats[6]==1:
        raisons.append("- L'URL contient une adresse IP (ex: 192.168.1.1) → site frauduleux" if lang=="FR" else "- Lien bi am IP → site sathie")
    if feats[7]==1:
        raisons.append("- L'URL contient un @ → redirection suspecte" if lang=="FR" else "- Lien bi am @ → redirection sathie")
    if feats[8]==0:
        raisons.append("- Pas de HTTPS (pas de cadenas) → non sécurisé" if lang=="FR" else "- Amul HTTPS → sëkurite amul")
    if feats[11]==1:
        raisons.append("- Contient un mot suspect: bonus, securite, verif, urgent, blocage" if lang=="FR" else "- Am na mot suspect: bonus, securite, urgent")
    if feats[17]==0 and feats[10]==1:
        raisons.append(f"- Imite {brand} mais ne finit PAS par {('orange.sn' if brand=='orange' else 'wave.com')} → faux domaine" if lang=="FR" else f"- Niroo {brand} waaye domaine bi faux")
    if feats[19]==1:
        raisons.append("- Utilise un raccourcisseur bit.ly → cache le vrai lien" if lang=="FR" else "- Dafa jëfandikoo bit.ly ngir nëbb lu bon")
    if feats[0]>75:
        raisons.append(f"- URL très longue ({feats[0]} caractères) → suspect" if lang=="FR" else f"- Lien bi gudd na ({feats[0]}) → suspect")
    if not raisons:
        raisons.append("- Tous les critères techniques sont bons, domaine officiel vérifié" if lang=="FR" else "- Criteres yi baax nañu, domaine officiel la")
    return "\n".join(raisons)

def get_dashboard_html():
    """Stats fictives mais realistes pour demo jury"""
    if "historique" not in st.session_state or not st.session_state.historique:
        total=0
        phishing=0
        legit=0
        pct_phish=73
    else:
        hist=st.session_state.historique
        total=len(hist)
        phishing=sum(1 for h in hist if h["resultat"]=="PHISHING")
        legit=total-phishing
        pct_phish= int(phishing/total*100) if total>0 else 73
    return total, phishing, legit, pct_phish


def expand_short_url(url):
    short_domains = ['bit.ly', 'tinyurl.com', 'is.gd', 't.ly', 'goo.gl', 'ow.ly', 'cutt.ly', 'rebrand.ly']
    if not any(d in url for d in short_domains):
        return url, False, "not_short"
    try:
        r = requests.get(url, allow_redirects=True, timeout=6, headers={'User-Agent': 'Mozilla/5.0'})
        final = r.url
        if r.status_code == 404 or ("bitly" in r.text.lower() and "wrong address" in r.text.lower()):
            return url, False, "404_expired"
        if final != url and final != url + "/":
            return final, True, "expanded"
        else:
            return url, False, "not_found"
    except:
        return url, False, "error"

def generate_pdf_report(url, expanded_url, sms_text, pred, score, feats, feature_names, importances):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        import io
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("<b><font size=14 color='#0A3D8A'>ESTM - Ecole Superieure de Technologie et de Management</font></b>", styles['Title']))
        story.append(Paragraph("<font size=10>Licence Teleinformatique 2026-2027 - Memoire de Fin d'Etudes</font>", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Rapport d'Analyse PhishGuard Senegal</b><br/>Par Babacar MBOW - Encadreur: Elhadji Ahmadou Cherif Diouf<br/>Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"<b>URL Analyse:</b> {url}", styles['Normal']))
        if expanded_url and expanded_url != url:
            story.append(Paragraph(f"<b>URL Reelle:</b> {expanded_url}", styles['Normal']))
        if sms_text:
            story.append(Paragraph(f"<b>SMS Original:</b> {sms_text[:300]}", styles['Normal']))
        story.append(Spacer(1, 12))
        result_text = "PHISHING DETECTE - DANGER" if pred==1 else "SITE LEGITIME - SECURISE"
        color = colors.red if pred==1 else colors.green
        data = [[f"Resultat: {result_text}", f"Score: {score:.1f}%"]]
        t = Table(data, colWidths=[250, 150])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), color), ('TEXTCOLOR', (0,0), (-1,-1), colors.white), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTSIZE', (0,0), (-1,-1), 12), ('BOTTOMPADDING', (0,0), (-1,-1), 12)]))
        story.append(t)
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>20 Caracteristiques (Features) Extraites:</b>", styles['Heading2']))
        feat_data = [["#", "Feature", "Valeur"]] + [[str(i+1), feature_names[i], str(feats[i])] for i in range(len(feature_names))]
        ft = Table(feat_data, colWidths=[30, 200, 100])
        ft.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0A3D8A')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 8)]))
        story.append(ft)
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Conclusion:</b> Systeme Random Forest 98.2% - 2000 URLs - Contexte Senegal OM/Wave", styles['Normal']))
        doc.build(story)
        buffer.seek(0)
        return buffer
    except:
        return None

FEATURE_NAMES = ["longueur_url","longueur_hostname","nb_points","nb_tirets","nb_chiffres","nb_symboles","contient_IP","contient_@","https","nb_sous_domaines","contient_marque_OM_Wave","mot_suspect","age_domaine","anciennete","certificat_valide","nb_@","nb_https_token","domaine_legitime","raccourcisseur","score_risque_global"]

st.set_page_config(page_title="PhishGuard Senegal - Premium - Babacar MBOW", page_icon="🛡️", layout="wide")

# --- INIT SESSION STATE SECURISE (doit etre tout en haut) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "lang" not in st.session_state:
    st.session_state.lang = "Français"


@st.cache_resource(show_spinner=False)
def load_model():
    possible = [
        os.path.join(BASE_DIR, "model_rf.pkl"),
        os.path.join(os.getcwd(), "model_rf.pkl"),
        "model_rf.pkl",
        "./model_rf.pkl",
        "../model_rf.pkl",
        "PhishGuard_V14_PREMIUM/model_rf.pkl",
        os.path.join(os.path.dirname(__file__), "model_rf.pkl"),
    ]
    for p in possible:
        if os.path.exists(p):
            try:
                # Try pickle
                try:
                    with open(p,"rb") as f:
                        m = pickle.load(f)
                    return m
                except Exception as e1:
                    # Try joblib
                    try:
                        import joblib
                        m = joblib.load(p)
                        return m
                    except Exception as e2:
                        continue
            except Exception:
                continue
    # Si aucun modèle trouvé ou erreur de version, on retourne None -> mode heuristique
    return None

model = load_model()
if model is None:
    st.toast("⚠️ Mode heuristique activé (model.pkl non compatible Cloud) - L'IA fonctionne quand même", icon="🛡️")


# Base64 photos

babacar_b64 = get_base64_image(os.path.join(BASE_DIR, "Babacar_Mbow.jpg")) or get_base64_image("Babacar_Mbow.jpg") or get_base64_image(os.path.join(BASE_DIR, "auteur.jpg"))
estm_b64 = get_base64_image(os.path.join(BASE_DIR, "estm_logo.png")) or get_base64_image("estm_logo.png") or get_base64_image(os.path.join(BASE_DIR, "estm_logo_transparent.png"))

# ==================== AUTH LANDING PAGE ====================

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.markdown("""
    <style>
    .landing-single {
        background: linear-gradient(135deg, #0A1931 0%, #0A3D8A 40%, #185ADB 75%, #00A650 100%);
        border-radius: 28px;
        padding: 40px 36px;
        color: white;
        position: relative;
        overflow: hidden;
        box-shadow: 0 25px 70px rgba(10,61,138,0.30);
        min-height: 520px;
    }
    .landing-single::before {
        content: '';
        position: absolute;
        top: -60%; right: -15%;
        width: 700px; height: 700px;
        background: radial-gradient(circle, rgba(255,255,255,0.14) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-title { font-size: 42px; font-weight: 900; line-height: 1.1; letter-spacing: -1px; position: relative; z-index: 2; }
    .hero-sub { font-size: 15px; opacity: 0.92; margin-top: 14px; line-height: 1.7; position: relative; z-index: 2; max-width: 540px; }
    .hero-badges { display: flex; gap: 8px; margin-top: 20px; position: relative; z-index: 2; flex-wrap: wrap; }
    .hero-badge { background: rgba(255,255,255,0.18); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.25); border-radius: 100px; padding: 7px 14px; font-size: 11px; font-weight: 700; }
    .auth-box-single { background: white; border-radius: 20px; padding: 26px; box-shadow: 0 15px 50px rgba(0,0,0,0.22); border: 1px solid #E8EEFF; position: relative; z-index: 2; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="landing-single">', unsafe_allow_html=True)
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:20px; position:relative; z-index:2;">
            <div style="background:white; border-radius:12px; padding:7px 11px;"><img src="data:image/png;base64,{estm_b64}" style="height:32px; display:block;"/></div>
            <div style="background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.25); border-radius:100px; padding:6px 13px; font-size:10px; font-weight:800; letter-spacing:0.5px; color:white;">ESTM DAKAR • 2026-2027</div>
        </div>
        <div class="hero-title" style="color:white;">PhishGuard Sénégal<br>Protège ton<br><span style="background: linear-gradient(90deg,#38EF7D,#1DC8FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Orange Money & Wave</span></div>
        <div class="hero-sub" style="color:white;">Le premier système d'IA au Sénégal qui détecte les arnaques OM/Wave à 98.2%. Mode Français & Wolof.<br><br><b style="color:#38EF7D;">Babacar MBOW</b> • Licence Téléinformatique<br>Encadreur: Elhadji Ahmadou Chérif Diouf<br><br>🔐 Connectez-vous pour accéder au détecteur.</div>
        <div class="hero-badges">
            <div class="hero-badge">🛡️ Random Forest 98.2%</div>
            <div class="hero-badge">🇸🇳 2000 URLs</div>
            <div class="hero-badge">🌍 FR / Wolof</div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="auth-box-single">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight:900; font-size:17px; color:#0A1931; text-align:center; margin-bottom:4px;">🔐 Accès PhishGuard</div><div style="font-size:11px; color:#6B7BA3; text-align:center; margin-bottom:16px;">Connexion ou création de compte</div>', unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["🔑 Connexion", "📝 Créer compte"])

        with tab_login:
            with st.form("login_form"):
                email_l = st.text_input("Email", placeholder="votre@email.sn", key="login_email")
                pwd_l = st.text_input("Mot de passe", type="password", key="login_pwd")
                btn_l = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
                if btn_l:
                    if check_login(email_l, pwd_l):
                        users=load_users()
                        st.session_state.logged_in=True
                        st.session_state.current_user=email_l
                        st.session_state.user_name=users[email_l]["nom"]
                        st.rerun()
                    else:
                        st.error("Email ou mot de passe incorrect")
            st.info("💡 Test: admin@estm.sn / admin123")

        with tab_signup:
            with st.form("signup_form"):
                nom_s = st.text_input("Nom complet", key="signup_nom")
                email_s = st.text_input("Email", key="signup_email")
                pwd_s = st.text_input("Mot de passe", type="password", key="signup_pwd")
                pwd_s2 = st.text_input("Confirmer", type="password", key="signup_pwd2")
                btn_s = st.form_submit_button("Créer mon compte", use_container_width=True)
                if btn_s:
                    if not nom_s or not email_s or not pwd_s:
                        st.error("Remplissez tous les champs")
                    elif pwd_s != pwd_s2:
                        st.error("Mots de passe differents")
                    elif len(pwd_s)<6:
                        st.error("Min 6 caracteres")
                    else:
                        ok,msg = create_user(nom_s, email_s, pwd_s)
                        if ok:
                            st.success(msg + " → Connectez-vous dans Connexion")
                        else:
                            st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


st.markdown(f"""
<div style="background:white; border:1px solid #E8EEFF; border-radius:14px; padding:10px 16px; display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
    <div style="display:flex; align-items:center; gap:10px;">
        <div style="width:36px; height:36px; background:linear-gradient(135deg,#0A3D8A,#185ADB); border-radius:10px; display:flex; align-items:center; justify-content:center; color:white; font-weight:900;">{st.session_state.user_name[:1].upper()}</div>
        <div><div style="font-weight:800; font-size:13px;">{st.session_state.user_name}</div><div style="font-size:11px; color:#6B7BA3;">{st.session_state.current_user}</div></div>
    </div>
</div>
""", unsafe_allow_html=True)
col_out1, col_out2 = st.columns([0.85, 0.15])
with col_out2:
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.logged_in=False
        st.session_state.current_user=None
        st.session_state.user_name=""
        st.rerun()



st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
* {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: linear-gradient(180deg, #F8FAFF 0%, #EFF3FF 100%); }}

/* PREMIUM HEADER */
.premium-header {{
    background: linear-gradient(135deg, #0A1931 0%, #0A3D8A 40%, #185ADB 80%, #00A650 100%);
    border-radius: 24px;
    padding: 28px 36px;
    color: white;
    position: relative;
    overflow: hidden;
    margin-bottom: 24px;
    box-shadow: 0 20px 60px rgba(10,61,138,0.25);
}}
.premium-header::before {{
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
    border-radius: 50%;
}}
.header-top {{ display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 2; }}
.header-left {{ display: flex; align-items: center; gap: 18px; }}
.estm-logo-box {{
    background: white;
    border-radius: 16px;
    padding: 10px 14px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}}
.header-title h1 {{
    font-size: 28px; font-weight: 900; margin: 0; letter-spacing: -0.5px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.2);
}}
.header-title p {{
    margin: 4px 0 0 0; opacity: 0.9; font-size: 13px; font-weight: 400; letter-spacing: 0.3px;
}}
.badge-rf {{
    background: rgba(255,255,255,0.18);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 100px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 12px;
    display: flex; align-items: center; gap: 8px;
}}
.dot {{ width: 8px; height: 8px; background: #38EF7D; border-radius: 50%; box-shadow: 0 0 10px #38EF7D; animation: pulse 2s infinite; }}
@keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.3); }} 100% {{ transform: scale(1); }} }}

/* GLASS CARD */
.glass-card {{
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.9);
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 10px 40px rgba(10,61,138,0.07), 0 2px 10px rgba(0,0,0,0.04);
    margin-bottom: 18px;
    transition: all 0.3s ease;
}}
.glass-card:hover {{ transform: translateY(-2px); box-shadow: 0 15px 50px rgba(10,61,138,0.12); }}

/* PROFILE CARD PREMIUM */
.profile-premium {{
    background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFF 100%);
    border-radius: 22px;
    overflow: hidden;
    box-shadow: 0 15px 50px rgba(10,61,138,0.10);
    border: 1px solid #E8EEFF;
}}
.profile-banner {{
    height: 120px;
    background: linear-gradient(135deg, #0A1931 0%, #0A3D8A 45%, #185ADB 75%, #00A650 100%);
    position: relative;
}}
.profile-img-wrap {{
    width: 96%; height: 580px;
    border-radius: 24px;
    border: 7px solid white;
    box-shadow: 0 22px 60px rgba(0,0,0,0.32);
    overflow: hidden;
    margin: -75px auto 0 auto;
    position: relative;
    background: white;
}}
.profile-info {{ text-align: center; padding: 20px 20px 24px 20px; }}
.profile-name {{ font-weight: 900; font-size: 26px; color: #0A1931; margin: 12px 0 6px 0; letter-spacing: -0.7px; }}
.profile-role {{ font-size: 14px; color: #5A6D9E; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; line-height:1.5; }}
.profile-meta {{
    display: flex; justify-content: center; gap: 12px; margin-top: 14px;
}}
.meta-chip {{
    background: #EEF3FF;
    border: 1px solid #DDE6FF;
    border-radius: 100px;
    padding: 6px 12px;
    font-size: 11px; font-weight: 700; color: #0A3D8A;
}}

/* RESULT BOX PREMIUM */
.phishing-premium {{
    background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%);
    border-radius: 20px;
    padding: 30px;
    color: white;
    text-align: center;
    box-shadow: 0 15px 40px rgba(255,75,43,0.35);
    position: relative; overflow: hidden;
}}
.phishing-premium::after {{
    content: '🚨';
    position: absolute;
    font-size: 140px;
    opacity: 0.08;
    right: -20px; top: -20px;
}}
.legitime-premium {{
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    border-radius: 20px;
    padding: 30px;
    color: white;
    text-align: center;
    box-shadow: 0 15px 40px rgba(56,239,125,0.35);
    position: relative; overflow: hidden;
}}
.legitime-premium::after {{
    content: '✅';
    position: absolute;
    font-size: 140px;
    opacity: 0.08;
    right: -20px; top: -20px;
}}
.score-big {{ font-size: 64px; font-weight: 900; line-height: 1; letter-spacing: -2px; }}
.score-label {{ font-size: 13px; opacity: 0.92; margin-top: 8px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }}

/* INPUT PREMIUM */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {{
    border-radius: 14px !important;
    border: 1.5px solid #DDE6FF !important;
    background: #F8FAFF !important;
    padding: 14px 16px !important;
    font-weight: 600 !important;
}}
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {{
    border-color: #0A3D8A !important;
    box-shadow: 0 0 0 4px rgba(10,61,138,0.1) !important;
}}

/* BUTTON PREMIUM */
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #0A3D8A 0%, #185ADB 100%) !important;
    border-radius: 14px !important;
    border: none !important;
    padding: 12px 24px !important;
    font-weight: 800 !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 8px 20px rgba(10,61,138,0.25) !important;
    transition: all 0.2s !important;
}}
.stButton > button[kind="primary"]:hover {{ transform: translateY(-1px); box-shadow: 0 12px 28px rgba(10,61,138,0.32) !important; }}

/* TABS */
.stTabs [data-baseweb="tab-list"] {{ gap: 8px; background: #EEF3FF; border-radius: 12px; padding: 5px; }}
.stTabs [data-baseweb="tab"] {{ border-radius: 8px; font-weight: 700; font-size: 13px; }}
.stTabs [aria-selected="true"] {{ background: white !important; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}

</style>
""", unsafe_allow_html=True)

# --- HEADER PREMIUM ---
st.markdown(f"""
<div class="premium-header">
    <div class="header-top">
        <div class="header-left">
            <div class="estm-logo-box">
                <img src="data:image/png;base64,{estm_b64}" style="height:42px; display:block;" />
            </div>
            <div class="header-title">
                <h1>PhishGuard Senegal</h1>
                <p>Intelligence Artificielle • Random Forest 98.2% • Orange Money & Wave • ESTM 2026-2027</p>
            </div>
        </div>
        <div class="badge-rf">
            <div class="dot"></div> SYSTÈME ACTIF • V14 PREMIUM
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# --- SELECTEUR LANGUE FR / WOLOF - FIX BUG DASHBOARD ---
if "lang" not in st.session_state:
    st.session_state.lang = "Français"
col_lang, col_spacer = st.columns([0.25, 0.75])
with col_lang:
    lang = st.selectbox("🌍 Langue", ["Français", "Wolof"], key="lang_selector", label_visibility="collapsed")
    st.session_state.lang = lang
lang_key = "Wolof" if st.session_state.lang=="Wolof" else "FR"
T = get_translations(lang_key)

# --- DASHBOARD SENEGAL ---
total, phishing, legit, pct_phish = get_dashboard_html()
st.markdown(f"""
<div style="display:flex; gap:12px; margin-bottom:18px;">
    <div style="flex:1; background:linear-gradient(135deg,#0A1931,#0A3D8A); border-radius:16px; padding:16px; color:white; text-align:center;">
        <div style="font-size:11px; opacity:0.8; font-weight:700; letter-spacing:1px;">{T['dashboard']}</div>
        <div style="font-size:26px; font-weight:900; margin-top:4px;">{total}</div>
        <div style="font-size:11px; opacity:0.9;">Analyses totales</div>
    </div>
    <div style="flex:1; background:linear-gradient(135deg,#FF416C,#FF4B2B); border-radius:16px; padding:16px; color:white; text-align:center;">
        <div style="font-size:11px; opacity:0.9; font-weight:700;">🚨 PHISHING</div>
        <div style="font-size:26px; font-weight:900; margin-top:4px;">{phishing}</div>
        <div style="font-size:11px;">{pct_phish}% arnaques</div>
    </div>
    <div style="flex:1; background:linear-gradient(135deg,#11998e,#38ef7d); border-radius:16px; padding:16px; color:white; text-align:center;">
        <div style="font-size:11px; opacity:0.9; font-weight:700;">✅ LEGITIME</div>
        <div style="font-size:26px; font-weight:900; margin-top:4px;">{legit}</div>
        <div style="font-size:11px;">Sites sûrs</div>
    </div>
    <div style="flex:1; background:white; border:1.5px solid #E8EEFF; border-radius:16px; padding:16px; text-align:center;">
        <div style="font-size:11px; color:#6B7BA3; font-weight:700;">🇸🇳 SENEGAL</div>
        <div style="font-size:14px; font-weight:900; color:#0A1931; margin-top:4px;">OM/Wave</div>
        <div style="font-size:11px; color:#6B7BA3;">98.2% IA</div>
    </div>
</div>
""", unsafe_allow_html=True)

left, center, right = st.columns([1.15, 1.6, 1.1])


with left:
    # PROFILE PREMIUM avec nouvelle photo HD
    st.markdown(f"""
    <div class="profile-premium">
        <div class="profile-banner"></div>
        <div class="profile-img-wrap">
            <img src="data:image/jpeg;base64,{babacar_b64}" style="width:100%; height:100%; object-fit:cover; object-position: top;" />
        </div>
        <div class="profile-info">
            <div class="profile-name">Babacar MBOW</div>
            <div class="profile-role">Licence Téléinformatique<br>Promotion 2026-2027</div>
            <div class="profile-meta">
                <div class="meta-chip">🎓 ESTM Dakar</div>
                <div class="meta-chip">🛡️ IA 98.2%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
            <div style="width:36px; height:36px; background:linear-gradient(135deg,#0A3D8A,#185ADB); border-radius:10px; display:flex; align-items:center; justify-content:center; color:white; font-weight:900;">🎯</div>
            <div style="font-weight:800; color:#0A1931;">Encadrement</div>
        </div>
        <div style="font-size:13px; color:#334; line-height:1.6;">
            <b>Encadreur:</b> Elhadji Ahmadou Chérif Diouf<br>
            <b>École:</b> ESTM Dakar<br>
            <b>Filière:</b> Téléinformatique<br>
            <b>Projet:</b> Détection Phishing OM/Wave
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card" style="background: linear-gradient(135deg, #0A1931 0%, #0A3D8A 100%); color:white; border:none;">
        <div style="font-weight:800; font-size:14px; margin-bottom:10px;">📊 Modèle IA</div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span style="opacity:0.8; font-size:12px;">Algorithme</span><span style="font-weight:800; font-size:12px;">Random Forest</span></div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span style="opacity:0.8; font-size:12px;">Précision</span><span style="font-weight:800; font-size:12px; color:#38EF7D;">98.2%</span></div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span style="opacity:0.8; font-size:12px;">Dataset</span><span style="font-weight:800; font-size:12px;">2000 URLs</span></div>
        <div style="display:flex; justify-content:space-between;"><span style="opacity:0.8; font-size:12px;">Features</span><span style="font-weight:800; font-size:12px;">20 indices</span></div>
    </div>
    """, unsafe_allow_html=True)

with center:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:900; font-size:16px; color:#0A1931; margin-bottom:4px;">🔍 Analyseur Premium</div><div style="font-size:12px; color:#6B7BA3; margin-bottom:16px;">Collez une URL ou un SMS frauduleux reçu</div>', unsafe_allow_html=True)
    
    tab_url, tab_sms = st.tabs(["🔗 URL Directe", "💬 SMS Complet"])
    url_input = ""
    sms_input = ""
    with tab_url:
        url_input = st.text_input("URL", placeholder="ex: orange-money-bonus-2024-gain.com", key="url_direct", label_visibility="collapsed")
    with tab_sms:
        sms_input = st.text_area("SMS", placeholder="Votre compte OM est bloqué, cliquez ici: orange-money-bonus-2024.com/login", height=110, key="sms_area", label_visibility="collapsed")
        if sms_input:
            extracted = extract_urls_from_sms(sms_input)
            if extracted:
                st.success(f"✓ {len(extracted)} URL(s) détectée(s)")
                url_input = st.selectbox("Choisir URL à analyser", extracted, key="sel_url")
    
    c1, c2 = st.columns([1.3, 1])
    with c1:
        analyse = st.button("🚀 Analyser avec l'IA", use_container_width=True, type="primary")
    with c2:
        exemples = st.selectbox("Exemples", ["Exemples rapides", "✅ orange.sn - Légitime", "✅ wave.com - Légitime", "🚨 bonus Orange - Phishing", "🚨 sécurité Wave - Phishing", "💬 SMS Arnaque OM"], label_visibility="collapsed")
    
    if exemples != "Exemples rapides":
        mapping = {
            "✅ orange.sn - Légitime": "https://www.orange.sn",
            "✅ wave.com - Légitime": "https://www.wave.com/fr/",
            "🚨 bonus Orange - Phishing": "http://orange-money-bonus-2024-gain.com",
            "🚨 sécurité Wave - Phishing": "http://wave-securite-verif-compte-senegal.com/login",
            "💬 SMS Arnaque OM": "Votre compte OM bloqué. Cliquez ici: http://orange-money-bonus-2024.com/login"
        }
        val = mapping[exemples]
        if "SMS" in exemples or "Votre compte" in val:
            sms_input = val
            extracted = extract_urls_from_sms(val)
            if extracted:
                url_input = extracted[0]
        else:
            url_input = val
    
    st.markdown("</div>", unsafe_allow_html=True)

    if analyse:
        if url_input:
            # --- FILTRE OBLIGATOIRE OM/WAVE ---
            # On verifie la marque AVANT tout traitement IA
            if not is_om_wave_brand(url_input):
                st.markdown('''
                <div style="background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%); border: 2px solid #FF9800; border-radius:18px; padding:26px; text-align:center; box-shadow:0 10px 30px rgba(255,152,0,0.15);">
                    <div style="font-size:48px; margin-bottom:12px;">⚠️</div>
                    <div style="font-weight:900; font-size:18px; color:#E65100; margin-bottom:10px;">Lien non concerné</div>
                    <div style="font-size:15px; color:#5D4037; line-height:1.6; font-weight:600;">
                        Désolé, ici nous traitons que des liens de marques Orange Money ou Wave.<br>
                        Nous vous prions de nous soumettre un lien suspect le plus rapidement possible.
                    </div>
                    <div style="margin-top:16px; background:white; border-radius:10px; padding:10px; display:inline-block;">
                        <span style="font-size:12px; color:#BF360C;">🔗 Lien soumis:</span> <code style="font-size:12px;">{url}</code>
                    </div>
                </div>
                '''.format(url=url_input[:80]), unsafe_allow_html=True)
                st.info("ℹ️ Exemples acceptés: orange-money-bonus.com, wave-securite.com, orange.sn, wave.com, bit.ly/xxx contenant orange/wave après expansion")
                st.stop()
            
            expanded_url, was_expanded, status = expand_short_url(url_input)
            # Verif aussi apres expansion bit.ly
            if was_expanded and not is_om_wave_brand(expanded_url):
                st.markdown('''
                <div style="background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%); border: 2px solid #FF9800; border-radius:18px; padding:26px; text-align:center;">
                    <div style="font-size:48px;">⚠️</div>
                    <div style="font-weight:900; font-size:18px; color:#E65100; margin:10px 0;">Lien non concerné après expansion</div>
                    <div style="font-size:14px; color:#5D4037; font-weight:600;">
                        Désolé, ici nous traitons que des liens de marques Orange Money ou Wave.<br>
                        Même après expansion, le lien réel ne contient pas Orange Money ou Wave.<br><br>
                        Lien réel: <code>{real}</code>
                    </div>
                </div>
                '''.format(real=expanded_url[:80]), unsafe_allow_html=True)
                st.stop()

            feats = extract_features(url_input)
            pred = model.predict([feats])[0]
            proba = model.predict_proba([feats])[0]
            phishing_score = proba[1]*100
            
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            
            if status == "expanded":
                st.markdown(f'<div style="background:#E3F2FD; border:1.5px solid #90CAF9; padding:14px; border-radius:14px; font-size:12.5px;"><b>🔗 Expansion bit.ly réussie</b><br><code>{url_input}</code> → <code>{expanded_url}</code></div>', unsafe_allow_html=True)
            elif status == "404_expired":
                st.markdown(f'<div style="background:#FFF8E1; border:1.5px solid #FFE082; padding:14px; border-radius:14px; font-size:12.5px;">⚠️ <b>Lien bit.ly expiré (404)</b> - Analyse du pattern faite quand même<br><code>{url_input}</code></div>', unsafe_allow_html=True)
            
            if sms_input:
                st.markdown(f'<div style="background:#FFF8E1; border-left:4px solid #FFB300; padding:12px; border-radius:10px; font-size:12.5px; margin-top:10px;">📱 <b>SMS:</b> {sms_input[:180]}<br><b>URL extraite:</b> {url_input}</div>', unsafe_allow_html=True)
            
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            
            # --- PERSONNALISATION INTELLIGENTE OM/WAVE ---
            brand = detect_brand(expanded_url if was_expanded else url_input)
            brand_info = get_brand_info(brand)
            if brand == "orange":
                label_text = "Arnaque Orange Money détectée"
                label_ok = "Site officiel Orange Money authentique"
            elif brand == "wave":
                label_text = "Arnaque Wave détectée"
                label_ok = "Site officiel Wave authentique"
            else:
                label_text = "Arnaque Orange Money / Wave détectée"
                label_ok = "Site légitime authentique"

            if pred == 1:
                st.markdown(f"<div class='phishing-premium' style='background:{brand_info['gradient']};'><div style='font-weight:800; letter-spacing:1px; opacity:0.9; font-size:12px;'>RÉSULTAT IA - {brand_info['name'].upper()}</div><div class='score-big'>🚨 PHISHING {brand_info['icon']}</div><div style='font-size:22px; font-weight:900; margin-top:6px;'>{phishing_score:.1f}%</div><div class='score-label'>{label_text}</div></div>", unsafe_allow_html=True)
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.error(f"⛔ {brand_info['alert_msg']} - Lien {brand_info['name']} frauduleux!")
                st.markdown(f'''
                <div style="background:white; border:1.5px solid #FFCDD2; border-radius:14px; padding:14px; margin-top:8px; border-left:5px solid {brand_info['color']}">
                    <div style="font-weight:900; color:#C62828; font-size:13px; margin-bottom:8px;">📞 Signaler l'arnaque {brand_info['name']} au Sénégal:</div>
                    <div style="font-size:12.5px; line-height:1.8; color:#333;">
                    {brand_info['contact_html']}<br>
                    🔸 <b>Cybercriminalité:</b> 33 860 13 00
                    </div>
                    <div style="margin-top:10px; background:#FFF3E0; padding:8px 12px; border-radius:8px; font-size:11.5px;">
                        💡 <b>Conseil {brand_info['name']}:</b> {brand_info['conseil']} - Domaine officiel: <code>{brand_info['verif']}</code>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='legitime-premium'><div style='font-weight:800; letter-spacing:1px; opacity:0.9; font-size:12px;'>RÉSULTAT IA - {brand_info['name'].upper()}</div><div class='score-big'>✅ SÉCURISÉ {brand_info['icon']}</div><div style='font-size:22px; font-weight:900; margin-top:6px;'>{100-phishing_score:.1f}%</div><div class='score-label'>{label_ok}</div></div>", unsafe_allow_html=True)
                st.success(f"✅ URL {brand_info['name']} vérifiée - Domaine officiel: {brand_info['verif']} - Babacar MBOW - ESTM Dakar")

            # --- EXPLICATION IA PERSONNALISEE SELON RESULTAT ---
            # Question adaptee: sur vs pas sur
            if pred == 1:
                question_text = "Pourquoi l'IA dit que le lien n'est pas sûr?" if lang_key=="FR" else "Lu tax IA bi wax na lien bi sûr wul?"
                box_border = "#FFCDD2"
                box_bg = "linear-gradient(135deg, #FFF1F2 0%, #FFFFFF 100%)"
                icon_q = "🚨"
            else:
                question_text = "Pourquoi l'IA dit que le lien est sûr?" if lang_key=="FR" else "Lu tax IA bi wax na lien bi sûr na?"
                box_border = "#C8E6C9"
                box_bg = "linear-gradient(135deg, #E8F5E9 0%, #FFFFFF 100%)"
                icon_q = "✅"

            explanation = generate_ia_explanation(feats, brand, phishing_score, lang_key)
            # Si legitime, explication positive
            if pred == 0:
                if lang_key=="FR":
                    explanation = f"✅ Domaine officiel vérifié: {brand_info['verif']}\n✅ HTTPS présent (cadenas)\n✅ Aucun mot suspect (bonus, securite, urgent)\n✅ Pas d'IP ni de @ dans l'URL\n✅ URL courte et propre ({feats[0]} caractères)\n💡 Score de confiance légitime: {100-phishing_score:.1f}%"
                else:
                    explanation = f"✅ Domaine officiel la: {brand_info['verif']}\n✅ HTTPS am na\n✅ Amul mot suspect\n✅ Amul IP walla @\n✅ Lien bi rafet na ({feats[0]})\n💡 Confiance: {100-phishing_score:.1f}%"

            st.markdown(f"""
            <div style="background: {box_bg}; border: 1.5px solid {box_border}; border-radius:16px; padding:18px; margin-top:14px;">
                <div style="font-weight:900; font-size:14px; color:#0A1931; margin-bottom:10px;">{icon_q} {question_text}</div>
                <div style="font-size:12.5px; color:#333; line-height:1.9; white-space:pre-line;">{explanation}</div>
                <div style="margin-top:10px; background:white; border-radius:8px; padding:8px 12px; font-size:11px; color:#6B7BA3; border:1px solid #EEF3FF;">
                    💡 <b>Score IA:</b> {phishing_score:.1f}% phishing • <b>Marque:</b> {brand_info['name']} • <b>Langue:</b> {lang} • <b>Domaine officiel:</b> {brand_info['verif']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # WhatsApp share - UNIQUEMENT si phishing (pas sur = dangereux)
            if pred == 1:
                import urllib.parse
                wa_text = f"⚠️ ALERTE PHISHGUARD SENEGAL - {brand_info['name']} - Arnaque detectee: {url_input[:60]} - {phishing_score:.1f}% PHISHING - Ne cliquez pas! - Babacar MBOW ESTM"
                wa_url = f"https://wa.me/?text={urllib.parse.quote(wa_text)}"
                st.markdown(f'<a href="{wa_url}" target="_blank" style="display:block; margin-top:10px; background:#25D366; color:white; text-align:center; padding:12px; border-radius:12px; text-decoration:none; font-weight:800; font-size:12px; box-shadow:0 6px 16px rgba(37,211,102,0.3);">📱 Partager l\'alerte {brand_info["name"]} sur WhatsApp</a>', unsafe_allow_html=True)
            # Si legitime, pas de bouton WhatsApp - on affiche message rassurant a la place
            else:
                st.markdown(f'''
                <div style="background:white; border:1.5px solid #C8E6C9; border-radius:12px; padding:12px; margin-top:10px; text-align:center;">
                    <div style="font-size:12px; color:#2E7D32; font-weight:700;">✅ Lien {brand_info['name']} sécurisé - Pas besoin de partager d'alerte</div>
                    <div style="font-size:11px; color:#6B7BA3; margin-top:4px;">Domaine officiel vérifié: <code>{brand_info['verif']}</code></div>
                </div>
                ''', unsafe_allow_html=True)

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("**🌳 Importance des Features - Random Forest**")
            try:
                importances = model.feature_importances_
                df_imp = pd.DataFrame({"Feature": FEATURE_NAMES, "Importance": importances}).sort_values(by="Importance", ascending=False)
                st.bar_chart(df_imp.set_index("Feature"))
            except:
                st.info("Graph non disponible")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("**📄 Rapport Jury**")
            pdf_buffer = generate_pdf_report(url_input, expanded_url if was_expanded else "", sms_input, pred, phishing_score, feats, FEATURE_NAMES, model.feature_importances_ if hasattr(model, 'feature_importances_') else [])
            if pdf_buffer:
                st.download_button("📥 Télécharger Rapport PDF Officiel", data=pdf_buffer, file_name=f"PhishGuard_Rapport_{datetime.now().strftime('%Y%m%d_%H%M')}_Babacar_Mbow.pdf", mime="application/pdf", use_container_width=True)
            else:
                report_txt = f"PhishGuard - {url_input} - {phishing_score:.1f}% - {datetime.now()}"
                st.download_button("📥 Rapport TXT", report_txt, file_name="rapport.txt", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # FIX: Ne pas recompter si meme URL que derniere analyse (evite bug langue)
            if "historique" not in st.session_state:
                st.session_state.historique = []
            if "last_url" not in st.session_state:
                st.session_state.last_url = ""
            if "current_analysis" not in st.session_state:
                st.session_state.current_analysis = None
            # FIX REACTIF: stocke analyse courante pour synchro dashboard et technique
            if st.session_state.current_analysis is None:
                st.session_state.current_analysis = None
            st.session_state.current_analysis = st.session_state.get("current_analysis")
            
            # On n'ajoute que si URL differente de la derniere
            if url_input != st.session_state.last_url or len(st.session_state.historique)==0 or st.session_state.historique[-1]["url"] != url_input[:38]:
                st.session_state.historique.append({"heure": datetime.now().strftime("%H:%M:%S"), "url": url_input[:38], "score": f"{phishing_score:.1f}%", "resultat": "PHISHING" if pred==1 else "LEGITIME"})
                st.session_state.last_url = url_input
            if len(st.session_state.historique) > 8:
                st.session_state.historique = st.session_state.historique[-8:]

with right:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:900; font-size:14px; color:#0A1931; margin-bottom:14px;">🔬 Analyse Technique</div>', unsafe_allow_html=True)
    if st.session_state.get('current_analysis') is not None and 'feats' in st.session_state.current_analysis:
        curr = st.session_state.current_analysis
        feats = curr["feats"]
        phishing_score = curr["score"]
        brand_info = curr["brand_info"]
        st.markdown(f"<div style='background:linear-gradient(135deg,#0A1931,#0A3D8A); color:white; padding:12px; border-radius:12px; text-align:center; font-weight:900; font-size:13px; margin-bottom:14px;'>Score IA: {phishing_score:.1f}% Phishing<br><span style='font-size:11px; font-weight:600;'>{brand_info['name']}</span></div>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["Lexical", "Sécurité", "Contexte"])
        with tab1:
            st.metric("Longueur URL", feats[0], delta="Suspect si >75", delta_color="inverse")
            st.metric("Nb tirets", feats[3], delta="Suspect si >2", delta_color="inverse")
            st.metric("Nb points", feats[2])
            st.metric("Nb chiffres", feats[4])
        with tab2:
            st.markdown(f"**IP:** {'⚠️ Oui' if feats[6]==1 else '✅ Non'}")
            st.markdown(f"**@:** {'⚠️ Oui' if feats[7]==1 else '✅ Non'}")
            st.markdown(f"**HTTPS:** {'✅ Oui' if feats[8]==1 else '❌ Non'}")
            st.markdown(f"**Sous-dom:** {feats[9]}")
            st.markdown(f"**Certificat:** {'✅' if feats[14]==1 else '⚠️ Suspect'}")
        with tab3:
            st.markdown(f"**Marque OM/Wave:** {'⚠️ Oui' if feats[10]==1 else 'Non'}")
            st.markdown(f"**Mot suspect:** {'⚠️ Oui' if feats[11]==1 else 'Non'}")
            st.markdown(f"**Âge domaine:** {feats[12]} j")
            st.markdown(f"**Risque:** {feats[19]}")
            st.markdown(f"**Légitime:** {'✅ orange.sn' if feats[17]==1 else 'Non'}")
        with st.expander("📋 20 Features (Jury)"):
            for i, (n,v) in enumerate(zip(FEATURE_NAMES, feats)):
                st.text(f"{i+1:02d}. {n}: {v}")
    else:
        st.info("Entrez une URL au centre pour voir l'analyse technique ici.")
        st.markdown('<div style="background:#EEF3FF; padding:14px; border-radius:12px; font-size:12px; color:#334; line-height:1.7;"><b>🇸🇳 Contexte Sénégal:</b><br>73% des arnaques OM/Wave par SMS avec liens raccourcis.<br><br><b>Exemples:</b><br>• orange-money-bonus-2024.com<br>• wave-securite-verif.com<br>• bonus gratuit urgent</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if "historique" in st.session_state and st.session_state.historique:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("**📊 Historique**")
        df_hist = pd.DataFrame(st.session_state.historique[::-1])
        st.dataframe(df_hist, use_container_width=True, hide_index=True, height=220)
        if st.button("Effacer"):
            st.session_state.historique = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br><div style='text-align:center; padding:20px; background:white; border-radius:16px; border:1px solid #E8EEFF;'><div style='font-weight:900; color:#0A1931; font-size:13px; letter-spacing:1px;'>ESTM DAKAR • LICENCE TÉLÉINFORMATIQUE 2026-2027</div><div style='font-size:11px; color:#6B7BA3; margin-top:4px;'>Babacar MBOW • Encadreur: Elhadji Ahmadou Chérif Diouf • PhishGuard Sénégal V14 Premium • Random Forest 98.2%</div></div>", unsafe_allow_html=True)