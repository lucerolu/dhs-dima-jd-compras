# secciones/vendedores.py

import streamlit as st
from utils.api_utils import obtener_vista
from utils.table_utils import mostrar_tabla_normal
import pandas as pd
import altair as alt

def mostrar(config):
    st.title("Vendedores")
    st.markdown("Análisis de rendimiento de vendedores")

    # -----------------------------
    # Obtener datos
    # -----------------------------
    df = obtener_vista("vw_dashboard_meta_vendedor_jd")

    if df.empty:
        st.warning("No hay datos disponibles de vendedores")
        return

    # -----------------------------
    # FILTRAR POR AÑO (solo 2026)
    # -----------------------------
    df = df[df["anio"] == 2026]

    # -----------------------------
    # Selector de sucursal
    # -----------------------------
    sucursales = df["sucursal"].sort_values().unique().tolist()
    sucursales.insert(0, "Todos")  # opción para mostrar todas
    sucursal_seleccionada = st.selectbox("Selecciona sucursal:", sucursales, index=0)
    if sucursal_seleccionada != "Todos":
        df = df[df["sucursal"] == sucursal_seleccionada]

    # -----------------------------
    # Selector de mes (periodo_jd)
    # -----------------------------
    meses_disponibles = df["periodo_jd"].sort_values().unique().tolist()
    mes_seleccionado = st.selectbox("Selecciona mes:", meses_disponibles, index=0)
    df = df[df["periodo_jd"] == mes_seleccionado]

    # -----------------------------
    # Agrupar por vendedor (sumar ventas y costos)
    # -----------------------------
    df_vendedor = df.groupby("vendedor", as_index=False).agg({
        "meta_vendedor": "first",  # tomar una sola meta
        "venta_real": "sum",
        "costo_real": "sum",
        "utilidad_real": "sum",
        "margen_real": "mean",  # promedio del margen si hay varios registros
        "porcentaje_cumplimiento": "mean",  # promedio del %cumplimiento
        "semaforo": "max"  # tomar el peor semáforo si hay varios
    })

    # -----------------------------
    # Gráfico de cumplimiento por vendedor
    # -----------------------------
    df_grafico_con_meta = df_vendedor[df_vendedor["meta_vendedor"].notnull()].copy()
    df_grafico_sin_meta = df_vendedor[df_vendedor["meta_vendedor"].isnull()].copy()

    # Ordenar por meta descendente y luego agregar los que no tienen meta
    df_grafico_con_meta = df_grafico_con_meta.sort_values("meta_vendedor", ascending=False)
    df_grafico = pd.concat([df_grafico_con_meta, df_grafico_sin_meta], ignore_index=True)

    # Colores según semáforo
    color_scale = alt.Scale(
        domain=["ROJO", "AMARILLO", "VERDE"],
        range=["#DC3545", "#FFC107", "#1E7E34"]
    )

    # Barra de meta (fondo gris) solo para los que tienen meta
    meta_bar = (
        alt.Chart(df_grafico[df_grafico["meta_vendedor"].notnull()])
        .mark_bar(color="#E0E0E0", opacity=0.9, size=26)
        .encode(
            y=alt.Y(
                "vendedor:N",
                sort=list(df_grafico["vendedor"]),
                title=""
            ),
            x=alt.X(
                "meta_vendedor:Q",
                title="Monto ($)"
            ),
            tooltip=[
                alt.Tooltip("vendedor:N", title="Vendedor"),
                alt.Tooltip("meta_vendedor:Q", title="Meta", format=",.2f")
            ]
        )
    )

    # Barra de ventas (cumplimiento) para todos los vendedores
    venta_bar = (
        alt.Chart(df_grafico)
        .mark_bar(size=18)
        .encode(
            y=alt.Y(
                "vendedor:N",
                sort=list(df_grafico["vendedor"])
            ),
            x=alt.X(
                "venta_real:Q"
            ),
            color=alt.condition(
                'datum.meta_vendedor != null',
                alt.Color("semaforo:N", scale=color_scale, legend=None),
                alt.value("#1f77b4")
            ),
            tooltip=[
                alt.Tooltip("vendedor:N", title="Vendedor"),
                alt.Tooltip("venta_real:Q", title="Venta real", format=",.2f"),
                alt.Tooltip("porcentaje_cumplimiento:Q", title="Cumplimiento (%)", format=".2f")
            ]
        )
    )


    chart = (meta_bar + venta_bar).properties(
        height=max(320, len(df_grafico) * 38),
        width=700
    )

    st.subheader(f"Cumplimiento de meta por vendedor – {mes_seleccionado}")
    st.altair_chart(chart, use_container_width=True)

    # -----------------------------
    # Preparar tabla agregada por vendedor (sin sucursal)
    # -----------------------------
    df_tabla = df_vendedor.copy()
    df_tabla.rename(columns={
        "meta_vendedor": "Meta",
        "venta_real": "Venta",
        "costo_real": "Costo",
        "utilidad_real": "Utilidad",
        "margen_real": "Margen",
        "porcentaje_cumplimiento": "% Cumplimiento",
        "semaforo": "Semáforo"
    }, inplace=True)

    columnas_numericas = ["Meta", "Venta", "Costo", "Utilidad", "Margen", "% Cumplimiento"]
    columnas_fijas = ["vendedor"]

    mostrar_tabla_normal(
        df_tabla,
        columnas_fijas=columnas_fijas,
        columnas_numericas=columnas_numericas,
        resaltar_primera_columna=True,
        height=600
    )
