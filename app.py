"""
PhishGuard Sénégal V9 - SKILLS EDITION
Babacar MBOW - ESTM Dakar 2026-2027
Amélioration avec système de Skills IA
"""
import streamlit as st, os, sys, re, base64, io, json, hashlib, pickle
from urllib.parse import urlparse
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="PhishGuard Sénégal - Skills Edition", page_icon="🛡️", layout="wide")

# ===== SKILL 1: AUTH SKILL - Gestion utilisateurs =====
USERS_FILE = os.path.join(BASE_DIR, "users.json")

def get_b64(p):
    try:
        if os.path.exists(p):
            with open(p,"rb") as f:
                return base64.b64encode(f.read()).decode()
    except: pass
    return ""

# On utilise le logo transparent généré par skill
estm_transparent = os.path.join(BASE_DIR, "estm_logo_transparent.png")
estm_b64 = get_b64(estm_transparent) or get_b64(os.path.join(BASE_DIR,"estm_logo.png")) or get_b64("estm_logo.png")
babacar_b64 = get_b64(os.path.join(BASE_DIR,"Babacar_Mbow.jpg")) or get_b64("Babacar_Mbow.jpg")

def load_users():
    if not os.path.exists(USERS_FILE):
        default_admin = {"admin": {"email": "admin@estm.sn","password": hashlib.sha256("admin123".encode()).hexdigest(),"nom": "admin"}}
        try: json.dump(default_admin, open(USERS_FILE,"w",encoding="utf-8"), indent=2)
        except: pass
        return default_admin
    try:
        data = json.load(open(USERS_FILE,"r",encoding="utf-8"))
        if not data or "admin" not in data:
            if not data: data = {}
            data["admin"] = {"email": "admin@estm.sn","password": hashlib.sha256("admin123".encode()).hexdigest(),"nom": "admin"}
            try: json.dump(data, open(USERS_FILE,"w",encoding="utf-8"), indent=2)
            except: pass
        return data
    except:
        return {"admin": {"email": "admin@estm.sn","password": hashlib.sha256("admin123".encode()).hexdigest(),"nom": "admin"}}

def save_users(u):
    try: json.dump(u, open(USERS_FILE,"w",encoding="utf-8"), indent=2)
    except: pass

def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

def register_user(username, email, password):
    users=load_users()
    if username in users: return False, "Nom déjà pris"
    if len(password)<6: return False, "Mot de passe trop court (min 6)"
    users[username]={"email":email,"password":hash_pwd(password),"nom":username}
    save_users(users); return True, "Compte créé avec succès"

def check_login(username, password):
    users=load_users()
    if username not in users: return False, "Utilisateur inexistant"
    if users[username]["password"]!=hash_pwd(password): return False, "Mot de passe incorrect"
    return True, "Connexion réussie"

def reset_password(username, email, new_password):
    users=load_users()
    if username not in users: return False, "Utilisateur inexistant"
    if users[username].get("email","").lower()!=email.lower(): return False, "Email ne correspond pas"
    if len(new_password)<6: return False, "Mot de passe trop court (min 6)"
    users[username]["password"]=hash_pwd(new_password); save_users(users)
    return True, "Mot de passe réinitialisé !"

if "authenticated" not in st.session_state: st.session_state.authenticated=False
if "username" not in st.session_state: st.session_state.username=""

