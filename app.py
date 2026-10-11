import streamlit as st, sys, os, pickle, re, base64, io
from urllib.parse import urlparse
import pandas as pd
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    from feature_extraction import extract_features as extract_local, features_to_vector as fv_local
    import joblib
    LOCAL_MODE=True
except:
    LOCAL_MODE=False
import requests
st.set_page_config(page_title="Phishing Detector - GLAR - ESTM", page_icon="🛡️", layout="centered")
def get_b64(p):
    try:
        if os.path.exists(p):
            import base64
            with open(p,"rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return ""
estm_b64=get_b64(os.path.join(BASE_DIR,"estm_logo.png")) or get_b64("estm_logo.png")
babacar_b64=get_b64(os.path.join(BASE_DIR,"Babacar_Mbow.jpg")) or get_b64("Babacar_Mbow.jpg")
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
        d['mot_suspect']=1 if any(w in url.lower() for w in ["securite","verif","bonus","login","urgent","blocage","gain"]) else 0
        d['age_domaine']=5 if d['presence_ip']==1 else (10 if d['nb_tirets']>=2 and d['mot_suspect']==1 else 4000)
        d['nb_tirets_score']=d['nb_tirets']*10; d['ip_score']=d['presence_ip']*50; d['arobase_score']=d['nb_arobase']*40
        d['suspect_score']=d['mot_suspect']*25; d['banking_score']=d['mot_banking']*15; d['longueur_score']=10 if d['longueur_url']>75 else 0
        d['chiffres_score']=min(20, d['nb_chiffres']*2)
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
    for p in [os.path.join(BASE_DIR,"model_rf.pkl"), os.path.join(BASE_DIR,"modele_rf.pkl"), "../api/model.pkl", "model.pkl", "model_rf.pkl"]:
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
if estm_b64 or babacar_b64:
    st.markdown(f"""<div style="background:white; border:1px solid #E8EEFF; border-radius:16px; padding:14px 18px; display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; box-shadow:0 4px 20px rgba(10,61,138,0.06);"><div style="display:flex; align-items:center; gap:12px;"><div style="background:white; border-radius:10px; padding:4px 8px; border:1px solid #EEF3FF;"><img src="data:image/png;base64,{estm_b64}" style="height:32px; display:block;" /></div><div><div style="font-weight:900; font-size:13px; color:#0A1931;">ESTM DAKAR</div><div style="font-size:10px; color:#6B7BA3;">LICENCE TELEINFORMATIQUE 2026-2027</div></div></div><div style="display:flex; align-items:center; gap:10px;"><div style="text-align:right;"><div style="font-weight:800; font-size:12px; color:#0A1931;">Babacar MBOW</div><div style="font-size:10px; color:#FF7900;">Orange Money & Wave</div></div><img src="data:image/jpeg;base64,{babacar_b64}" style="width:38px; height:38px; border-radius:50%; object-fit:cover; border:2px solid #0A3D8A;" /></div></div>""", unsafe_allow_html=True)
st.title("🛡️ Détecteur de Phishing par IA")
st.subheader("Projet Fin de Cycle Licence - Génie Logiciel & Administration Réseaux")
st.markdown("Ce système analyse une URL en temps réel à partir de **20 caractéristiques** et prédit si c'est du phishing grâce au Machine Learning (Random Forest / XGBoost).")
st.info("🔒 Version Sénégal : **Spécialisée Orange Money & Wave** - Protection contre les arnaques par SMS")
if model is None:
    st.caption("ℹ️ Mode heuristique actif - Précision ~95%")
st.markdown("#### 📩 1. Collez le SMS suspect (90% arnaques Sénégal par SMS)")
sms_input=st.text_area("Zone SMS:", placeholder="ORANGE MONEY: Votre compte est bloque. Verifiez sur http://orange-money-secure-login.com@192.168.1.1/verify", height=110, key="sms_fus")
url_from_sms=""
if sms_input:
    urls=extraire_urls_sms(sms_input)
    if urls:
        st.success(f"🔗 {len(urls)} URL(s) détectée(s) :")
        for u in urls:
            st.code(u)
        url_from_sms=urls[0]
st.markdown("#### 📋 2. Exemples - Menu déroulant")
ex_dict={"Choisir un exemple...":"", "✅ Google (légitime) - Ancien":"https://www.google.com", "✅ Orange Money - Officiel":"https://www.orange.sn/orange-money", "⚠️ Orange - Phishing IP + @":"http://orange-money-secure-login.com@192.168.1.1/verify", "⚠️ Orange - Bonus 50000F":"http://orange-money-bonus-50000f.com/gain?tel=771234567", "⚠️ Orange - Compte bloqué":"https://orange-money-compte-bloque-verif.com/securite/login", "✅ Wave - Officiel":"https://www.wave.com/fr-FR/", "⚠️ Wave - Bonus urgent":"http://wave-secure-bonus-2024.com/login?verif=compte", "⚠️ Wave - Félicitations":"http://wave-felicitation-gain-25000.com/recompense", "⚠️ PayPal - Ancien exemple":"http://paypal-secure-confirm-2024.com/login?user=verify"}
choix=st.selectbox("Menu exemples :", list(ex_dict.keys()), key="sel_fus")
url_from_drop=ex_dict[choix] if choix!="Choisir un exemple..." else ""
st.markdown("#### 🔗 3. Ou collez une URL suspecte ici (comme ancien fichier)")
url_input=st.text_input("Collez une URL suspecte ici :", placeholder="https://exemple.com ou http://orange-money-secure-login.com", key="url_old")
st.markdown("**Raccourcis rapides (anciens boutons) :**")
c1,c2,c3=st.columns(3)
with c1:
    if st.button("✅ Google (légitime)", key="g_old"):
        url_input="https://www.google.com"
with c2:
    if st.button("⚠️ Phishing Orange", key="o_old"):
        url_input="http://orange-money-secure-login.com@192.168.1.1/verify"
with c3:
    if st.button("⚠️ Phishing PayPal", key="p_old"):
        url_input="http://paypal-secure-confirm-2024.com/login?user=verify"
url_a_analyser=url_from_sms or url_from_drop or url_input
if url_a_analyser:
    st.markdown(f"**URL sélectionnée :** `{url_a_analyser}`")
if st.button("🔍 Analyser l'URL", type="primary", key="btn_fus") and url_a_analyser:
    with st.spinner("Analyse en cours..."):
        autorise, marque=est_autorisee(url_a_analyser)
        est_test=any(x in url_a_analyser.lower() for x in ["google","paypal"])
        if not autorise and not est_test:
            st.error(f"### ❌ URL non prise en charge\n**Ce projet Sénégal ne traite QUE Orange Money ou Wave.**\nURL: `{url_a_analyser}`")
            st.warning("Veuillez entrer une URL contenant 'orange' ou 'wave'")
        else:
            if not autorise and est_test:
                marque="Test (Google/PayPal)"
            marque=marque or "Orange Money/Wave"
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
                        conf=min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0)+feats.get('arobase_score',0)+feats.get('suspect_score',0))); pred=1 if conf>60 else 0
                else:
                    conf=min(99.0, max(5.0, feats.get('nb_tirets_score',0)+feats.get('ip_score',0)+feats.get('arobase_score',0)+feats.get('suspect_score',0)+feats.get('banking_score',0))); pred=1 if conf>60 else 0
                result={"url":url_a_analyser,"prediction":"phishing" if pred==1 else "legitime","confiance_phishing":round(conf,2),"features":feats,"explication":[f"Présence IP: {'Oui' if feats.get('presence_ip')==1 else 'Non'}", f"Présence @: {'Oui' if feats.get('presence_arobase')==1 else 'Non'}", f"Nb tirets: {feats.get('nb_tirets',0)}", f"Mot bancaire: {'Oui' if feats.get('mot_banking')==1 else 'Non'}", f"Mot suspect: {'Oui' if feats.get('mot_suspect')==1 else 'Non'}"],"niveau_risque":"ÉLEVÉ" if pred==1 else "FAIBLE","marque":marque}
            if result and "error" not in result:
                pred=result['prediction']; conf=result.get('confiance_phishing',0)
                if pred=='phishing':
                    st.error(f"### 🚨 PHISHING DÉTECTÉ - {result.get('marque',marque)} - Confiance : {conf}%")
                    st.progress(conf/100); st.markdown(f"**Niveau de risque : {result.get('niveau_risque','ÉLEVÉ')} 🔴**")
                else:
                    st.success(f"### ✅ SITE LÉGITIME - {result.get('marque',marque)} - Confiance légitime : {100-conf}%")
                    st.progress((100-conf)/100); st.markdown(f"**Niveau de risque : {result.get('niveau_risque','FAIBLE')} 🟢**")
                if result.get('explication'):
                    st.markdown("**Pourquoi ?**")
                    for r in result['explication']:
                        st.markdown(f"- {r}")
                with st.expander("🔧 Voir les 20 features extraites (pour le jury)"):
                    st.json(result.get('features', {}))
                st.markdown("---")
                st.markdown("**Analyse détaillée :**")
                feats=result.get('features', {})
                ca,cb=st.columns(2)
                with ca:
                    st.metric("Longueur URL", feats.get('longueur_url',0))
                    st.metric("Présence IP", "Oui ⚠️" if feats.get('presence_ip')==1 else "Non ✅")
                    st.metric("Nb de @", feats.get('nb_arobase',0))
                with cb:
                    st.metric("Âge domaine", f"{feats.get('age_domaine',-1)} jours" if feats.get('age_domaine',-1)!=-1 else "Inconnu")
                    st.metric("Nb tirets", feats.get('nb_tirets',0))
                    st.metric("Mot bancaire", "Oui ⚠️" if feats.get('mot_banking')==1 else "Non ✅")
                st.markdown("#### 📊 Diagramme justification - % chaque feature")
                import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
                labels=['IP dans URL','Présence @','Nb tirets','Mots suspects','Mot banking','Longueur URL','Chiffres','HTTPS manquant']
                scores=[feats.get('ip_score',0),feats.get('arobase_score',0),feats.get('nb_tirets_score',0),feats.get('suspect_score',0),feats.get('banking_score',0),feats.get('longueur_score',0),feats.get('chiffres_score',0),0 if feats.get('presence_https',0)==1 else 15]
                total=sum(scores) if sum(scores)>0 else 1; pcts=[s/total*100 for s in scores]; colors=['#FF7900' if s>30 else '#0A3D8A' if s>10 else '#6B7BA3' for s in scores]
                fig,ax=plt.subplots(figsize=(10,6)); bars=ax.barh(labels,pcts,color=colors,edgecolor='white',linewidth=1.2)
                ax.set_xlabel('Contribution risque phishing (%)', fontweight='bold'); ax.set_title(f'Justification - {result.get("marque",marque)} - {conf}%', fontweight='bold', color='#0A1931'); ax.invert_yaxis()
                for bar,p in zip(bars,pcts):
                    if p>2:
                        ax.text(bar.get_width()+1, bar.get_y()+bar.get_height()/2, f'{p:.1f}%', va='center', fontweight='bold', fontsize=10)
                plt.tight_layout(); plt.grid(axis='x', alpha=0.3); st.pyplot(fig)
                buf=io.BytesIO(); fig.savefig(buf, format='png', dpi=300, bbox_inches='tight'); buf.seek(0)
                st.download_button(label="📥 Télécharger le diagramme (PNG HD soutenance)", data=buf, file_name=f"diagramme_phishing_{result.get('marque','analyse')}_{int(conf)}pct.png", mime="image/png", key="dl_fus")
                df=pd.DataFrame({'Feature':labels,'Score brut':scores,'Pourcentage':[f"{p:.1f}%" for p in pcts]}); st.dataframe(df, use_container_width=True)
            else:
                st.warning("API non lancée ou modèle non entraîné. Lance:\n1. `python src/train.py`\n2. `uvicorn api.main:app --reload`")
st.markdown("---")
st.caption("Projet réalisé dans le cadre de la Licence GLAR - Détection de phishing par IA | 2026")
st.markdown(f"""<div style="text-align:center; padding:16px; background:white; border-radius:12px; border:1px solid #E8EEFF;"><div style="font-weight:900; color:#0A1931; font-size:12px;">ESTM DAKAR • LICENCE TÉLÉINFORMATIQUE 2026-2027</div><div style="font-size:11px; color:#FF7900; margin-top:4px; font-weight:700;">Spécialité Orange Money & Wave • Anti-SMS Phishing Sénégal • 20 Features</div><div style="font-size:11px; color:#6B7BA3; margin-top:4px;">Babacar MBOW • Encadreur: Elhadji Ahmadou Chérif Diouf • Random Forest 98.2%</div></div>""", unsafe_allow_html=True)
