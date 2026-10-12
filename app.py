"""
PhishGuard Senegal - AUTH + FORGOT PASSWORD - Ultra Beautiful
Babacar MBOW - ESTM Dakar 2026-2027
Page accueil avec Creation compte + Connexion + Mot de passe oublie
"""
import streamlit as st, sys, os, pickle, re, base64, io, json, hashlib
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

st.set_page_config(page_title="PhishGuard - Auth", page_icon="🛡️", layout="centered")

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

USERS_FILE = os.path.join(BASE_DIR, "users.json")
def load_users():
    # Auto-cree admin si fichier n'existe pas (fix bug Utilisateur inexistant sur Streamlit Cloud)
    if not os.path.exists(USERS_FILE):
        default_admin = {
            "admin": {
                "email": "admin@estm.sn",
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "nom": "admin"
            }
        }
        try:
            json.dump(default_admin, open(USERS_FILE,"w",encoding="utf-8"), indent=2)
            return default_admin
        except:
            return default_admin
    try:
        data = json.load(open(USERS_FILE,"r",encoding="utf-8"))
        # Si fichier vide ou sans admin, on ajoute admin
        if not data or "admin" not in data:
            if not data:
                data = {}
            data["admin"] = {
                "email": "admin@estm.sn",
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "nom": "admin"
            }
            try:
                json.dump(data, open(USERS_FILE,"w",encoding="utf-8"), indent=2)
            except:
                pass
        return data
    except:
        return {
            "admin": {
                "email": "admin@estm.sn",
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "nom": "admin"
            }
        }
def save_users(u):
    try:
        json.dump(u, open(USERS_FILE,"w",encoding="utf-8"), indent=2)
    except:
        pass
def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

def register_user(username, email, password):
    users=load_users()
    if username in users: return False, "Nom deja pris"
    if len(password)<6: return False, "Mot de passe trop court (min 6)"
    users[username]={"email":email,"password":hash_pwd(password),"nom":username}
    save_users(users)
    return True, "Compte cree avec succes"

def check_login(username, password):
    users=load_users()
    if username not in users: return False, "Utilisateur inexistant"
    if users[username]["password"]!=hash_pwd(password): return False, "Mot de passe incorrect"
    return True, "Connexion reussie"

def reset_password(username, email, new_password):
    users=load_users()
    if username not in users: return False, "Utilisateur inexistant"
    if users[username].get("email","").lower()!=email.lower(): return False, "Email ne correspond pas"
    if len(new_password)<6: return False, "Mot de passe trop court (min 6)"
    users[username]["password"]=hash_pwd(new_password)
    save_users(users)
    return True, "Mot de passe reinitialise ! Connectez-vous maintenant"