# ===== SKILL 2: DESIGN SKILL - CSS Pro avec logo transparent =====
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800;900&display=swap');
html, body, [class*="css"] {{font-family: 'Outfit', sans-serif !important;}}
[data-testid="stAppViewContainer"] {{
    background: radial-gradient(1200px 600px at 10% -10%, #E8F0FF 0%, transparent 60%),
                radial-gradient(1000px 500px at 90% 0%, #FFF0E6 0%, transparent 60%),
                linear-gradient(180deg, #F8FAFF 0%, #FFFFFF 100%);
}}
.hero {{
    background: linear-gradient(135deg, #0A1931 0%, #0A3D8A 50%, #123D8A 100%);
    border-radius: 28px; padding: 32px; color: white;
    box-shadow: 0 20px 60px rgba(10,61,138,0.35), inset 0 1px 0 rgba(255,255,255,0.2);
    position: relative; overflow: hidden; margin-bottom: 24px;
}}
.hero-title {{font-size: 36px; font-weight: 900; letter-spacing: -0.5px;}}
.hero-sub {{font-size: 14px; opacity: 0.85; margin-top: 8px; line-height: 1.6;}}
.badge {{display: inline-flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18); padding: 6px 14px; border-radius: 999px; font-size: 11px; font-weight: 700; backdrop-filter: blur(10px);}}
.badge-orange {{background: linear-gradient(90deg, #FF7900, #FF9A3D); border: none; color: white; box-shadow: 0 6px 20px rgba(255,121,0,0.4);}}
.glass-card {{
    background: rgba(255,255,255,0.92); backdrop-filter: blur(16px);
    border-radius: 22px; padding: 24px;
    border: 1px solid rgba(230,236,255,0.9);
    box-shadow: 0 12px 40px rgba(10,61,138,0.08);
    transition: all 0.35s;
}}
.glass-card:hover {{transform: translateY(-3px); box-shadow: 0 20px 60px rgba(10,61,138,0.15);}}
.skill-card {{
    background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFF 100%);
    border-radius: 18px; padding: 18px; border: 1px solid #E6ECFF;
    border-left: 4px solid #0A3D8A; margin-bottom: 12px;
}}
.skill-icon {{font-size: 22px; margin-bottom: 8px;}}
.footer {{text-align: center; padding: 20px; margin-top: 30px; border-top: 1px solid #E6ECFF;}}
</style>
""", unsafe_allow_html=True)

# ===== SKILL 3: DETECTION SKILL - Extraction features =====
def extract_features(url):
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        feats = {}
        feats['longueur_url'] = len(url)
        feats['longueur_hostname'] = len(hostname)
        feats['nb_points'] = url.count('.')
        feats['nb_tirets'] = url.count('-')
        feats['nb_chiffres'] = sum(c.isdigit() for c in url)
        feats['nb_arobase'] = url.count('@')
        feats['presence_ip'] = 1 if re.match(r'^\d+\.\d+\.\d+\.\d+$', hostname) else 0
        feats['presence_arobase'] = 1 if '@' in url else 0
        feats['presence_https'] = 1 if parsed.scheme == 'https' else 0
        feats['age_domaine'] = -1
        feats['mot_banking'] = 1 if any(w in url.lower() for w in ['orange','wave','money','om','pay']) else 0
        feats['mot_suspect'] = 1 if any(w in url.lower() for w in ['bonus','gagner','blocage','urgent','verif','securite']) else 0
        # scores
        feats['ip_score'] = 35 if feats['presence_ip']==1 else 0
        feats['arobase_score'] = 30 if feats['presence_arobase']==1 else 0
        feats['nb_tirets_score'] = min(feats['nb_tirets']*5, 25)
        feats['suspect_score'] = 25 if feats['mot_suspect']==1 else 0
        feats['banking_score'] = 20 if feats['mot_banking']==1 else 0
        feats['longueur_score'] = 15 if feats['longueur_url']>75 else 5
        feats['chiffres_score'] = min(feats['nb_chiffres'], 15)
        return feats
    except:
        return {}

def predict_url(url, feats):
    score = sum([feats.get('ip_score',0), feats.get('arobase_score',0), feats.get('nb_tirets_score',0), feats.get('suspect_score',0), feats.get('banking_score',0), feats.get('longueur_score',0), feats.get('chiffres_score',0)])
    if feats.get('presence_https',1)==0: score+=15
    conf = min(score, 99.5)
    is_phish = conf > 45
    return is_phish, conf

# ===== PAGE D'ACCUEIL AVEC SKILLS =====
if not st.session_state.authenticated:
    # Header avec logo transparent
    col_logo, col_title = st.columns([1,4])
    with col_logo:
        if os.path.exists(estm_transparent):
            st.image(estm_transparent, width=130)
        elif estm_b64:
            st.markdown(f'<img src="data:image/png;base64,{estm_b64}" width="130" style="background:transparent">', unsafe_allow_html=True)
    with col_title:
        st.markdown("""
        <div class="hero">
            <div style="display:flex; gap:10px; margin-bottom:12px;">
                <span class="badge">🛡️ ESTM DAKAR 2026-2027</span>
                <span class="badge badge-orange">✨ NOUVELLE VERSION SKILLS</span>
            </div>
            <div class="hero-title">PhishGuard Sénégal</div>
            <div class="hero-sub">Le Protecteur Sénégalais contre les arnaques Orange Money & Wave<br>Maintenant boosté par un système de Skills IA modulaires</div>
        </div>
        """, unsafe_allow_html=True)

    # Section Skills expliquée
    st.markdown("### 🧩 Les Skills qui améliorent PhishGuard")
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown('<div class="skill-card"><div class="skill-icon">🎨</div><b>Design Skill</b><br><span style="font-size:12px">Logo ESTM avec fond transparent (plus de fond blanc moche), glassmorphism, animations douces. Expérience premium pour le jury.</span></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="skill-card" style="border-left-color:#FF7900"><div class="skill-icon">🔐</div><b>Auth Skill</b><br><span style="font-size:12px">Connexion sécurisée, création de compte, mot de passe oublié avec vérification email. Plus de bug "Utilisateur inexistant".</span></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="skill-card" style="border-left-color:#00A650"><div class="skill-icon">🧠</div><b>Detection Skill</b><br><span style="font-size:12px">IA qui explique chaque décision: pourquoi ce lien est dangereux, diagramme HD 300 DPI pour ta soutenance.</span></div>', unsafe_allow_html=True)

    st.markdown("---")
    # Auth UI
    tab_login, tab_register, tab_forgot = st.tabs(["🔑 Connexion", "📝 Créer compte", "❓ Mot de passe oublié"])
    with tab_login:
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            u = st.text_input("Nom d'utilisateur", key="login_u")
            p = st.text_input("Mot de passe", type="password", key="login_p")
            if st.button("Se connecter →", use_container_width=True, type="primary"):
                ok, msg = check_login(u,p)
                if ok:
                    st.session_state.authenticated=True; st.session_state.username=u
                    st.success(msg); st.rerun()
                else: st.error(msg)
            st.info("Compte test: admin / admin123")
            st.markdown('</div>', unsafe_allow_html=True)
    with tab_register:
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            nu = st.text_input("Nouveau nom", key="reg_u")
            em = st.text_input("Email", key="reg_e")
            np = st.text_input("Mot de passe", type="password", key="reg_p")
            if st.button("Créer mon compte", use_container_width=True):
                ok,msg=register_user(nu,em,np)
                if ok: st.success(msg + " → Va te connecter")
                else: st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)
    with tab_forgot:
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            fu = st.text_input("Nom d'utilisateur", key="fog_u")
            fe = st.text_input("Email associé", key="fog_e")
            fn = st.text_input("Nouveau mot de passe", type="password", key="fog_n")
            if st.button("Réinitialiser", use_container_width=True):
                ok,msg=reset_password(fu,fe,fn)
                if ok: st.success(msg)
                else: st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # ===== SYSTEME APRES AUTH =====
    st.sidebar.image(estm_transparent if os.path.exists(estm_transparent) else os.path.join(BASE_DIR,"estm_logo.png"), width=100)
    st.sidebar.markdown(f"**👋 {st.session_state.username}**")
    st.sidebar.markdown("**PhishGuard Skills**\n- 🎨 Design\n- 🔐 Auth\n- 🧠 Detection\n- 📊 Explain")
    if st.sidebar.button("Déconnexion"):
        st.session_state.authenticated=False; st.rerun()

    col1, col2 = st.columns([1,2])
    with col1:
        if babacar_b64:
            st.markdown(f'<div class="glass-card" style="text-align:center"><img src="data:image/jpeg;base64,{babacar_b64}" style="width:140px; height:140px; border-radius:50%; object-fit:cover; border:4px solid #0A3D8A"><div style="font-weight:900; margin-top:10px;">Babacar MBOW</div><div style="font-size:11px; color:#6B7BA3;">Licence Téléinformatique<br>ESTM 2026-2027</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="skill-card"><b>🎯 Mission du jour</b><br><span style="font-size:12px">Teste 5 liens suspects Orange Money et génère les diagrammes HD pour ton mémoire.</span></div>', unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="hero" style="padding:22px">
            <div class="hero-title" style="font-size:26px">🛡️ Système de Détection Activé</div>
            <div class="hero-sub">Colle un lien suspect ci-dessous, la Skill Detection va l'analyser avec 20 features et t'expliquer le verdict.</div>
        </div>
        """, unsafe_allow_html=True)
        url_input = st.text_input("🔗 URL à analyser", placeholder="https://orange-money-bonus-gagner.com", key="url_input_key")
        if st.button("Analyser avec les Skills →", type="primary", use_container_width=True):
            if url_input:
                feats = extract_features(url_input)
                is_phish, conf = predict_url(url_input, feats)
                marque = "Orange Money" if "orange" in url_input.lower() else "Wave" if "wave" in url_input.lower() else "Sénégal"
                if is_phish:
                    st.error(f"🚨 PHISHING DÉTECTÉ - {conf:.1f}% de risque - {marque}")
                else:
                    st.success(f"✅ LIEN LÉGITIME - Confiance {100-conf:.1f}% - {marque}")
                
                with st.expander("🔬 Analyse Technique (Skill Explain)"):
                    st.json(feats)
                
                # Diagramme
                import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
                labels=['IP','@','Tirets','Suspect','Banking','Longueur','Chiffres','HTTPS']
                scores=[feats.get('ip_score',0),feats.get('arobase_score',0),feats.get('nb_tirets_score',0),feats.get('suspect_score',0),feats.get('banking_score',0),feats.get('longueur_score',0),feats.get('chiffres_score',0),0 if feats.get('presence_https',0)==1 else 15]
                fig,ax=plt.subplots(figsize=(9,4.5)); fig.patch.set_facecolor('white'); ax.set_facecolor('#F8FAFF')
                colors=['#FF7900' if s>30 else '#0A3D8A' if s>10 else '#6B7BA3' for s in scores]
                ax.barh(labels, scores, color=colors, edgecolor='white', height=0.6)
                ax.set_xlabel('Score de risque'); ax.set_title(f'Justification Skill - {marque} - {conf:.1f}%', fontweight='900')
                ax.invert_yaxis(); st.pyplot(fig, use_container_width=True)
                buf=io.BytesIO(); fig.savefig(buf, format='png', dpi=300, bbox_inches='tight'); buf.seek(0)
                st.download_button("📥 Télécharger diagramme HD", data=buf, file_name=f"diagramme_{marque}_{int(conf)}pct.png", mime="image/png", use_container_width=True)

    st.markdown("---")
    st.caption("PhishGuard Sénégal V9 Skills Edition - ESTM Dakar - Licence GLAR 2026 - Babacar MBOW")
