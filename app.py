import streamlit as st
import pickle, re, os, base64
from urllib.parse import urlparse
BASE_DIR=os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="PhishGuard Senegal", page_icon="🛡️", layout="centered")
@st.cache_data(show_spinner=False)
def get_b64(p):
 try:
  if os.path.exists(p):
   with open(p,"rb") as f:
    return base64.b64encode(f.read()).decode()
 except: pass
 return ""
estm_b64=get_b64(os.path.join(BASE_DIR,"estm_logo.png"))
babacar_b64=get_b64(os.path.join(BASE_DIR,"Babacar_Mbow.jpg"))
def extract_features(url):
 try:
  d={}; d['longueur_url']=len(url); d['nb_tirets']=url.count("-"); d['nb_points']=url.count(".")
  d['presence_ip']=1 if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", url) else 0
  d['nb_arobase']=url.count("@")
  d['mot_banking']=1 if any(w in url.lower() for w in ["orange","wave","money","paypal","bank"]) else 0
  d['mot_suspect']=1 if any(w in url.lower() for w in ["securite","verif","bonus","login","urgent"]) else 0
  return d
 except: return {'longueur_url':len(url)}
def load_model():
 try:
  import sklearn
 except ImportError:
  return None
 for p in [os.path.join(BASE_DIR,"model_rf.pkl"),"model_rf.pkl"]:
  if os.path.exists(p):
   try:
    with open(p,"rb") as f:
     return pickle.load(f)
   except:
    try:
     import joblib; return joblib.load(p)
    except: continue
 return None
model=load_model()
if estm_b64 or babacar_b64:
 st.markdown(f'<div style="background:white; border:1px solid #E8EEFF; border-radius:16px; padding:14px; display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;"><div style="display:flex; align-items:center; gap:12px;"><img src="data:image/png;base64,{estm_b64}" style="height:32px;" /><div><div style="font-weight:900; font-size:13px;">ESTM DAKAR</div></div></div><div style="display:flex; align-items:center; gap:10px;"><div style="text-align:right;"><div style="font-weight:800; font-size:12px;">Babacar MBOW</div></div><img src="data:image/jpeg;base64,{babacar_b64}" style="width:38px; height:38px; border-radius:50%;" /></div></div>', unsafe_allow_html=True)
st.title("🛡️ Détecteur de Phishing par IA")
st.subheader("Projet GLAR - ESTM Dakar")
if model is None:
 st.info("Mode heuristique actif")
url_input=st.text_input("URL:", placeholder="https://exemple.com")
c1,c2,c3=st.columns(3)
with c1:
 if st.button("Google"): url_input="https://www.google.com"
with c2:
 if st.button("Orange"): url_input="http://orange-money-secure-login.com@192.168.1.1/verify"
with c3:
 if st.button("PayPal"): url_input="http://paypal-secure-confirm-2024.com/login"
if st.button("Analyser", type="primary") and url_input:
 feats=extract_features(url_input)
 score=feats.get('nb_tirets',0)*10+feats.get('mot_banking',0)*30+feats.get('mot_suspect',0)*20+feats.get('presence_ip',0)*50+feats.get('nb_arobase',0)*40
 conf=min(99.0,max(5.0,score))
 pred=1 if conf>60 else 0
 if model is not None:
  try:
   vec=[0]*19+[score]
   pred=int(model.predict([vec])[0]); proba=model.predict_proba([vec])[0]; conf=float(proba[1]*100) if len(proba)>1 else conf
  except: pass
 if pred==1:
  st.error(f"PHISHING DETECTE - {conf:.1f}%"); st.progress(conf/100)
 else:
  st.success(f"SITE LEGITIME - {100-conf:.1f}%"); st.progress((100-conf)/100)
 with st.expander("Features"): st.json(feats)
st.caption("ESTM - Babacar MBOW - 2026")