if "authenticated" not in st.session_state: st.session_state.authenticated=False
if "username" not in st.session_state: st.session_state.username=""
if "url_input_key" not in st.session_state: st.session_state.url_input_key=""

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800;900&display=swap');
html, body, [class*="css"] {font-family:'Outfit',sans-serif !important;}
[data-testid="stAppViewContainer"]{background: radial-gradient(1200px 600px at 10% -10%, #E8F0FF 0%, transparent 60%), radial-gradient(1000px 500px at 90% 0%, #FFF0E6 0%, transparent 60%), linear-gradient(180deg, #F8FAFF 0%, #FFFFFF 100%);}
.hero-auth{background: linear-gradient(135deg, #0A1931 0%, #0A3D8A 50%, #1E4EB8 100%); border-radius:28px; padding:28px; color:white; box-shadow:0 24px 70px rgba(10,61,138,0.4); position:relative; overflow:hidden; margin-bottom:22px;}
.glass-card{background:rgba(255,255,255,0.92); backdrop-filter:blur(16px); border-radius:22px; padding:22px; border:1px solid rgba(230,236,255,0.9); box-shadow:0 12px 40px rgba(10,61,138,0.08); margin-bottom:18px;}
.auth-container{background:rgba(255,255,255,0.96); backdrop-filter:blur(20px); border-radius:24px; overflow:hidden; border:1px solid rgba(230,236,255,0.9); box-shadow:0 20px 60px rgba(10,61,138,0.12);}
.stTextInput > div > div > input{border-radius:14px !important; border:2px solid #E6ECFF !important; background:#FBFCFF !important;}
div[data-testid="stButton"] > button{background: linear-gradient(100deg, #0A3D8A 0%, #1A5DBE 45%, #FF7900 100%) !important; color:white !important; border:none !important; border-radius:14px !important; padding:13px !important; font-weight:800 !important; width:100%;}
.footer{background:white; border:1px solid #E6ECFF; border-radius:18px; padding:18px; text-align:center; margin-top:24px;}
</style>
""", unsafe_allow_html=True)

MARQUES=["orange","orangemoney","orange-money","wave","wave.com"]
def est_autorisee(url):
    l=url.lower()
    for m in MARQUES:
        if m in l: return True, "Orange Money" if "orange" in m else "Wave"
    return False, None
def extraire_urls_sms(txt):
    pat=r'(https?://[^\s\n]+|www\.[^\s\n]+|[a-zA-Z0-9.-]+\.(?:com|sn|net|org)/[^\s\n]*|(?:orange|wave)[^\s\n]*\.[^\s\n]+)'
    urls=re.findall(pat, txt, re.IGNORECASE)
    clean=[u.strip().rstrip('.,!?)') for u in urls if len(u.strip())>5]
    if not clean and any(m in txt.lower() for m in MARQUES):
        m=re.search(r'((?:https?://)?[^\s]*?(?:orange|wave)[^\s]*)', txt, re.IGNORECASE)
        if m: clean=[m.group(1)]
    return clean
def extract_features(url):
    if LOCAL_MODE:
        try: return extract_local(url)
        except: pass
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
        d['mot_suspect']=1 if any(w in url.lower() for w in ["securite","verif","bonus","login","urgent","blocage","gain"]) else 0
        d['age_domaine']=5 if d['presence_ip']==1 else (10 if d['nb_tirets']>=2 else 4000)
        d['nb_tirets_score']=d['nb_tirets']*10; d['ip_score']=d['presence_ip']*50; d['arobase_score']=d['nb_arobase']*40; d['suspect_score']=d['mot_suspect']*25; d['banking_score']=d['mot_banking']*15; d['longueur_score']=10 if d['longueur_url']>75 else 0; d['chiffres_score']=min(20, d['nb_chiffres']*2)
        return d
    except:
        return {'longueur_url':len(url),'longueur_hostname':0,'nb_points':0,'nb_tirets':0,'nb_chiffres':0,'nb_symboles':0,'presence_ip':0,'presence_arobase':0,'nb_arobase':0,'presence_https':0,'nb_sous_domaines':0,'mot_banking':0,'mot_suspect':0,'age_domaine':-1,'nb_tirets_score':0,'ip_score':0,'arobase_score':0,'suspect_score':0,'banking_score':0,'longueur_score':0,'chiffres_score':0}
def features_to_vector(fd):
    if LOCAL_MODE:
        try: return fv_local(fd)
        except: pass
    try:
        f1=fd.get('longueur_url',0); f2=fd.get('longueur_hostname',0); f3=fd.get('nb_points',0); f4=fd.get('nb_tirets',0); f5=fd.get('nb_chiffres',0); f6=fd.get('nb_symboles',0); f7=fd.get('presence_ip',0); f8=fd.get('presence_arobase',0); f9=fd.get('presence_https',0); f10=fd.get('nb_sous_domaines',0); f11=fd.get('mot_banking',0); f12=fd.get('mot_suspect',0); f13=fd.get('age_domaine',4000); f14=30 if f13<100 else 365; f15=0 if f7==1 else (1 if f9==1 else 0); f16=2 if f8==1 else 0; f17=1 if f13>1000 else 0; f18=1; f19=0; f20=(f4*2+f11*3+f12*2+f7*5)
        return [f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f19,f20]
    except:
        return [0]*20
def load_model():
    try:
        import sklearn
    except:
        return None
    for p in [os.path.join(BASE_DIR,"model_rf.pkl"), "model.pkl"]:
        if os.path.exists(p):
            try:
                with open(p,"rb") as f: return pickle.load(f)
            except:
                try:
                    import joblib; return joblib.load(p)
                except: continue
    return None
model=load_model()

ex_dict={"Saisie manuelle":"", "Orange Money - Officiel":"https://www.orange.sn/orange-money", "Orange - Phishing IP + @":"http://orange-money-secure-login.com@192.168.1.1/verify", "Wave - Officiel":"https://www.wave.com/fr-FR/", "Wave - Bonus":"http://wave-secure-bonus-2024.com/login"}
def on_exemple_change():
    choix=st.session_state.get("exemple_select_key","Saisie manuelle")
    if choix!="Saisie manuelle": st.session_state.url_input_key=ex_dict.get(choix,"")
def on_sms_change():
    txt=st.session_state.get("sms_input_key","")
    if txt:
        urls=extraire_urls_sms(txt)
        if urls: st.session_state.url_input_key=urls[0]

if not st.session_state.authenticated:
    if estm_b64:
        st.markdown(f"""
        <div class="hero-auth">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="display:flex; align-items:center; gap:12px;">
                        <div style="background:white; border-radius:12px; padding:6px 10px;"><img src="data:image/png;base64,{estm_b64}" style="height:32px;" /></div>
                        <div><div style="font-weight:900; font-size:13px;">ESTM DAKAR</div><div style="font-size:10px; opacity:0.8;">LICENCE TELEINFORMATIQUE 2026-2027</div></div>
                    </div>
                    <div style="font-size:30px; font-weight:900; margin-top:16px; line-height:1.1;">PhishGuard<br/>Senegal</div>
                    <div style="font-size:12px; opacity:0.85; margin-top:8px;">Orange Money & Wave - IA 98.2% - Anti-SMS</div>
                </div>
                <div style="text-align:center;"><img src="data:image/jpeg;base64,{babacar_b64}" style="width:56px; height:56px; border-radius:16px; object-fit:cover; border:3px solid white;" /><div style="font-weight:800; font-size:11px; margin-top:6px;">Babacar MBOW</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    tab_login, tab_signup, tab_forgot = st.tabs(["Connexion", "Creer un compte", "Mot de passe oublie"])

    with tab_login:
        st.markdown('<div style="padding:20px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight:800; font-size:16px; color:#0A1931;">Bienvenue !</div><div style="font-size:13px; color:#6B7BA3; margin-bottom:16px;">Connectez-vous pour acceder au systeme</div>', unsafe_allow_html=True)
        login_user=st.text_input("Nom d utilisateur", key="login_user")
        login_pwd=st.text_input("Mot de passe", type="password", key="login_pwd")
        if st.button("Se connecter", key="btn_login"):
            if not login_user or not login_pwd: st.warning("Remplir tous les champs")
            else:
                ok,msg=check_login(login_user, login_pwd)
                if ok:
                    st.session_state.authenticated=True; st.session_state.username=login_user; st.success(msg); st.rerun()
                else: st.error(msg)
        st.caption("Test: admin / admin123")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_signup:
        st.markdown('<div style="padding:20px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight:800; font-size:16px; color:#0A1931;">Creer votre compte</div><div style="font-size:13px; color:#6B7BA3; margin-bottom:16px;">Rejoignez PhishGuard</div>', unsafe_allow_html=True)
        signup_user=st.text_input("Nom d utilisateur", key="signup_user")
        signup_email=st.text_input("Email", key="signup_email")
        signup_pwd=st.text_input("Mot de passe", type="password", key="signup_pwd")
        signup_pwd2=st.text_input("Confirmer", type="password", key="signup_pwd2")
        if st.button("Creer mon compte", key="btn_signup"):
            if not signup_user or not signup_email or not signup_pwd: st.warning("Remplir tous les champs")
            elif signup_pwd!=signup_pwd2: st.error("Mots de passe differents")
            else:
                ok,msg=register_user(signup_user, signup_email, signup_pwd)
                if ok: st.success(msg + " - Allez dans Connexion")
                else: st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_forgot:
        st.markdown('<div style="padding:20px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight:800; font-size:16px; color:#0A1931;">Mot de passe oublie ?</div><div style="font-size:13px; color:#6B7BA3; margin-bottom:16px;">Reinitialisez avec nom + email</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FFFBEB, #FEF3C7); border:1px solid #FCD34D; border-radius:14px; padding:12px; margin-bottom:14px; display:flex; gap:10px;">
            <div style="background:#F59E0B; color:white; width:32px; height:32px; border-radius:10px; display:flex; align-items:center; justify-content:center;">🔑</div>
            <div><div style="font-weight:800; font-size:12px; color:#92400E;">Securite</div><div style="font-size:11px; color:#78350F;">Nous verifions que l email correspond au compte</div></div>
        </div>
        """, unsafe_allow_html=True)
        forgot_user=st.text_input("Nom d utilisateur", key="forgot_user")
        forgot_email=st.text_input("Email du compte", key="forgot_email")
        forgot_new_pwd=st.text_input("Nouveau mot de passe", type="password", key="forgot_new_pwd")
        forgot_new_pwd2=st.text_input("Confirmer nouveau mot de passe", type="password", key="forgot_new_pwd2")
        if st.button("Reinitialiser mon mot de passe", key="btn_forgot"):
            if not forgot_user or not forgot_email or not forgot_new_pwd: st.warning("Remplir tous les champs")
            elif forgot_new_pwd!=forgot_new_pwd2: st.error("Mots de passe differents")
            else:
                ok,msg=reset_password(forgot_user, forgot_email, forgot_new_pwd)
                if ok: st.success(msg); st.balloons()
                else: st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Projet realise dans le cadre de la Licence GLAR - Detection phishing par IA | 2026")
    st.markdown('<div class="footer"><div style="font-weight:900; font-size:11px;">ESTM DAKAR - GLAR 2026-2027</div><div style="font-size:10px; color:#FF7900; margin-top:4px;">Auth + Mot de passe oublie + Orange Money & Wave</div></div>', unsafe_allow_html=True)

else:
    col1,col2=st.columns([3,1])
    with col1: st.markdown(f"### Bienvenue {st.session_state.username} - PhishGuard")
    with col2:
        if st.button("Deconnexion"):
            st.session_state.authenticated=False; st.session_state.username=""; st.rerun()
    st.markdown("---")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:800; font-size:12px; color:#0A3D8A;">ZONE SMS</div>', unsafe_allow_html=True)
    st.text_area("SMS", key="sms_input_key", on_change=on_sms_change, placeholder="Collez SMS Orange Money / Wave ici", height=90, label_visibility="collapsed")
    if st.session_state.get("sms_input_key",""):
        urls=extraire_urls_sms(st.session_state.sms_input_key)
        if urls: st.success(f"URL detectee: {urls[0]}")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.selectbox("Exemple (remplit champ ci-dessous):", list(ex_dict.keys()), key="exemple_select_key", on_change=on_exemple_change)
    url_a_analyser=st.text_input("URL Orange/Wave:", key="url_input_key", placeholder="https://orange...")
    if url_a_analyser:
        aut,marq=est_autorisee(url_a_analyser)
        if aut: st.info(f"Marque: {marq}")
        else: st.warning("Hors Orange/Wave - bloque")
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("Analyser l URL", type="primary", use_container_width=True):
        url_final=st.session_state.get("url_input_key","").strip()
        if not url_final: st.warning("Saisir URL orange/wave")
        else:
            autorise,marque=est_autorisee(url_final)
            if not autorise: st.error(f"URL NON PRISE EN CHARGE - Orange/Wave ONLY: {url_final}")
            else:
                with st.spinner(f"Analyse {marque}..."):
                    feats=extract_features(url_final); vec=features_to_vector(feats)
                    if model is not None:
                        try: pred=int(model.predict([vec])[0]); proba=model.predict_proba([vec])[0]; conf=float(proba[1]*100) if len(proba)>1 else 95.0 if pred==1 else 5.0
                        except: conf=min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0))); pred=1 if conf>60 else 0
                    else: conf=min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0)+feats.get('suspect_score',0))); pred=1 if conf>60 else 0
                    if pred==1: st.error(f"PHISHING DETECTE - {marque} - {conf:.1f}%"); st.progress(conf/100)
                    else: st.success(f"SITE LEGITIME - {marque} - {100-conf:.1f}%"); st.progress((100-conf)/100)
                    tab1,tab2,tab3=st.tabs(["Lexical","Securite","Contexte"])
                    with tab1: st.metric("Longueur",feats.get('longueur_url',0)); st.metric("Tirets",feats.get('nb_tirets',0))
                    with tab2: st.metric("IP","Oui" if feats.get('presence_ip')==1 else "Non"); st.metric("HTTPS","Oui" if feats.get('presence_https')==1 else "Non")
                    with tab3: st.metric("Marque",marque)
                    with st.expander("JSON 20 features"): st.json(feats)
    st.caption("Projet Licence GLAR - 2026")
