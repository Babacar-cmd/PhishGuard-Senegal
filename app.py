"""
PhishGuard Senegal - VERSION BEAUTE + SANS RACCOURCIS + DROPDOWN PARTAGE CHAMP URL
Babacar MBOW - ESTM Dakar 2026-2027
Amelioration beaute: UI moderne, gradient, cards, animations
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

# CSS BEAUTE
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] {font-family: 'Poppins', sans-serif;}
    .main {background: linear-gradient(180deg, #F8FAFF 0%, #FFFFFF 100%);}
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 14px !important; border: 2px solid #E6ECFF !important;
        padding: 14px !important; font-size: 14px !important;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #0A3D8A !important; box-shadow: 0 0 0 3px rgba(10,61,138,0.1) !important;
    }
    .stSelectbox > div > div {
        border-radius: 14px !important; border: 2px solid #E6ECFF !important;
    }
    .beauty-card {
        background: white; border-radius: 18px; padding: 22px; 
        border: 1px solid #EEF3FF; box-shadow: 0 8px 32px rgba(10,61,138,0.08);
        margin-bottom: 18px; transition: transform 0.2s ease;
    }
    .beauty-card:hover {transform: translateY(-2px); box-shadow: 0 12px 40px rgba(10,61,138,0.12);}
    .gradient-text {
        background: linear-gradient(90deg, #0A3D8A 0%, #FF7900 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 900;
    }
    .metric-beauty {
        background: linear-gradient(135deg, #F8FAFF 0%, #FFFFFF 100%);
        border-radius: 12px; padding: 14px; border: 1px solid #E6ECFF; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

MARQUES=["orange","orangemoney","orange-money","wave"]
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
        d['mot_banking']=1 if any(w in url.lower() for w in ["orange","wave","money","paypal","bank"]) else 0
        d['mot_suspect']=1 if any(w in url.lower() for w in ["securite","verif","bonus","login","urgent","blocage","gain","recompense"]) else 0
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

# HEADER BEAUTE AMELIORE
if estm_b64 or babacar_b64:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFF 100%); border:1px solid #E6ECFF; border-radius:20px; padding:18px 22px; display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; box-shadow: 0 12px 40px rgba(10,61,138,0.10);">
        <div style="display:flex; align-items:center; gap:14px;">
            <div style="background: white; border-radius:14px; padding:6px 10px; border:1px solid #EEF3FF; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <img src="data:image/png;base64,{estm_b64}" style="height:38px; display:block;" />
            </div>
            <div>
                <div style="font-weight:900; font-size:15px; color:#0A1931; letter-spacing:0.3px;">ESTM DAKAR</div>
                <div style="font-size:11px; color:#6B7BA3; font-weight:600;">LICENCE TÉLÉINFORMATIQUE 2026-2027</div>
                <div style="font-size:10px; color:#FF7900; font-weight:700; margin-top:2px;">PhishGuard Sénégal</div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="text-align:right;">
                <div style="font-weight:800; font-size:13px; color:#0A1931;">Babacar MBOW</div>
                <div style="font-size:11px; color:#6B7BA3;">Étudiant GLAR</div>
                <div style="font-size:10px; background: linear-gradient(90deg, #0A3D8A, #FF7900); color:white; padding:2px 8px; border-radius:20px; margin-top:4px; display:inline-block;">Orange Money & Wave</div>
            </div>
            <img src="data:image/jpeg;base64,{babacar_b64}" style="width:48px; height:48px; border-radius:50%; object-fit:cover; border:3px solid white; box-shadow: 0 4px 16px rgba(10,61,138,0.2);" />
        </div>
    </div>
    """, unsafe_allow_html=True)

