# secciones/compras.py

import streamlit as st
from utils.api_utils import obtener_vista


def mostrar(config):
    st.title("🛒 Compras vs Meta")

    st.markdown(
        """
        Seguimiento de compras comparadas contra la meta establecida.
        """
    )

    # Vista base (placeholder)
    df = obtener_vista("vw_dashboard_avance_jd")

    if df.empty:
        st.warning("No hay datos disponibles de compras.")
        return

    st.subheader("Avance de compras")
    st.dataframe(df, use_container_width=True)

    # VISTAS DISPONIBLES (para usar después)
    # - vw_dashboard_meta_compras
    # - vw_dashboard_compras_mes

