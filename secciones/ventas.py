# secciones/ventas.py

import streamlit as st
import pandas as pd
from utils.api_utils import obtener_vista


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

    # Asegurar tipos
    df["venta_real"] = pd.to_numeric(df["venta_real"], errors="coerce").fillna(0)

    # --------------------------------------------------
    # AÑO FISCAL ACTUAL (el más reciente disponible)
    # --------------------------------------------------
    anio_fiscal_actual = df["anio_fiscal_jd"].max()

    df_fiscal = df[df["anio_fiscal_jd"] == anio_fiscal_actual]

    # --------------------------------------------------
    # AGRUPACIÓN MENSUAL (todas las sucursales)
    # --------------------------------------------------
    mensual = (
        df_fiscal
        .groupby(["anio_fiscal_jd", "mes", "mes_nombre", "periodo_jd"], as_index=False)
        .agg({"venta_real": "sum"})
        .sort_values("mes")
    )

    # --------------------------------------------------
    # KPI: Venta acumulada fiscal
    # --------------------------------------------------
    venta_acumulada = mensual["venta_real"].sum()

    # --------------------------------------------------
    # KPI: Mes actual (último con datos)
    # --------------------------------------------------
    mes_actual = mensual.iloc[-1]
    venta_mes_actual = mes_actual["venta_real"]

    # --------------------------------------------------
    # KPI: Variación vs mes anterior
    # --------------------------------------------------
    if len(mensual) > 1:
        venta_mes_anterior = mensual.iloc[-2]["venta_real"]
        variacion_pct = (
            (venta_mes_actual - venta_mes_anterior) / venta_mes_anterior * 100
            if venta_mes_anterior > 0 else 0
        )
    else:
        variacion_pct = 0

    # --------------------------------------------------
    # TARJETAS KPI
    # --------------------------------------------------
    col1, col2, col3 = st.columns(3)

    col1.metric(
        label=f"Venta acumulada FY {anio_fiscal_actual}",
        value=f"${venta_acumulada:,.2f}"
    )

    col2.metric(
        label=f"Venta mes actual ({mes_actual['periodo_jd']})",
        value=f"${venta_mes_actual:,.2f}"
    )

    col3.metric(
        label="Variación vs mes anterior",
        value=f"{variacion_pct:,.2f} %",
        delta=f"{variacion_pct:,.2f} %"
    )

    st.markdown("---")

    # --------------------------------------------------
    # TABLA MES A MES
    # --------------------------------------------------
    mensual["variacion_pct"] = mensual["venta_real"].pct_change() * 100

    # Formato para mostrar
    tabla = mensual[[
        "periodo_jd",
        "venta_real",
        "variacion_pct"
    ]].copy()

    tabla.rename(columns={
        "periodo_jd": "Periodo",
        "venta_real": "Venta",
        "variacion_pct": "% Variación vs mes anterior"
    }, inplace=True)

    # --------------------------------------------------
    # ESTILOS
    # --------------------------------------------------
    def color_variacion(val):
        if pd.isna(val):
            return ""
        elif val > 0:
            return "color: green; font-weight: bold;"
        elif val < 0:
            return "color: red; font-weight: bold;"
        return ""

    st.subheader("📊 Ventas mes a mes (Año fiscal JD)")

    st.dataframe(
        tabla.style
        .format({
            "Venta": "${:,.2f}",
            "% Variación vs mes anterior": "{:,.2f} %"
        })
        .applymap(color_variacion, subset=["% Variación vs mes anterior"]),
        use_container_width=True
    )

