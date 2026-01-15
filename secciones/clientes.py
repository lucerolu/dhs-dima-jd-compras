# secciones/clientes.py

import streamlit as st
from utils.api_utils import obtener_vista


def mostrar(config):
    st.title("👥 Clientes / Ubicación")

    st.markdown(
        """
        Análisis de clientes por:
        - Ubicación
        - Frecuencia
        - Comportamiento mensual
        """
    )

    # Vista base (placeholder)
    df = obtener_vista("vw_dashboard_ubicacion_clientes")

    if df.empty:
        st.warning("No hay datos disponibles de clientes.")
        return

    st.subheader("Clientes por ubicación")
    st.dataframe(df, use_container_width=True)

    # VISTAS DISPONIBLES (para usar después)
    # - vw_dashboard_ubicacion_clientes_mes
    # - vw_dhs_ubi_clientes_espec
