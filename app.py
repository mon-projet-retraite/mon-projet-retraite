import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Companion Quantfury", layout="wide")

st.title("🛡️ Companion Retraite & Autonomie")
st.subheader("Détection des Splits Forward & Calculateur POC Quantfury")

# Chargement de la liste Quantfury
@st.cache_data
def load_quantfury_list():
    try:
        df = pd.read_csv("Liste_quantfury.csv")
        return df['Ticker'].dropna().str.strip().unique().tolist()
    except Exception:
        return []

quantfury_tickers = load_quantfury_list()

# Calcul du POC (Volume Profile)
def get_poc_price(ticker_symbol, days=15, bins=30):
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="2mo", interval="1d")
        if data.empty:
            return None
        
        data = data.tail(days)
        prices = (data['High'] + data['Low'] + data['Close']) / 3
        volumes = data['Volume']
        
        counts, bin_edges = np.histogram(prices, bins=bins, weights=volumes)
        max_idx = np.argmax(counts)
        poc_price = (bin_edges[max_idx] + bin_edges[max_idx+1]) / 2
        return round(float(poc_price), 2)
    except Exception:
        return None

# Organisation par Onglets
tab1, tab2 = st.tabs(["🔎 Scanner des Candidates Split", "📐 Calculateur des 3 Ordres (POC)"])

# --- ONGLET 1 : SCANNER DES SPLITS ---
with tab1:
    st.markdown("### 📡 Détection des Splits Récoltés sur Quantfury")
    st.write("Ce scanner analyse la liste de vos tickers éligibles sur Quantfury pour détecter les splits récents ou imminents.")
    
    if st.button("🚀 Lancer le scan des tickers Quantfury"):
        if not quantfury_tickers:
            st.error("Fichier 'Liste_quantfury.csv' introuvable sur GitHub.")
        else:
            detected_splits = []
            progress_bar = st.progress(0)
            
            # Analyse des tickers (échantillon/liste)
            for i, ticker_code in enumerate(quantfury_tickers[:50]): # Scan des 50 premiers
                try:
                    tk = yf.Ticker(ticker_code)
                    splits = tk.splits
                    if not splits.empty:
                        last_split_date = splits.index[-1].tz_localize(None)
                        days_since = (datetime.now() - last_split_date).days
                        
                        # Si le split a eu lieu il y a moins de 60 jours
                        if 0 <= days_since <= 60:
                            ratio = splits.iloc[-1]
                            status = "🎯 Prêt (Post 15 jours)" if days_since >= 15 else f"⏳ En observation (Jour {days_since}/15)"
                            detected_splits.append({
                                "Ticker": ticker_code,
                                "Date du Split": last_split_date.strftime('%Y-%m-%d'),
                                "Ratio": f"{int(ratio)}:1" if ratio >= 1 else f"1:{int(1/ratio)}",
                                "Jours écoulés": days_since,
                                "Statut": status
                            })
                except Exception:
                    pass
                progress_bar.progress((i + 1) / min(len(quantfury_tickers), 50))
            
            if detected_splits:
                df_results = pd.DataFrame(detected_splits)
                st.dataframe(df_results, use_container_width=True)
            else:
                st.info("Aucun split récent (moins de 60 jours) trouvé dans l'échantillon scanné.")

# --- ONGLET 2 : CALCULATEUR D'ORDRES ---
with tab2:
    st.sidebar.header("⚙️ Configuration Ligne")
    capital_ligne = st.sidebar.number_input("Capital par ligne ($)", min_value=100, max_value=5000, value=750, step=50)

    selected_ticker = st.text_input("Entrez un Ticker validé (ex: NVDA) :", value="NVDA").strip().upper()

    if selected_ticker:
        is_in_qf = selected_ticker in quantfury_tickers if quantfury_tickers else True
        
        if quantfury_tickers and not is_in_qf:
            st.error(f"⚠️ **{selected_ticker}** N'EST PAS dans votre liste Quantfury.")
        else:
            if quantfury_tickers:
                st.success(f"✅ **{selected_ticker}** est validé et disponible sur Quantfury !")
            
            with st.spinner(f"Calcul du POC post-15 jours pour {selected_ticker}..."):
                auto_poc = get_poc_price(selected_ticker, days=15)
            
            poc_prix = auto_poc if auto_poc else st.number_input("Prix Achat / POC ($)", min_value=0.1, value=50.0, step=0.5)

            if poc_prix > 0:
                st.metric(label=f"POC Calculé (15j) - {selected_ticker}", value=f"{poc_prix} $")
                
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
                    st.write(f"**Achat:** {poc_prix} $ | **SL:** {sl_initial} $ | **TP1:** {tp1_prix} $")
                    
                with col2:
                    st.metric("Ordre 2 (TP2)", f"{qte_tp2} titres")
                    st.write(f"**Achat:** {poc_prix} $ | **SL:** {sl_initial} $ | **TP2:** {tp2_prix} $")
                    
                with col3:
                    st.metric("Ordre 3 (Moonbag)", f"{qte_moonbag} titres")
                    st.write(f"**Achat:** {poc_prix} $ | **SL:** {sl_initial} $ | **TP (Trailing):** Actif")
                
                st.markdown("---")
                
                fiche_text = f"""--- FICHE D'EXÉCUTION QUANTFURY ({selected_ticker}) ---
Achat total: {nb_titres} titres @ {poc_prix} $ ({engagement} $)

1. ORDRE TP1: {qte_tp1} titres | Achat: {poc_prix} $ | SL: {sl_initial} $ | TP1: {tp1_prix} $
2. ORDRE TP2: {qte_tp2} titres | Achat: {poc_prix} $ | SL: {sl_initial} $ | TP2: {tp2_prix} $
3. MOONBAG:   {qte_moonbag} titres | Achat: {poc_prix} $ | SL: {sl_initial} $ | TP: Trailing Stop
--------------------------------------------------"""
                st.text_area("📋 Fiche synthétique :", fiche_text, height=140)
