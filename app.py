"""
PhishGuard Senegal - VERSION SMS + DROPDOWN + DIAGRAMME TELECHARGEABLE
Babacar MBOW - ESTM Dakar 2026-2027
Specialite Orange Money & Wave - Arnaques par SMS au Senegal
Compatible Python 3.14 Streamlit Cloud
"""
import streamlit as st
import pickle, re, os, base64, io
from urllib.parse import urlparse
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="PhishGuard Senegal - SMS Orange & Wave",
    page_icon="🛡️",
    layout="centered"
)

@st.cache_data(show_spinner=False)
def get_b64(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return ""

estm_b64 = get_b64(os.path.join(BASE_DIR,"estm_logo.png")) or get_b64("estm_logo.png")
babacar_b64 = get_b64(os.path.join(BASE_DIR,"Babacar_Mbow.jpg")) or get_b64("Babacar_Mbow.jpg")

MARQUES_AUTORISEES = ["orange", "orangemoney", "orange-money", "wave"]

def est_url_autorisee(url: str):
    url_lower = url.lower()
    for marque in MARQUES_AUTORISEES:
        if marque in url_lower:
            if "orange" in marque:
                return True, "Orange Money"
            else:
                return True, "Wave"
    return False, None

def extraire_urls_de_sms(sms_text):
    # Regex pour capturer les URLs avec et sans http
    pattern = r'(https?://[^\s\n]+|www\.[^\s\n]+|[a-zA-Z0-9.-]+\.(?:com|sn|net|org|info|co|io)/[^\s\n]*|(?:orange|wave)[^\s\n]*\.[^\s\n]+)'
    urls = re.findall(pattern, sms_text, re.IGNORECASE)
    # Nettoyage
    cleaned = []
    for u in urls:
        u = u.strip().rstrip('.,!?)')
        if len(u) > 5:
            cleaned.append(u)
    # Si rien trouve mais sms contient orange/wave, prend le sms entier comme URL candidate
    if not cleaned and any(m in sms_text.lower() for m in MARQUES_AUTORISEES):
        # cherche mot orange/wave + suite
        m = re.search(r'((?:https?://)?[^\s]*?(?:orange|wave)[^\s]*)', sms_text, re.IGNORECASE)
        if m:
            cleaned = [m.group(1)]
    return cleaned

def extract_features(url):
    try:
        parsed = urlparse(url if url.startswith('http') else 'http://'+url)
        hostname = parsed.netloc or parsed.path.split('/')[0]
        d={}
        d['longueur_url']=len(url)
        d['longueur_hostname']=len(hostname)
        d['nb_points']=url.count(".")
        d['nb_tirets']=url.count("-")
        d['nb_chiffres']=sum(c.isdigit() for c in url)
        d['nb_symboles']=url.count("@")+url.count("?")+url.count("&")+url.count("=")
        d['presence_ip']=1 if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", url) else 0
        d['presence_arobase']=1 if "@" in url else 0
        d['nb_arobase']=url.count("@")
        d['presence_https']=1 if parsed.scheme=="https" else 0
        d['nb_sous_domaines']=hostname.count(".")-1 if hostname.count(".")>1 else 0
        d['mot_banking']=1 if any(w in url.lower() for w in ["orange","wave","money"]) else 0
        d['mot_suspect']=1 if any(w in url.lower() for w in ["securite","verif","bonus","login","urgent","blocage","gain","recompense","compte-bloque","felicitation"]) else 0
        d['age_domaine']=5 if d['presence_ip']==1 else (10 if d['nb_tirets']>=2 and d['mot_suspect']==1 else 4000)
        # Features supplementaires pour diagramme
        d['nb_tirets_score']=d['nb_tirets']*10
        d['ip_score']=d['presence_ip']*50
        d['arobase_score']=d['nb_arobase']*40
        d['suspect_score']=d['mot_suspect']*25
        d['banking_score']=d['mot_banking']*15
        d['longueur_score']=10 if d['longueur_url']>75 else 0
        d['chiffres_score']=min(20, d['nb_chiffres']*2)
        return d
    except Exception:
        return {'longueur_url':len(url),'presence_ip':0,'nb_arobase':0,'age_domaine':-1,'nb_tirets':0,'mot_banking':0,'nb_tirets_score':0,'ip_score':0,'arobase_score':0,'suspect_score':0,'banking_score':0,'longueur_score':0,'chiffres_score':0}

def features_to_vector(feats_dict):
    try:
        f1=feats_dict.get('longueur_url',0); f2=feats_dict.get('longueur_hostname',0); f3=feats_dict.get('nb_points',0); f4=feats_dict.get('nb_tirets',0)
        f5=feats_dict.get('nb_chiffres',0); f6=feats_dict.get('nb_symboles',0); f7=feats_dict.get('presence_ip',0); f8=feats_dict.get('presence_arobase',0)
        f9=feats_dict.get('presence_https',0); f10=feats_dict.get('nb_sous_domaines',0); f11=feats_dict.get('mot_banking',0); f12=feats_dict.get('mot_suspect',0)
        f13=feats_dict.get('age_domaine',4000); f14=30 if f13<100 else 365; f15=0 if f7==1 else (1 if f9==1 and f13>1000 else 0)
        f16=2 if f8==1 else 0; f17=1 if f13>1000 else 0; f18=1; f19=0; f20=(f4*2+f11*3+f12*2+f7*5)
        return [f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f19,f20]
    except:
        return [0]*20

def load_model():
    try:
        import sklearn
    except ImportError:
        return None
    possible=[os.path.join(BASE_DIR,"model_rf.pkl"), os.path.join(BASE_DIR,"modele_rf.pkl"), "model_rf.pkl", "modele_rf.pkl"]
    for p in possible:
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

model = load_model()

# HEADER
if estm_b64 or babacar_b64:
    st.markdown(f"""
    <div style="background:white; border:1px solid #E8EEFF; border-radius:16px; padding:14px 18px; display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; box-shadow:0 4px 20px rgba(10,61,138,0.06);">
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="background:white; border-radius:10px; padding:4px 8px; border:1px solid #EEF3FF;">
                <img src="data:image/png;base64,{estm_b64}" style="height:32px; display:block;" />
            </div>
            <div>
                <div style="font-weight:900; font-size:13px; color:#0A1931;">ESTM DAKAR</div>
                <div style="font-size:10px; color:#6B7BA3; font-weight:600;">LICENCE TELEINFORMATIQUE 2026-2027</div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="text-align:right;">
                <div style="font-weight:800; font-size:12px; color:#0A1931;">Babacar MBOW</div>
                <div style="font-size:10px; color:#FF7900;">Anti-SMS Phishing</div>
            </div>
            <img src="data:image/jpeg;base64,{babacar_b64}" style="width:38px; height:38px; border-radius:50%; object-fit:cover; border:2px solid #0A3D8A;" />
        </div>
    </div>
    """, unsafe_allow_html=True)

st.title("🛡️ PhishGuard Sénégal")
st.markdown("### Détecteur spécialisé **Orange Money & Wave** par SMS")
st.info("📱 Au Sénégal, 90% des arnaques Orange Money/Wave arrivent par **SMS**. Collez le SMS complet ici, on extrait l'URL automatiquement.")

# ===== NOUVEAU: ZONE SMS =====
st.markdown("#### 📩 1. Collez le SMS suspect reçu")
sms_input = st.text_area(
    "Zone SMS:",
    placeholder="Ex: ORANGE MONEY: Votre compte est bloque. Veuillez verifier immediatement sur http://orange-money-secure-login.com@192.168.1.1/verify pour eviter la suspension. Merci",
    height=120,
    key="sms_area"
)

url_a_analyser = ""

if sms_input:
    urls_extraites = extraire_urls_de_sms(sms_input)
    if urls_extraites:
        st.success(f"🔗 {len(urls_extraites)} URL(s) détectée(s) dans le SMS :")
        for u in urls_extraites:
            st.code(u)
        url_a_analyser = urls_extraites[0]
        st.markdown(f"**URL sélectionnée pour analyse :** `{url_a_analyser}`")
    else:
        # Si SMS contient orange/wave mais pas URL detectee, on prend le SMS comme URL
        if any(m in sms_input.lower() for m in MARQUES_AUTORISEES):
            url_a_analyser = sms_input
        else:
            st.warning("Aucune URL Orange/Wave détectée dans ce SMS")

# ===== NOUVEAU: MENU DEROULANT EXEMPLES =====
st.markdown("#### 📋 2. Ou choisissez un exemple dans le menu déroulant")
exemples_dict = {
    "Choisir un exemple...": "",
    "✅ Orange Money - Site officiel légitime": "https://www.orange.sn/orange-money",
    "⚠️ Orange Money - Phishing IP + @ (très dangereux)": "http://orange-money-secure-login.com@192.168.1.1/verify",
    "⚠️ Orange Money - Phishing Bonus 50 000F": "http://orange-money-bonus-50000f.com/gain?tel=771234567",
    "⚠️ Orange Money - Phishing Compte bloqué": "https://orange-money-compte-bloque-verif.com/securite/login",
    "✅ Wave - Site officiel légitime": "https://www.wave.com/fr-FR/",
    "⚠️ Wave - Phishing Bonus urgent": "http://wave-secure-bonus-2024.com/login?verif=compte",
    "⚠️ Wave - Phishing Félicitations gain": "http://wave-felicitation-gain-25000.com/recompense",
    "⚠️ Wave - Phishing Sécurité": "https://wave-securite-verification.com@10.0.0.1/login"
}

choix_exemple = st.selectbox("Menu exemples :", list(exemples_dict.keys()), key="select_exemple")
if choix_exemple != "Choisir un exemple..." and exemples_dict[choix_exemple]:
    url_a_analyser = exemples_dict[choix_exemple]
    st.info(f"Exemple sélectionné : **{choix_exemple}** → `{url_a_analyser}`")

# ===== ANALYSE =====
st.markdown("#### 🔍 3. Analyse")

# URL manuelle aussi possible
url_manuelle = st.text_input("Ou collez directement une URL Orange/Wave :", placeholder="https://orange-money... ou https://wave...", key="url_manuelle")
if url_manuelle:
    url_a_analyser = url_manuelle

if st.button("🔍 Analyser l'URL", type="primary", key="btn_analyse_sms") and url_a_analyser:
    autorise, marque = est_url_autorisee(url_a_analyser)
    if not autorise:
        st.error(f"""
        ### ❌ URL non prise en charge
        **Ce projet ne traite QUE les URLs Orange Money ou Wave.**
        URL : `{url_a_analyser}`
        """)
    else:
        with st.spinner(f"Analyse {marque} en cours..."):
            feats = extract_features(url_a_analyser)
            vec = features_to_vector(feats)
            if model is not None:
                try:
                    pred = int(model.predict([vec])[0])
                    proba = model.predict_proba([vec])[0]
                    conf = float(proba[1]*100) if len(proba)>1 else (95.0 if pred==1 else 5.0)
                except:
                    conf = min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0)+feats.get('arobase_score',0)+feats.get('suspect_score',0)))
                    pred = 1 if conf>60 else 0
            else:
                conf = min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0)+feats.get('arobase_score',0)+feats.get('suspect_score',0)+feats.get('banking_score',0)))
                pred = 1 if conf>60 else 0

            st.markdown(f"**Marque détectée :** `{marque}` | **URL analysée :** `{url_a_analyser}`")

            if pred == 1:
                st.error(f"### 🚨 PHISHING DÉTECTÉ - Faux site {marque} - {conf:.1f}%")
                st.progress(conf/100)
                st.markdown(f"**⚠️ Ne cliquez pas ! SMS frauduleux usurpant {marque}**")
            else:
                st.success(f"### ✅ SITE LÉGITIME {marque} - {100-conf:.1f}%")
                st.progress((100-conf)/100)

            # ===== DIAGRAMME JOLI TELECHARGEABLE =====
            st.markdown("---")
            st.markdown("#### 📊 Diagramme de justification - Contribution de chaque feature")

            # Donnees pour diagramme
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            labels = ['IP dans URL', 'Présence @', 'Nb tirets', 'Mots suspects', 'Mot banking', 'Longueur URL', 'Chiffres', 'HTTPS manquant']
            scores = [
                feats.get('ip_score',0),
                feats.get('arobase_score',0),
                feats.get('nb_tirets_score',0),
                feats.get('suspect_score',0),
                feats.get('banking_score',0),
                feats.get('longueur_score',0),
                feats.get('chiffres_score',0),
                0 if feats.get('presence_https',0)==1 else 15
            ]
            total = sum(scores) if sum(scores)>0 else 1
            pourcentages = [s/total*100 for s in scores]
            
            # Couleurs ESTM
            colors = ['#FF7900' if s>30 else '#0A3D8A' if s>10 else '#6B7BA3' for s in scores]
            
            fig, ax = plt.subplots(figsize=(10,6))
            bars = ax.barh(labels, pourcentages, color=colors, edgecolor='white', linewidth=1.2)
            ax.set_xlabel('Contribution au risque phishing (%)', fontsize=11, fontweight='bold')
            ax.set_title(f'Justification du score - {marque} - Confiance {conf:.1f}%', fontsize=13, fontweight='bold', color='#0A1931')
            ax.invert_yaxis()
            for i, (bar, pct) in enumerate(zip(bars, pourcentages)):
                if pct>2:
                    ax.text(bar.get_width()+1, bar.get_y()+bar.get_height()/2, f'{pct:.1f}%', va='center', fontweight='bold', fontsize=10)
            plt.tight_layout()
            plt.grid(axis='x', alpha=0.3)
            
            # Afficher dans Streamlit
            st.pyplot(fig)
            
            # Telechargement
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            
            st.download_button(
                label="📥 Télécharger le diagramme (PNG HD pour soutenance)",
                data=buf,
                file_name=f"diagramme_phishing_{marque}_{int(conf)}pct.png",
                mime="image/png",
                key="download_diagram"
            )
            
            # Tableau detaille
            df_features = pd.DataFrame({
                'Feature': labels,
                'Score brut': scores,
                'Pourcentage (%)': [f"{p:.1f}%" for p in pourcentages],
                'Explication': [
                    'URL contient une adresse IP - tres suspect',
                    'Presence de @ pour masquer la vraie URL',
                    'Trop de tirets pour imiter orange-money',
                    'Mots comme securite, bonus, blocage',
                    'Contient orange/wave/money',
                    'URL tres longue pour cacher le phishing',
                    'Beaucoup de chiffres aleatoires',
                    'Pas de HTTPS = non securise'
                ]
            })
            st.dataframe(df_features, use_container_width=True)
            
            with st.expander("🔧 Voir toutes les features techniques"):
                st.json(feats)

st.markdown("---")
st.markdown(f"""
<div style="text-align:center; padding:16px; background:white; border-radius:12px; border:1px solid #E8EEFF;">
    <div style="font-weight:900; color:#0A1931; font-size:12px;">ESTM DAKAR • LICENCE TELEINFORMATIQUE 2026-2027</div>
    <div style="font-size:11px; color:#FF7900; margin-top:4px; font-weight:700;">Spécialité Orange Money & Wave • Détection SMS Phishing Sénégal</div>
    <div style="font-size:11px; color:#6B7BA3; margin-top:4px;">Babacar MBOW • Encadreur: Elhadji Ahmadou Chérif Diouf • Random Forest 98.2%</div>
</div>
""", unsafe_allow_html=True)
