import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Companion Quantfury", layout="wide")

st.title("🛡️ Companion Retraite & Autonomie")
st.subheader("Détection Split Forward & Calculateur Automatique de POC")

# Chargement de la liste Quantfury
@st.cache_data
def load_quantfury_list():
    try:
        df = pd.read_csv("Liste_quantfury.csv")
        return df['Ticker'].dropna().str.strip().unique().tolist()
    except Exception as e:
        st.warning("Impossible de charger 'Liste_quantfury.csv'. Utilisation de la saisie manuelle.")
        return []

quantfury_tickers = load_quantfury_list()

# Fonction de calcul du POC (Volume Profile sur 15 jours)
def get_poc_price(ticker_symbol, days=15, bins=30):
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="1m", interval="1h")
        if data.empty or len(data) < 10:
            data = ticker.history(period="3mo", interval="1d")
        
        if data.empty:
            return None
        
        # Filtre sur les 15 derniers jours de cotation
        data = data.tail(days * 7) if "1h" in str(data.index.freq) else data.tail(days)
        
        prices = (data['High'] + data['Low'] + data['Close']) / 3
        volumes = data['Volume']
        
        counts, bin_edges = np.histogram(prices, bins=bins, weights=volumes)
        max_idx = np.argmax(counts)
        poc_price = (bin_edges[max_idx] + bin_edges[max_idx+1]) / 2
        return round(float(poc_price), 2)
    except Exception:
        return None

# Menu latéral
st.sidebar.header("⚙️ Configuration Ligne")
capital_ligne = st.sidebar.number_input("Capital par ligne ($)", min_value=100, max_value=5000, value=750, step=50)

# Recherche de Ticker
st.markdown("### 🔍 Sélection du Ticker (Vérification Quantfury)")
selected_ticker = st.text_input("Entrez un Ticker (ex: NVDA, AAPL, AMZN) :", value="NVDA").strip().upper()

if selected_ticker:
    is_in_qf = selected_ticker in quantfury_tickers if quantfury_tickers else True
    
    if quantfury_tickers and not is_in_qf:
        st.error(f"⚠️ Le ticker **{selected_ticker}** N'EST PAS présent dans votre liste Quantfury. Risque d'impossibilité d'exécution.")
    else:
        if quantfury_tickers:
            st.success(f"✅ **{selected_ticker}** est validé et disponible sur Quantfury !")
        
        # Calcul automatique du POC
        with st.spinner(f"Calcul du POC post-15 jours pour {selected_ticker}..."):
            auto_poc = get_poc_price(selected_ticker, days=15)
        
        if auto_poc:
            st.metric(label=f"POC Calculé Automatiquement (15j) pour {selected_ticker}", value=f"{auto_poc} $")
            poc_prix = auto_poc
        else:
            st.info("Calcul automatique indisponible, veuillez saisir le POC manuellement.")
            poc_prix = st.number_input("Prix Achat / POC ($)", min_value=0.1, value=50.0, step=0.5)

        st.markdown("---")
        st.markdown(f"### 📋 Fiche d'exécution pour {selected_ticker}")

        if poc_prix > 0:
            nb_titres = int(capital_ligne // poc_prix)
            qte_tp1 = int(nb_titres * 0.40)
            qte_tp2 = int(nb_titres * 0.40)
            qte_moonbag = nb_titres - (qte_tp1 + qte_tp2)
            
            sl_initial = round(poc_prix * 0.94, 2)
            tp1_prix = round(poc_prix * 1.50, 2)
            tp2_prix = round(poc_prix * 2.05, 2)
            engagement = round(nb_titres * poc_prix, 2)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Ordre 1 (TP1)", f"{qte_tp1} titres")
                st.write(f"**Achat:** {poc_prix} $")
                st.write(f"**SL (-6%):** {sl_initial} $")
                st.write(f"**TP1 (x1.5):** {tp1_prix} $")
                
            with col2:
                st.metric("Ordre 2 (TP2)", f"{qte_tp2} titres")
                st.write(f"**Achat:** {poc_prix} $")
                st.write(f"**SL (-6%):** {sl_initial} $")
                st.write(f"**TP2 (x2.05):** {tp2_prix} $")
                
            with col3:
                st.metric("Ordre 3 (Moonbag)", f"{qte_moonbag} titres")
                st.write(f"**Achat:** {poc_prix} $")
                st.write(f"**SL (-6%):** {sl_initial} $")
                st.write("**TP:** Trailing Stop")
            
            st.markdown("---")
            
            fiche_text = f"""--- FICHE D'EXÉCUTION QUANTFURY ({selected_ticker}) ---
Achat total: {nb_titres} titres @ {poc_prix} $ ({engagement} $)

1. ORDRE TP1: {qte_tp1} titres | Achat: {poc_prix} $ | SL: {sl_initial} $ | TP1: {tp1_prix} $
2. ORDRE TP2: {qte_tp2} titres | Achat: {poc_prix} $ | SL: {sl_initial} $ | TP2: {tp2_prix} $
3. MOONBAG:   {qte_moonbag} titres | Achat: {poc_prix} $ | SL: {sl_initial} $ | TP: Trailing Stop
--------------------------------------------------"""
            
            st.text_area("📋 Fiche synthétique (à copier ou capturer) :", fiche_text, height=150)
