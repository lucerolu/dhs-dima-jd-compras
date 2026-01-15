# secciones/ventas.py

import streamlit as st
from utils.api_utils import obtener_vista


def mostrar(config):
    st.title("📈 Ventas")

    st.markdown(
        """
        Esta sección mostrará el avance de ventas por:
        - Sucursal
        - Vendedor
        - Cliente
        """
    )

    # Vista base (placeholder)
    df = obtener_vista("vw_facturacion_sucursal_mes_jd")

    if df.empty:
        st.warning("No hay datos disponibles para ventas.")
        return

    st.subheader("Vista base: Facturación por sucursal / mes")
    st.dataframe(df, use_container_width=True)

    # VISTAS DISPONIBLES (para usar después)
    # - vw_dashboard_meta_sucursal
    # - vw_dashboard_meta_vendedor_jd
    # - vw_clientes_mensuales_venta
    # - vw_cancelaciones_clientes_detalle
    # - vw_cancelaciones_vendedor_sucursal



