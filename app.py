"""
PhishGuard Senegal - VERSION DEFINITIVE CORRIGEE - Dropdown remplit champ automatiquement
FIX: utilisation callback on_change + key pour text_input
Babacar MBOW - ESTM Dakar 2026-2027
Orange Money & Wave ONLY - Lexical/Securite/Contexte
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

st.set_page_config(page_title="PhishGuard Senegal", page_icon="🛡️", layout="centered")

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

st.markdown("""
<style>
.beauty-card{background:white; border-radius:18px; padding:22px; border:1px solid #EEF3FF; box-shadow:0 8px 32px rgba(10,61,138,0.08); margin-bottom:18px;}
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

# HEADER
if estm_b64 or babacar_b64:
    st.markdown(f"""<div style="background:white; border:1px solid #E6ECFF; border-radius:20px; padding:18px 22px; display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;"><div style="display:flex; align-items:center; gap:14px;"><div style="background:white; border-radius:14px; padding:6px 10px; border:1px solid #EEF3FF;"><img src="data:image/png;base64,{estm_b64}" style="height:38px;" /></div><div><div style="font-weight:900; font-size:15px; color:#0A1931;">ESTM DAKAR</div><div style="font-size:11px; color:#6B7BA3;">LICENCE TELEINFORMATIQUE 2026-2027</div></div></div><div style="display:flex; align-items:center; gap:12px;"><div style="text-align:right;"><div style="font-weight:800; font-size:13px;">Babacar MBOW</div><div style="font-size:10px; background: linear-gradient(90deg, #0A3D8A, #FF7900); color:white; padding:2px 8px; border-radius:20px;">Orange Money & Wave ONLY</div></div><img src="data:image/jpeg;base64,{babacar_b64}" style="width:48px; height:48px; border-radius:50%; object-fit:cover; border:3px solid white;" /></div></div>""", unsafe_allow_html=True)

st.title("🛡️ Détecteur de Phishing par IA")
st.subheader("Projet Fin de Cycle - Orange Money & Wave - 20 caractéristiques")
st.info("🔒 Ce système ne détecte QUE les URLs Orange Money ou Wave - Spécialité Sénégal (arnaques SMS)")

# DICTIONNAIRE EXEMPLES
ex_dict = {
    "✍️ Saisie manuelle (écrire ci-dessous)": "",
    "✅ Orange Money - Officiel légitime": "https://www.orange.sn/orange-money",
    "⚠️ Orange - Phishing IP + @ (très dangereux)": "http://orange-money-secure-login.com@192.168.1.1/verify",
    "⚠️ Orange - Bonus 50 000F": "http://orange-money-bonus-50000f.com/gain?tel=771234567",
    "⚠️ Orange - Compte bloqué": "https://orange-money-compte-bloque-verif.com/securite/login",
    "✅ Wave - Officiel légitime": "https://www.wave.com/fr-FR/",
    "⚠️ Wave - Bonus urgent": "http://wave-secure-bonus-2024.com/login?verif=compte",
    "⚠️ Wave - Félicitations gain": "http://wave-felicitation-gain-25000.com/recompense"
}

# INIT SESSION STATE
if "url_input_key" not in st.session_state:
    st.session_state.url_input_key = ""
if "sms_key" not in st.session_state:
    st.session_state.sms_key = ""

# CALLBACKS - LA SOLUTION QUI MARCHE
def on_exemple_change():
    choix = st.session_state.exemple_select_key
    if choix != "✍️ Saisie manuelle (écrire ci-dessous)":
        st.session_state.url_input_key = ex_dict[choix]
    else:
        # Si on repasse en manuel, on ne vide pas pour permettre edition
        pass

def on_sms_change():
    txt = st.session_state.sms_input_key
    if txt:
        urls = extraire_urls_sms(txt)
        if urls:
            st.session_state.url_input_key = urls[0]

# SECTION 1: SMS
st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
st.markdown("#### 📩 1. Zone SMS - Collez le SMS d'arnaque")
st.text_area(
    "SMS:",
    placeholder="ORANGE MONEY: Votre compte est bloqué. Cliquez ici: http://orange-money-secure-login.com@192.168.1.1/verify",
    height=100,
    key="sms_input_key",
    on_change=on_sms_change
)
# Affichage URL detectee dans SMS
if st.session_state.sms_key if False else False:
    pass
sms_current = st.session_state.get("sms_input_key","")
if sms_current:
    urls = extraire_urls_sms(sms_current)
    if urls:
        st.success(f"🔗 URL détectée et copiée automatiquement dans le champ ci-dessous : {urls[0]}")
st.markdown('</div>', unsafe_allow_html=True)

# SECTION 2: MENU DEROULANT + CHAMP PARTAGE - VERSION CORRIGEE DEFINITIVE
st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
st.markdown("#### 🔗 2. Analyse URL - Menu déroulant + Champ partagé (même champ)")

# Dropdown avec callback qui remplit le champ
st.selectbox(
    "📋 Choisir un exemple (remplit automatiquement le champ URL) :",
    options=list(ex_dict.keys()),
    key="exemple_select_key",
    on_change=on_exemple_change
)

# Champ URL partage - key = url_input_key, donc il est rempli par le callback
url_a_analyser = st.text_input(
    "🌐 URL Orange/Wave à analyser (rempli automatiquement par le menu ci-dessus) :",
    placeholder="https://orange-money... ou https://wave...",
    key="url_input_key"
)

if url_a_analyser:
    aut, marq = est_autorisee(url_a_analyser)
    if aut:
        st.info(f"✅ Marque détectée : {marq} - Prêt pour analyse")
    else:
        st.warning(f"⚠️ Cette URL ne contient pas orange/wave - Elle sera bloquée (système Orange/Wave ONLY)")
        st.caption("Exemples valides: orange-money, orange.sn, wave.com")

st.markdown('</div>', unsafe_allow_html=True)

# BOUTON ANALYSER - TOUJOURS VISIBLE
analyser = st.button("🔍 Analyser l'URL maintenant", type="primary", use_container_width=True)

if analyser:
    url_final = st.session_state.get("url_input_key","").strip()
    if not url_final:
        st.warning("⚠️ Veuillez d'abord choisir un exemple dans le menu déroulant ou coller un SMS ou saisir une URL contenant orange ou wave.")
    else:
        autorise, marque = est_autorisee(url_final)
        if not autorise:
            st.error(f"""
            ### ❌ URL NON PRISE EN CHARGE - ORANGE/WAVE ONLY
            
            Ce système intelligent ne détecte QUE les URLs de marque Orange Money ou Wave.
            
            URL entrée : `{url_final}`
            
            **Exemples valides :**
            - https://www.orange.sn/orange-money
            - http://orange-money-secure-login.com@192.168.1.1/verify
            - https://www.wave.com/fr-FR/
            """)
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
                    st.error(f"### 🚨 PHISHING DÉTECTÉ - {marque} - Confiance : {conf:.1f}%")
                    st.progress(conf/100)
                    st.markdown(f"**Niveau de risque : ÉLEVÉ 🔴 - Faux site {marque}**")
                else:
                    st.success(f"### ✅ SITE LÉGITIME - {marque} - Confiance : {100-conf:.1f}%")
                    st.progress((100-conf)/100)
                    st.markdown(f"**Niveau de risque : FAIBLE 🟢 - Vrai site {marque}**")

                # Analyse Technique Lexical/Securite/Contexte
                st.markdown("## 🔬 Analyse Technique")
                tab_lex, tab_sec, tab_ctx = st.tabs(["📝 Lexical", "🔒 Sécurité", "🌍 Contexte"])
                with tab_lex:
                    st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
                    c1,c2,c3=st.columns(3)
                    with c1:
                        st.metric("Longueur URL", feats.get('longueur_url',0)); st.metric("Hostname", feats.get('longueur_hostname',0))
                    with c2:
                        st.metric("Points", feats.get('nb_points',0)); st.metric("Tirets", feats.get('nb_tirets',0))
                    with c3:
                        st.metric("Chiffres", feats.get('nb_chiffres',0)); st.metric("@", feats.get('nb_arobase',0))
                    st.markdown('</div>', unsafe_allow_html=True)
                with tab_sec:
                    st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
                    c1,c2,c3=st.columns(3)
                    with c1:
                        st.metric("IP", "Oui ⚠️" if feats.get('presence_ip')==1 else "Non ✅"); st.metric("@", "Oui ⚠️" if feats.get('presence_arobase')==1 else "Non ✅")
                    with c2:
                        st.metric("HTTPS", "Oui ✅" if feats.get('presence_https')==1 else "Non ⚠️"); st.metric("Âge", f"{feats.get('age_domaine',-1)} j")
                    with c3:
                        st.metric("IP+@ critique", "Oui 🔴" if feats.get('presence_ip')==1 and feats.get('presence_arobase')==1 else "Non ✅")
                    st.markdown('</div>', unsafe_allow_html=True)
                with tab_ctx:
                    st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
                    c1,c2=st.columns(2)
                    with c1:
                        st.metric("Mot bancaire", "Oui" if feats.get('mot_banking')==1 else "Non"); st.metric("Marque", marque)
                    with c2:
                        st.metric("Mot suspect", "Oui" if feats.get('mot_suspect')==1 else "Non")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with st.expander("🔧 Voir 20 features JSON"):
                    st.json(feats)
                
                # Diagramme
                st.markdown('<div class="beauty-card">', unsafe_allow_html=True)
                st.markdown("#### 📊 Diagramme justification")
                import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
                labels=['IP','@','Tirets','Suspects','Banking','Longueur','Chiffres','HTTPS']
                scores=[feats.get('ip_score',0),feats.get('arobase_score',0),feats.get('nb_tirets_score',0),feats.get('suspect_score',0),feats.get('banking_score',0),feats.get('longueur_score',0),feats.get('chiffres_score',0),0 if feats.get('presence_https',0)==1 else 15]
                total=sum(scores) if sum(scores)>0 else 1; pcts=[s/total*100 for s in scores]; colors=['#FF7900' if s>30 else '#0A3D8A' if s>10 else '#6B7BA3' for s in scores]
                fig,ax=plt.subplots(figsize=(10,5)); bars=ax.barh(labels,pcts,color=colors,edgecolor='white',height=0.6)
                ax.set_xlabel('Contribution (%)'); ax.set_title(f'Justification - {marque} - {conf:.1f}%'); ax.invert_yaxis()
                for bar,p in zip(bars,pcts):
                    if p>2:
                        ax.text(bar.get_width()+1, bar.get_y()+bar.get_height()/2, f'{p:.1f}%', va='center', fontweight='bold')
                plt.tight_layout(); st.pyplot(fig)
                buf=io.BytesIO(); fig.savefig(buf, format='png', dpi=300, bbox_inches='tight'); buf.seek(0)
                st.download_button("📥 Télécharger diagramme HD", data=buf, file_name=f"diagramme_{marque}_{int(conf)}pct.png", mime="image/png")
                st.markdown('</div>', unsafe_allow_html=True)

st.caption("Projet Licence GLAR - 2026 | Orange Money & Wave ONLY")
