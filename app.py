import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Companion Quantfury", layout="wide")

st.markdown("""
<style>
    .stTextArea textarea {
        font-family: monospace;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# Gestion de l'état du guide (Ouvert / Fermé)
if 'show_guide' not in st.session_state:
    st.session_state.show_guide = False

def toggle_guide():
    st.session_state.show_guide = not st.session_state.show_guide

# En-tête principal avec le bouton toggle
col_title, col_settings = st.columns([0.78, 0.22])

with col_title:
    st.title("🛡️ Companion Retraite & Autonomie")
    st.subheader("Méthode 'Double Moteur' & Filtre Feu Tricolore POC")

with col_settings:
    st.write("")
    btn_label = "❌ Fermer le Guide" if st.session_state.show_guide else "⚙️ Guide & Règles"
    st.button(btn_label, on_click=toggle_guide, use_container_width=True)

# Fenêtre d'explications / Guide complet
if st.session_state.show_guide:
    with st.container():
        st.info("📖 **GUIDE COMPLET DE LA STRATÉGIE**")
        st.markdown("""
        ### 🚀 Bienvenue dans le Système Double Moteur

        Ce système a été conçu pour construire et protéger votre patrimoine de manière ultra-disciplinée.
        **Temps requis : 3 minutes le samedi matin.**

        ---

        ### 🏦 1. L'Architecture des 2 Moteurs (Capital : 15 000 $)
        * **Moteur 1 : Le Socle Spot (10 000 $)**
          * **Rôle :** Générer un rendement passif régulier (~4.5% APR).
          * **Objectif :** Servir de ceinture de sécurité et faire fructifier le capital de base en continu.
        * **Moteur 2 : Le Moteur Trading (5 000 $)**
          * **Rôle :** Capter les mouvements explosifs sur les plus belles actions américaines grâce aux **Splits d'actions**.
          * **Gestion des Lignes :** Maximum 3 lignes simultanées de **750 $** par opération.

        ---

        ### 🎯 2. La Méthode "Split + POC"
        Lorsqu'une grande entreprise annonce un **Split d'actions** (ex: division du prix par 10), cela attire un énorme flux d'acheteurs.

        1. **Période d'observation (15 jours) :** Après le split, nous observons le marché pendant 15 jours sans rien toucher pour laisser le cours se stabiliser.
        2. **Le POC (Point of Control) :** L'algorithme calcule le niveau de prix exact où le plus grand volume d'achats s'est échangé durant ces 15 jours. C'est notre **prix d'achat idéal**.

        ---

        ### 🚥 3. Le Filtre Feu Tricolore (Règle Anti-FOMO)
        Le samedi matin, l'application compare le cours de clôture du vendredi avec le POC :

        * 🟢 **FEU VERT (Prix Idéal) :** Le cours est proche du POC (entre 0% et +5%). L'achat est autorisé.
        * 🟠 **FEU ORANGE (Zone d'Attente) :** Le cours a grimpé (+5% à +15% au-dessus du POC). **Ordre Limite OBLIGATOIRE sur le POC**. On ne court pas après le prix !
        * 🔴 **FEU ROUGE (Trop Cher) :** Le prix est à plus de +15% du POC. **Ligne rejetée**, on ne touche à rien.

        ---

        ### 🛡️ 4. Plan de Traitement & Sortie des 3 Ordres
        Pour chaque ligne de 750 $, l'achat est immédiatement fractionné en **3 ordres identiques** sur Quantfury :

        * **Stop-Loss Initial :** Fixé strictement à **-6% du POC** dès l'entrée sur les 3 ordres.
        * **Ordre 1 (TP1) :** 40% des titres. Vente automatique à **POC x 1.50** (+50% de gain).
        * **Ordre 2 (TP2) :** 40% des titres. Dès que TP1 est vendu, le Stop-Loss des lignes restantes est monté à **+8% (Sécurisation)**. Vente automatique à **POC x 2.05** (+105% de gain).
        * **Ordre 3 (Moonbag) :** 20% des titres. Pas de TP fixe ! On laisse courir avec un **Trailing Stop** ajusté chaque weekend.

        ---

        ### ☕ 5. La Routine du Samedi
        1. Ouvrir l'application Companion.
        2. Cliquer sur **Lancer le scan**.
        3. **Rien à l'horizon ?** On ferme l'application et on va boire son café !
        4. **Un split prêt ?** On copie la fiche synthétique et on saisit les 3 ordres sur Quantfury.
        """)
        
        if st.button("⬆️ Masquer / Réduire le Guide", key="close_guide_bottom"):
            st.session_state.show_guide = False
            st.rerun()
            
        st.markdown("---")

# Chargement de la liste Quantfury
@st.cache_data
def load_quantfury_list():
    try:
        df = pd.read_csv("Liste_quantfury.csv")
        return df['Ticker'].dropna().str.strip().unique().tolist()
    except Exception:
        return []

quantfury_tickers = load_quantfury_list()

# Récupération du cours et calcul du POC
def get_market_data(ticker_symbol, days=15, bins=30):
    try:
        tk = yf.Ticker(ticker_symbol)
        hist = tk.history(period="3mo", interval="1d")
        if hist.empty:
            return None, None
        
        close_friday = round(float(hist['Close'].iloc[-1]), 2)
        
        data = hist.tail(days)
        prices = (data['High'] + data['Low'] + data['Close']) / 3
        volumes = data['Volume']
        
        counts, bin_edges = np.histogram(prices, bins=bins, weights=volumes)
        max_idx = np.argmax(counts)
        poc_price = round(float((bin_edges[max_idx] + bin_edges[max_idx+1]) / 2), 2)
        
        return close_friday, poc_price
    except Exception:
        return None, None

tab1, tab2 = st.tabs(["🔎 Scanner des Candidates Split", "📐 Calculateur POC & Feu Tricolore"])

# --- ONGLET 1 : SCANNER DES SPLITS ---
with tab1:
    st.markdown("### 📡 Détection des Splits Récoltés sur Quantfury")
    st.write("Analyse automatique de votre liste pour identifier les opportunités de split.")
    
    if st.button("🚀 Lancer le scan des tickers Quantfury"):
        if not quantfury_tickers:
            st.error("Fichier 'Liste_quantfury.csv' introuvable sur GitHub.")
        else:
            detected_splits = []
            progress_bar = st.progress(0)
            
            for i, ticker_code in enumerate(quantfury_tickers[:50]):
                try:
                    tk = yf.Ticker(ticker_code)
                    splits = tk.splits
                    if not splits.empty:
                        last_split_date = splits.index[-1].tz_localize(None)
                        days_since = (datetime.now() - last_split_date).days
                        
                        if 0 <= days_since <= 60:
                            ratio = splits.iloc[-1]
                            status = "🎯 Prêt (Post 15 jours)" if days_since >= 15 else f"⏳ En observation ({days_since}/15j)"
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
                st.info("Aucun candidat split récent dans l'échantillon scanné. Utilisez le calculateur ci-dessous pour analyser un titre (ex: MNST).")

# --- ONGLET 2 : CALCULATEUR & FEU TRICOLORE ---
with tab2:
    st.sidebar.header("⚙️ Configuration Ligne")
    capital_ligne = st.sidebar.number_input("Capital par ligne ($)", min_value=100, max_value=5000, value=750, step=50)

    selected_ticker = st.text_input("Entrez le Ticker à analyser (ex: MNST, NVDA) :", value="MNST").strip().upper()

    if selected_ticker:
        is_in_qf = selected_ticker in quantfury_tickers if quantfury_tickers else True
        
        if quantfury_tickers and not is_in_qf:
            st.error(f"⚠️ **{selected_ticker}** N'EST PAS disponible dans la liste Quantfury.")
        else:
            if quantfury_tickers:
                st.success(f"✅ **{selected_ticker}** est validé et tradable sur Quantfury !")
            
            with st.spinner(f"Analyse du cours et du POC pour {selected_ticker}..."):
                close_price, auto_poc = get_market_data(selected_ticker, days=15)
            
            if close_price and auto_poc:
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Cours Clôture Vendredi", f"{close_price} $")
                col_m2.metric("POC Calculé (15j)", f"{auto_poc} $")
                
                ecart_pct = round(((close_price - auto_poc) / auto_poc) * 100, 2)
                col_m3.metric("Écart / POC", f"{'+' if ecart_pct > 0 else ''}{ecart_pct} %")
                
                st.markdown("#### 🚥 Signal d'Achetabilité")
                
                if ecart_pct <= 5.0:
                    st.success(f"🟢 **FEU VERT (OK - Bon prix)** : Le cours ({close_price} $) est idéalement positionné proche du POC ({auto_poc} $). Exécution autorisée.")
                    can_trade = True
                elif 5.0 < ecart_pct <= 15.0:
                    st.warning(f"🟠 **FEU ORANGE (+{ecart_pct}% du POC)** : Le titre a grimpé. Placement d'ordres limites OBLIGATOIRE sur le POC ({auto_poc} $). Ne pas acheter au marché !")
                    can_trade = True
                else:
                    st.error(f"🔴 **FEU ROUGE (Trop cher : +{ecart_pct}% du POC)** : Écart supérieur à +15%. Le titre est sur-étendu. **Ligne rejetée**, attendre un retracement.")
                    can_trade = False
                
                poc_prix = auto_poc
            else:
                st.info("Données en direct indisponibles, saisie manuelle :")
                close_price = st.number_input("Cours Clôture ($)", value=50.0)
                poc_prix = st.number_input("POC ($)", value=48.0)
                can_trade = True

            if can_trade and poc_prix > 0:
                st.markdown("---")
                st.markdown(f"### 📋 Fiche d'exécution Quantfury pour {selected_ticker}")
                
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
                    st.write(f"**Achat (Limite):** {poc_prix} $")
                    st.write(f"**SL (-6%):** {sl_initial} $")
                    st.write(f"**TP1 (x1.5):** {tp1_prix} $")
                    
                with col2:
                    st.metric("Ordre 2 (TP2)", f"{qte_tp2} titres")
                    st.write(f"**Achat (Limite):** {poc_prix} $")
                    st.write(f"**SL (-6%):** {sl_initial} $")
                    st.write(f"**TP2 (x2.05):** {tp2_prix} $")
                    
                with col3:
                    st.metric("Ordre 3 (Moonbag)", f"{qte_moonbag} titres")
                    st.write(f"**Achat (Limite):** {poc_prix} $")
                    st.write(f"**SL (-6%):** {sl_initial} $")
                    st.write("**TP:** Trailing Stop")
                
                st.markdown("---")
                
                fiche_text = f"""--- FICHE D'EXÉCUTION QUANTFURY ({selected_ticker}) ---
Achat total: {nb_titres} titres @ {poc_prix} $ ({engagement} $)

1. ORDRE TP1: {qte_tp1} titres | Achat: {poc_prix} $ | SL: {sl_initial} $ | TP1: {tp1_prix} $
2. ORDRE TP2: {qte_tp2} titres | Achat: {poc_prix} $ | SL: {sl_initial} $ | TP2: {tp2_prix} $
3. MOONBAG:   {qte_moonbag} titres | Achat: {poc_prix} $ | SL: {sl_initial} $ | TP: Trailing Stop
--------------------------------------------------"""
                st.text_area("📋 Fiche synthétique (à copier ou capturer) :", fiche_text, height=140)