# TITRE AVEC GRADIENT
st.markdown('<h1 class="gradient-text" style="font-size:32px; text-align:center; margin-bottom:4px;">🛡️ PhishGuard Sénégal</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#6B7BA3; font-size:14px; margin-top:0;">Détecteur de Phishing par IA • <b>20 caractéristiques</b> • Random Forest 98.2%</p>', unsafe_allow_html=True)
st.markdown("""
<div class="beauty-card" style="background: linear-gradient(135deg, #0A3D8A 0%, #1A5DBE 100%); color:white; border:none;">
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="font-size:28px;">🇸🇳</div>
        <div>
            <div style="font-weight:800; font-size:14px;">Spécialité Sénégal - Orange Money & Wave</div>
            <div style="font-size:12px; opacity:0.9; margin-top:2px;">90% des arnaques au Sénégal se font par SMS. Collez le SMS complet, on extrait l'URL automatiquement.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# SESSION STATE POUR PARTAGE CHAMP
if 'url_value' not in st.session_state:
    st.session_state.url_value = ""

# Exemples dictionnaire
ex_dict = {
    "✍️ Saisie manuelle - Écrire une URL": "",
    "✅ Orange Money - Site officiel (légitime)": "https://www.orange.sn/orange-money",
    "⚠️ Orange - Phishing IP + @ (très dangereux)": "http://orange-money-secure-login.com@192.168.1.1/verify",
    "⚠️ Orange - Bonus 50 000F": "http://orange-money-bonus-50000f.com/gain?tel=771234567",
    "⚠️ Orange - Compte bloqué": "https://orange-money-compte-bloque-verif.com/securite/login",
    "✅ Wave - Site officiel (légitime)": "https://www.wave.com/fr-FR/",
    "⚠️ Wave - Bonus urgent": "http://wave-secure-bonus-2024.com/login?verif=compte",
    "⚠️ Wave - Félicitations gain": "http://wave-felicitation-gain-25000.com/recompense"
}

def on_exemple_change():
    choix = st.session_state.exemple_select
    if choix != "✍️ Saisie manuelle - Écrire une URL":
        st.session_state.url_value = ex_dict[choix]

# ===== SECTION 1: SMS =====
st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
st.markdown("#### 📩 Zone SMS - Arnaque reçue par SMS")
sms_input=st.text_area("Collez le SMS complet ici :", placeholder="ORANGE MONEY: Votre compte est bloqué. Cliquez ici: http://orange-money-secure-login.com@192.168.1.1/verify pour débloquer", height=110, key="sms_beaute", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

url_from_sms=""
if sms_input:
    urls=extraire_urls_sms(sms_input)
    if urls:
        st.markdown('<div class="beauty-card" style="border-left: 4px solid #FF7900;">', unsafe_allow_html=True)
        st.success(f"🔗 {len(urls)} URL(s) détectée(s) automatiquement :")
        for u in urls:
            st.code(u, language="text")
        url_from_sms=urls[0]
        st.session_state.url_value = url_from_sms
        st.markdown('</div>', unsafe_allow_html=True)

# ===== SECTION 2: URL + DROPDOWN MEME CHAMP =====
st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
st.markdown("#### 🔗 Analyse URL - Menu déroulant + Champ partagé")

# Dropdown et champ partagent la meme valeur via session_state
col_sel, col_url = st.columns([1, 1.6])

with col_sel:
    st.selectbox(
        "📋 Choisir un exemple :",
        options=list(ex_dict.keys()),
        key="exemple_select",
        on_change=on_exemple_change,
        help="Sélectionnez un exemple, il remplira automatiquement le champ URL à droite"
    )

with col_url:
    url_input = st.text_input(
        "🌐 URL à analyser :",
        value=st.session_state.url_value,
        placeholder="https://orange-money... ou https://wave...",
        key="url_beaute",
        help="Ce champ est partagé avec le menu déroulant - modifiez ici ou choisissez un exemple"
    )
    # Mettre à jour session_state si user tape manuellement
    if url_input != st.session_state.url_value:
        st.session_state.url_value = url_input

url_a_analyser = st.session_state.url_value or url_from_sms

if url_a_analyser:
    autorise_test, marque_test = est_autorisee(url_a_analyser)
    badge_color = "#0A3D8A" if autorise_test else "#6B7BA3"
    st.markdown(f'<div style="background: {badge_color}10; border: 1px solid {badge_color}20; border-radius: 10px; padding: 10px 14px; margin-top: 12px; font-size: 13px;"><b>URL prête :</b> <code>{url_a_analyser}</code><br><span style="color:{badge_color}; font-weight:700;">Marque : {marque_test or "Non détectée (hors Orange/Wave)"}</span></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# BOUTON ANALYSE BEAUTE
st.markdown("""
<style>
div[data-testid="stButton"] > button {
    background: linear-gradient(90deg, #0A3D8A 0%, #FF7900 100%) !important;
    color: white !important; border: none !important; border-radius: 14px !important;
    padding: 14px 28px !important; font-weight: 800 !important; font-size: 15px !important;
    box-shadow: 0 8px 24px rgba(10,61,138,0.25) !important; transition: all 0.3s ease !important;
    width: 100%;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-2px); box-shadow: 0 12px 32px rgba(10,61,138,0.35) !important;
}
</style>
""", unsafe_allow_html=True)

if st.button("🔍 Analyser l'URL maintenant", type="primary", key="btn_beaute") and url_a_analyser:
    with st.spinner("🔬 Analyse en cours..."):
        autorise, marque=est_autorisee(url_a_analyser)
        est_test=any(x in url_a_analyser.lower() for x in ["google","paypal"])
        if not autorise and not est_test:
            st.markdown('<div class="beauty-card" style="border-left: 4px solid #FF3B30; background: #FFF5F5;">', unsafe_allow_html=True)
            st.error(f"### ❌ URL non prise en charge\n**Ce projet Sénégal ne traite QUE Orange Money ou Wave.**")
            st.code(url_a_analyser)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            marque=marque or ("Test" if est_test else "Orange/Wave")
            api_url="http://localhost:8000/predict"
            result=None
            try:
                resp=requests.get(api_url, params={"url": url_a_analyser}, timeout=3)
                if resp.status_code==200:
                    result=resp.json()
            except:
                feats=extract_features(url_a_analyser)
                vec=features_to_vector(feats)
                if model is not None:
                    try:
                        pred=int(model.predict([vec])[0]); proba=model.predict_proba([vec])[0]; conf=float(proba[1]*100) if len(proba)>1 else (95.0 if pred==1 else 5.0)
                    except:
                        conf=min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0)+feats.get('arobase_score',0))); pred=1 if conf>60 else 0
                else:
                    conf=min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0)+feats.get('arobase_score',0)+feats.get('suspect_score',0)+feats.get('banking_score',0))); pred=1 if conf>60 else 0
                result={"url":url_a_analyser,"prediction":"phishing" if pred==1 else "legitime","confiance_phishing":round(conf,2),"features":feats,"explication":[f"IP suspecte: {'Oui' if feats.get('presence_ip')==1 else 'Non'}", f"@ masquage: {'Oui' if feats.get('presence_arobase')==1 else 'Non'}", f"Tirets: {feats.get('nb_tirets',0)}", f"Mot bancaire: {'Oui' if feats.get('mot_banking')==1 else 'Non'}", f"Mot suspect: {'Oui' if feats.get('mot_suspect')==1 else 'Non'}"],"niveau_risque":"ÉLEVÉ" if pred==1 else "FAIBLE","marque":marque}
            if result and "error" not in result:
                pred=result['prediction']; conf=result.get('confiance_phishing',0)
                if pred=='phishing':
                    st.markdown(f'<div class="beauty-card" style="background: linear-gradient(135deg, #FFF5F5 0%, #FFE5E5 100%); border: 2px solid #FF3B30; border-left: 6px solid #FF3B30;"><div style="font-size:22px; font-weight:900; color:#FF3B30;">🚨 PHISHING DÉTECTÉ - {result.get("marque",marque)}</div><div style="font-size:16px; color:#7A0000; margin-top:6px;">Confiance : <b>{conf}%</b> • Risque : {result.get("niveau_risque","ÉLEVÉ")} 🔴</div><div style="margin-top:12px;"><div style="background:#FF3B30; height:10px; border-radius:20px; width:{conf}%;"></div></div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="beauty-card" style="background: linear-gradient(135deg, #F0FFF4 0%, #DCFCE7 100%); border: 2px solid #00C950; border-left: 6px solid #00C950;"><div style="font-size:22px; font-weight:900; color:#00A63D;">✅ SITE LÉGITIME - {result.get("marque",marque)}</div><div style="font-size:16px; color:#005A1F; margin-top:6px;">Confiance légitime : <b>{100-conf}%</b> • Risque : {result.get("niveau_risque","FAIBLE")} 🟢</div><div style="margin-top:12px;"><div style="background:#00C950; height:10px; border-radius:20px; width:{100-conf}%;"></div></div></div>', unsafe_allow_html=True)
                if result.get('explication'):
                    st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
                    st.markdown("**🔎 Pourquoi ce résultat ?**")
                    for r in result['explication']:
                        st.markdown(f"- {r}")
                    st.markdown('</div>', unsafe_allow_html=True)
                # ANALYSE TECHNIQUE
                st.markdown("## 🔬 Analyse Technique")
                feats=result.get('features', {})
                tab_lex, tab_sec, tab_ctx = st.tabs(["📝 Lexical", "🔒 Sécurité", "🌍 Contexte"])
                with tab_lex:
                    st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
                    st.markdown("**📝 Analyse lexicale - structure de l'URL**")
                    c1,c2,c3=st.columns(3)
                    with c1:
                        st.metric("Longueur URL", feats.get('longueur_url',0)); st.metric("Hostname", feats.get('longueur_hostname',0)); st.metric("Points (.)", feats.get('nb_points',0))
                    with c2:
                        st.metric("Tirets (-)", feats.get('nb_tirets',0)); st.metric("Chiffres", feats.get('nb_chiffres',0)); st.metric("Sous-domaines", feats.get('nb_sous_domaines',0))
                    with c3:
                        st.metric("Symboles", feats.get('nb_symboles',0)); st.metric("@", feats.get('nb_arobase',0)); st.metric("Suspect >75", "Oui ⚠️" if feats.get('longueur_url',0)>75 else "Non ✅")
                    st.markdown('</div>', unsafe_allow_html=True)
                with tab_sec:
                    st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
                    st.markdown("**🔒 Analyse sécurité - tromperie**")
                    c1,c2,c3=st.columns(3)
                    with c1:
                        st.metric("Présence IP", "Oui ⚠️" if feats.get('presence_ip')==1 else "Non ✅"); st.metric("Présence @", "Oui ⚠️" if feats.get('presence_arobase')==1 else "Non ✅"); st.metric("HTTPS", "Oui ✅" if feats.get('presence_https')==1 else "Non ⚠️")
                    with c2:
                        st.metric("Âge", f"{feats.get('age_domaine',-1)} j" if feats.get('age_domaine',-1)!=-1 else "Inconnu"); st.metric("Récent <30j", "Oui ⚠️" if feats.get('age_domaine',4000)<30 else "Non ✅")
                    with c3:
                        st.metric("IP+@ critique", "Oui 🔴" if feats.get('presence_ip')==1 and feats.get('presence_arobase')==1 else "Non ✅"); st.metric("Score sécu", f"{feats.get('ip_score',0)+feats.get('arobase_score',0)}/100")
                    st.markdown('</div>', unsafe_allow_html=True)
                with tab_ctx:
                    st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
                    st.markdown("**🌍 Contexte Sénégal**")
                    c1,c2,c3=st.columns(3)
                    with c1:
                        st.metric("Mot bancaire", "Oui ⚠️" if feats.get('mot_banking')==1 else "Non ✅"); st.metric("Marque", result.get('marque',marque))
                    with c2:
                        st.metric("Mot suspect", "Oui ⚠️" if feats.get('mot_suspect')==1 else "Non ✅"); st.metric("SMS", "Arnaque SMS" if feats.get('mot_suspect')==1 and feats.get('mot_banking')==1 else "Normal")
                    with c3:
                        st.metric("Cible", "Orange/Wave" if feats.get('mot_banking')==1 else "Autre"); st.metric("Score ctx", f"{feats.get('banking_score',0)+feats.get('suspect_score',0)}/100")
                    st.markdown('</div>', unsafe_allow_html=True)
                with st.expander("🔧 JSON complet 20 features - Jury"):
                    st.json(feats)
                st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
                st.markdown("#### 📊 Diagramme justification")
                import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
                labels=['IP dans URL','Présence @','Nb tirets','Mots suspects','Mot banking','Longueur URL','Chiffres','HTTPS manquant']
                scores=[feats.get('ip_score',0),feats.get('arobase_score',0),feats.get('nb_tirets_score',0),feats.get('suspect_score',0),feats.get('banking_score',0),feats.get('longueur_score',0),feats.get('chiffres_score',0),0 if feats.get('presence_https',0)==1 else 15]
                total=sum(scores) if sum(scores)>0 else 1; pcts=[s/total*100 for s in scores]; colors=['#FF7900' if s>30 else '#0A3D8A' if s>10 else '#6B7BA3' for s in scores]
                fig,ax=plt.subplots(figsize=(10,5.5)); fig.patch.set_facecolor('white'); ax.set_facecolor('#F8FAFF')
                bars=ax.barh(labels,pcts,color=colors,edgecolor='white',linewidth=1.5, height=0.6)
                ax.set_xlabel('Contribution risque (%)', fontweight='bold', fontsize=11); ax.set_title(f'Justification - {result.get("marque",marque)} - {conf}%', fontweight='900', color='#0A1931', fontsize=14, pad=20); ax.invert_yaxis()
                for bar,p in zip(bars,pcts):
                    if p>2:
                        ax.text(bar.get_width()+1, bar.get_y()+bar.get_height()/2, f'{p:.1f}%', va='center', fontweight='bold', fontsize=10, color='#0A1931')
                plt.tight_layout(); plt.grid(axis='x', alpha=0.2); st.pyplot(fig)
                buf=io.BytesIO(); fig.savefig(buf, format='png', dpi=300, bbox_inches='tight'); buf.seek(0)
                st.download_button(label="📥 Télécharger diagramme HD (PNG)", data=buf, file_name=f"diagramme_{result.get('marque','analyse')}_{int(conf)}pct.png", mime="image/png", key="dl_beaute")
                df=pd.DataFrame({'Feature':labels,'Score':scores,'%':[f"{p:.1f}%" for p in pcts]}); st.dataframe(df, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"""<div style="text-align:center; padding:18px; background:white; border-radius:16px; border:1px solid #E6ECFF; box-shadow: 0 8px 24px rgba(10,61,138,0.06);"><div style="font-weight:900; color:#0A1931; font-size:12px;">ESTM DAKAR • LICENCE TÉLÉINFORMATIQUE 2026-2027</div><div style="font-size:11px; color:#FF7900; margin-top:6px; font-weight:800;">✨ UI Moderne • Lexical • Sécurité • Contexte • Orange Money & Wave</div><div style="font-size:11px; color:#6B7BA3; margin-top:4px;">Babacar MBOW • Elhadji Ahmadou Chérif Diouf • Random Forest 98.2%</div></div>""", unsafe_allow_html=True)
