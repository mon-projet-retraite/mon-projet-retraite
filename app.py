import streamlit as st

st.set_page_config(page_title="Companion Quantfury", layout="centered")

st.title("🛡️ Companion Retraite & Autonomie")
st.subheader("Méthode Split + POC (Modèle Double Moteur)")

# Paramètres utilisateur
st.sidebar.header("⚙️ Configuration Ligne")
capital_ligne = st.sidebar.number_input("Capital par ligne ($)", min_value=100, max_value=2000, value=816, step=50)

st.markdown("---")
st.markdown("### 📋 Fiche d'exécution pour vos 3 Ordres")

poc_prix = st.number_input("Prix Achat / POC ($)", min_value=1.0, value=50.0, step=0.5)

if poc_prix > 0:
    nb_titres = int(capital_ligne // poc_prix)
    qte_tp1 = int(nb_titres * 0.40)
    qte_tp2 = int(nb_titres * 0.40)
    qte_moonbag = nb_titres - (qte_tp1 + qte_tp2)
    
    sl_initial = round(poc_prix * 0.94, 2)
    tp1_prix = round(poc_prix * 1.50, 2)
    tp2_prix = round(poc_prix * 2.05, 2)
    
    st.write(f"**Nombre total de titres :** {nb_titres} (Engagement : {round(nb_titres * poc_prix, 2)} $)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ordre 1 (TP1)", f"{qte_tp1} titres")
        st.write(f"Achat: {poc_prix} $")
        st.write(f"SL (-6%): {sl_initial} $")
        st.write(f"TP1 (x1.5): {tp1_prix} $")
        
    with col2:
        st.metric("Ordre 2 (TP2)", f"{qte_tp2} titres")
        st.write(f"Achat: {poc_prix} $")
        st.write(f"SL (-6%): {sl_initial} $")
        st.write(f"TP2 (x2.05): {tp2_prix} $")
        
    with col3:
        st.metric("Ordre 3 (Moonbag)", f"{qte_moonbag} titres")
        st.write(f"Achat: {poc_prix} $")
        st.write(f"SL (-6%): {sl_initial} $")
        st.write("TP: Trailing Stop")
