# secciones/ventas.py

import streamlit as st
import pandas as pd

from utils.api_utils import obtener_vista
from utils.table_utils import mostrar_tabla_aggrid


def mostrar(config):
    st.title("📈 Ventas")

    st.markdown(
        """
        **Resumen de ventas JD**
        
        - Acumulado del año fiscal
        - Venta del mes actual
        - Comparativo mes contra mes
        """
    )

    # --------------------------------------------------
    # CARGA DE DATOS
    # --------------------------------------------------
    df = obtener_vista("vw_facturacion_sucursal_mes_jd")

    if df.empty:
        st.warning("No hay datos disponibles para ventas.")
        return

    df["venta_real"] = pd.to_numeric(df["venta_real"], errors="coerce").fillna(0)

    # --------------------------------------------------
    # AÑO FISCAL ACTUAL
    # --------------------------------------------------
    anio_fiscal_actual = df["anio_fiscal_jd"].max()
    df_fiscal = df[df["anio_fiscal_jd"] == anio_fiscal_actual]

    # --------------------------------------------------
    # AGRUPACIÓN MENSUAL (ORDEN FISCAL CORRECTO)
    # --------------------------------------------------
    mensual = (
        df_fiscal
        .groupby(
            ["anio_fiscal_jd", "orden_mes_fiscal", "periodo_jd"],
            as_index=False
        )
        .agg({"venta_real": "sum"})
        .sort_values("orden_mes_fiscal")
    )

    # --------------------------------------------------
    # KPIs
    # --------------------------------------------------
    venta_acumulada = mensual["venta_real"].sum()

    mes_actual = mensual.iloc[-1]
    venta_mes_actual = mes_actual["venta_real"]

    if len(mensual) > 1:
        venta_mes_anterior = mensual.iloc[-2]["venta_real"]
        variacion_pct = (
            (venta_mes_actual - venta_mes_anterior) / venta_mes_anterior * 100
            if venta_mes_anterior > 0 else 0
        )
    else:
        variacion_pct = 0

    col1, col2, col3 = st.columns(3)

    col1.metric(
        f"Venta acumulada FY {anio_fiscal_actual}",
        f"${venta_acumulada:,.2f}"
    )

    col2.metric(
        f"Venta mes actual ({mes_actual['periodo_jd']})",
        f"${venta_mes_actual:,.2f}"
    )

    col3.metric(
        "Variación vs mes anterior",
        f"{variacion_pct:,.2f} %",
        delta=f"{variacion_pct:,.2f} %"
    )

    st.markdown("---")

    # --------------------------------------------------
    # TABLA MES A MES
    # --------------------------------------------------
    mensual["% Variación"] = mensual["venta_real"].pct_change() * 100

    tabla = mensual[[
        "periodo_jd",
        "venta_real",
        "% Variación"
    ]].rename(columns={
        "periodo_jd": "Periodo",
        "venta_real": "Venta"
    })

    st.subheader("📊 Ventas mes a mes (Año fiscal JD)")

    mostrar_tabla_aggrid(
        df=tabla,
        columnas_fijas=["Periodo"],
        columnas_numericas=["Venta", "% Variación"],
        height=450
    )

