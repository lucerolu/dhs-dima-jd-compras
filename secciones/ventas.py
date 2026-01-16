# secciones/ventas.py

import streamlit as st
import pandas as pd
import altair as alt

from utils.api_utils import obtener_vista
from utils.table_utils import mostrar_tabla_normal
from utils.table_utils import mostrar_tabla_matriz


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
    df_meta = obtener_vista("vw_dashboard_meta_sucursal")

    if df.empty:
        st.warning("No hay datos disponibles para ventas.")
        return

    if df_meta.empty:
        st.warning("No hay datos de metas disponibles.")
        return

    df["venta_real"] = pd.to_numeric(df["venta_real"], errors="coerce").fillna(0)
    
    # --------------------------------------------------
    # AÑO FISCAL ACTUAL
    # --------------------------------------------------
    anio_fiscal_actual = df["anio_fiscal_jd"].max()
    df_fiscal = df[df["anio_fiscal_jd"] == anio_fiscal_actual]
    
    
    df_meta_fiscal = df_meta[df_meta["anio_fiscal_jd"] == anio_fiscal_actual].copy()
    df_meta_fiscal["venta_real"] = pd.to_numeric(df_meta_fiscal["venta_real"], errors="coerce").fillna(0)
    df_meta_fiscal["meta"] = pd.to_numeric(df_meta_fiscal["meta"], errors="coerce").fillna(0)


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

    meta_mensual = (
        df_meta_fiscal
        .groupby("periodo_jd", as_index=False)
        .agg({
            "venta_real": "sum",
            "meta": "sum"
        })
    )

    meta_mensual["cumplimiento_meta_pct"] = (
        meta_mensual["venta_real"] / meta_mensual["meta"] * 100
    ).where(meta_mensual["meta"] > 0)



    mensual = mensual.merge(
        meta_mensual[[
            "periodo_jd",
            "meta",
            "cumplimiento_meta_pct"
        ]],
        on="periodo_jd",
        how="left"
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
    # Gráfico de tabla y meta 
    # --------------------------------------------------

    st.subheader("📈 Venta vs Meta por mes (Año fiscal JD)")

    grafica_df = mensual[[
        "periodo_jd",
        "venta_real",
        "meta",
        "cumplimiento_meta_pct"
    ]].dropna(subset=["meta"])


    grafica_long = grafica_df.melt(
        id_vars=["periodo_jd", "cumplimiento_meta_pct"],
        value_vars=["venta_real", "meta"],
        var_name="Tipo",
        value_name="Monto"
    )

    grafica_long["Tipo"] = grafica_long["Tipo"].map({
        "venta_real": "Venta real",
        "meta": "Meta"
    })

    chart = (
        alt.Chart(grafica_long)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "periodo_jd:N",
                title="Periodo",
                sort=list(mensual["periodo_jd"]),
                axis=alt.Axis(labelAngle=0)
            ),
            y=alt.Y(
                "Monto:Q",
                title="Monto ($)"
            ),
            color=alt.Color(
                "Tipo:N",
                legend=alt.Legend(title="")
            ),
            tooltip=[
                alt.Tooltip("periodo_jd:N", title="Periodo"),
                alt.Tooltip("Tipo:N", title="Tipo"),
                alt.Tooltip("Monto:Q", title="Monto", format=",.2f"),
                alt.Tooltip(
                    "cumplimiento_meta_pct:Q",
                    title="% Cumplimiento",
                    format=".2f"
                )
            ]
        )
        .properties(height=420)
    )

    st.altair_chart(chart, use_container_width=True)


    # --------------------------------------------------
    # TABLA MES A MES
    # --------------------------------------------------
    mensual["% Variación"] = mensual["venta_real"].pct_change() * 100

    tabla = mensual[[
        "periodo_jd",
        "venta_real",
        "% Variación",
        "cumplimiento_meta_pct"
    ]].rename(columns={
        "periodo_jd": "Periodo",
        "venta_real": "Venta",
        "cumplimiento_meta_pct": "% Cumplimiento Meta"
    })

    st.subheader("📊 Ventas mes a mes (Año fiscal JD)")

    mostrar_tabla_normal(
        df=tabla,
        columnas_fijas=["Periodo"],
        columnas_numericas=[
            "Venta",
            "% Variación",
            "% Cumplimiento Meta"
        ],
        height=480
    )

    # --------------------------------------------------
    # VENTA POR SUCURSAL VS META (MES A MES)
    # --------------------------------------------------

    st.subheader("🏬 Venta por sucursal vs meta (Año fiscal JD)")

    sucursales = sorted(df_meta_fiscal["sucursal"].dropna().unique())
    sucursal_sel = st.selectbox(
        "Selecciona una sucursal",
        sucursales,
        key="sucursal_venta_meta"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    df_sucursal = df_meta_fiscal[
        df_meta_fiscal["sucursal"] == sucursal_sel
    ]

    mensual_sucursal = (
        df_sucursal
        .groupby(
            ["periodo_jd", "orden_mes_fiscal"],
            as_index=False
        )
        .agg({
            "venta_real": "sum",
            "meta": "sum"
        })
        .sort_values("orden_mes_fiscal")
    )

    mensual_sucursal["cumplimiento_meta_pct"] = (
        mensual_sucursal["venta_real"]
        / mensual_sucursal["meta"].replace(0, None)
        * 100
    )

    grafica_long = mensual_sucursal.melt(
        id_vars=["periodo_jd", "cumplimiento_meta_pct"],
        value_vars=["venta_real", "meta"],
        var_name="Tipo",
        value_name="Monto"
    )

    grafica_long["Tipo"] = grafica_long["Tipo"].map({
        "venta_real": "Venta real",
        "meta": "Meta"
    })

    chart = (
        alt.Chart(grafica_long)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "periodo_jd:N",
                sort=list(mensual_sucursal["periodo_jd"]),
                axis=alt.Axis(labelAngle=0),
                title="Periodo"
            ),
            y=alt.Y(
                "Monto:Q",
                title="Monto ($)"
            ),
            color=alt.Color(
                "Tipo:N",
                legend=alt.Legend(title="")
            ),
            tooltip=[
                alt.Tooltip("periodo_jd:N", title="Periodo"),
                alt.Tooltip("Tipo:N", title="Tipo"),
                alt.Tooltip("Monto:Q", title="Monto", format=",.2f"),
                alt.Tooltip("% Cumplimiento Meta:Q", title="% Cumplimiento", format=".2f")
            ]
        )
        .properties(height=420)
    )

    st.altair_chart(chart, use_container_width=True)

    st.subheader("📋 Detalle mensual de venta vs meta")

    tabla_mensual = mensual_sucursal[[
        "periodo_jd",
        "venta_real",
        "meta",
        "cumplimiento_meta_pct"
    ]].rename(columns={
        "periodo_jd": "Periodo",
        "venta_real": "Venta",
        "meta": "Meta",
        "cumplimiento_meta_pct": "% Cumplimiento"
    })

    st.dataframe(
        tabla_mensual,
        use_container_width=True,
        hide_index=True
    )

    
    # --------------------------------------------------
    # MATRIZ DE VENTAS POR SUCURSAL Y MES
    # --------------------------------------------------

    st.subheader("📊 Venta mensual por sucursal (Año fiscal JD)")

    ventas_sucursal_mes = (
        df_fiscal
        .groupby(
            ["orden_mes_fiscal", "periodo_jd", "sucursal"],
            as_index=False
        )
        .agg({"venta_real": "sum"})
    )

    matriz = (
        ventas_sucursal_mes
        .pivot(
            index=["orden_mes_fiscal", "periodo_jd"],
            columns="sucursal",
            values="venta_real"
        )
        .fillna(0)
        .reset_index()
        .sort_values("orden_mes_fiscal")
    )

    matriz = matriz.drop(columns=["orden_mes_fiscal"])

    header_left = ["periodo_jd"]
    data_columns = [c for c in matriz.columns if c != "periodo_jd"]

    footer_totals = {
        "periodo_jd": "TOTAL",
        **{col: matriz[col].sum() for col in data_columns}
    }

    # columnas de sucursales
    data_columns = [c for c in matriz.columns if c != "periodo_jd"]

    # TOTAL por fila
    matriz["Total"] = matriz[data_columns].sum(axis=1)

    # TOTAL por columna (footer)
    footer_totals = {
        "periodo_jd": "TOTAL",
        **{col: matriz[col].sum() for col in data_columns},
        "Total": matriz["Total"].sum()
    }

    mostrar_tabla_matriz(
        df=matriz,
        header_left=["periodo_jd"],
        data_columns=data_columns,
        header_right=["Total"],
        footer_totals=footer_totals,
        max_height=520
    )











