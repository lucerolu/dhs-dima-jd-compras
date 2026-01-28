# secciones/vendedores.py

import streamlit as st
import pandas as pd
import altair as alt

from utils.api_utils import obtener_vista
from utils.table_utils import mostrar_tabla_normal


# =========================================================
# CARGA CONTROLADA DE DATOS (1 sola vez por sesión)
# =========================================================
def cargar_datos_vendedores():
    # USAMOS UN TRY/EXCEPT AQUÍ TAMBIÉN
    if "df_vendedores_raw" not in st.session_state or st.session_state.df_vendedores_raw is None:
        try:
            with st.spinner("Obteniendo datos..."):
                df = obtener_vista("vw_dashboard_meta_vendedor_jd")
                
                if df is not None and not df.empty:
                    st.session_state.df_vendedores_raw = df
                else:
                    return None
        except Exception:
            return None
            
    return st.session_state.df_vendedores_raw


# =========================================================
# SECCIÓN PRINCIPAL
# =========================================================
def mostrar(config):
    st.title("Vendedores")
    st.markdown("Análisis de rendimiento de vendedores")

    # -----------------------------
    # Cargar datos base
    # -----------------------------
    df_raw = cargar_datos_vendedores()

    if df_raw is None or df_raw.empty:
        st.warning("No hay datos disponibles de vendedores")
        st.stop()

    # -----------------------------
    # FILTRO FIJO: AÑO
    # -----------------------------
    df_base = df_raw[df_raw["anio"] == 2026].copy()

    if df_base.empty:
        st.info("No hay datos para el año seleccionado")
        st.stop()

    # =====================================================
    # FILTROS UI
    # =====================================================
    col1, col2 = st.columns(2)

    with col1:
        sucursales = sorted(df_base["sucursal"].dropna().unique().tolist())
        sucursales.insert(0, "Todos")
        sucursal_sel = st.selectbox(
            "Selecciona sucursal",
            sucursales,
            index=0,
            key="vendedores_sucursal"
        )

    # Filtrado intermedio para que el mes SIEMPRE tenga datos de la sucursal elegida
    df_temp_sucursal = df_base.copy()
    if sucursal_sel != "Todos":
        df_temp_sucursal = df_temp_sucursal[df_temp_sucursal["sucursal"] == sucursal_sel]

    with col2:
        # Extraemos los meses que SÍ existen para la sucursal seleccionada
        meses_disponibles = sorted(df_temp_sucursal["periodo_jd"].dropna().unique().tolist())
        
        # Si no hay meses (caso raro), evitamos que truene el selectbox
        if not meses_disponibles:
            st.warning("No hay meses con datos para esta sucursal.")
            st.stop()

        mes_sel = st.selectbox(
            "Selecciona mes",
            meses_disponibles,
            index=0,
            key="vendedores_mes"
        )

    # -----------------------------
    # Aplicar filtro final
    # -----------------------------
    # Usamos el df_temp_sucursal que ya tiene el filtro de sucursal
    df = df_temp_sucursal[df_temp_sucursal["periodo_jd"] == mes_sel].copy()

    # IMPORTANTE: No usamos st.stop() aquí si es posible, 
    # para que Streamlit no "olvide" dibujar el resto de la página
    if df.empty:
        st.info(f"No se encontraron datos para {sucursal_sel} en {mes_sel}")
        return # Usamos return en lugar de stop para salir de la función limpiamente

    # =====================================================
    # AGRUPACIÓN POR VENDEDOR
    # =====================================================
    df_vendedor = (
        df.groupby("vendedor", as_index=False)
        .agg({
            "meta_vendedor": "first",
            "venta_real": "sum",
            "costo_real": "sum",
            "utilidad_real": "sum",
            "margen_real": "mean",
            "porcentaje_cumplimiento": "mean",
            "semaforo": "max",
        })
    )

    if df_vendedor.empty:
        st.info("No hay datos agregados para mostrar")
        st.stop()

    # =====================================================
    # GRÁFICO
    # =====================================================
    df_con_meta = df_vendedor[df_vendedor["meta_vendedor"].notna()]
    df_sin_meta = df_vendedor[df_vendedor["meta_vendedor"].isna()]

    df_con_meta = df_con_meta.sort_values("meta_vendedor", ascending=False)
    df_grafico = pd.concat([df_con_meta, df_sin_meta], ignore_index=True)

    color_scale = alt.Scale(
        domain=["ROJO", "AMARILLO", "VERDE"],
        range=["#DC3545", "#FFC107", "#1E7E34"]
    )

    meta_bar = (
        alt.Chart(df_grafico[df_grafico["meta_vendedor"].notna()])
        .mark_bar(color="#E0E0E0", size=26)
        .encode(
            y=alt.Y("vendedor:N", sort=list(df_grafico["vendedor"]), title=""),
            x=alt.X("meta_vendedor:Q", title="Monto ($)"),
            tooltip=[
                alt.Tooltip("vendedor:N", title="Vendedor"),
                alt.Tooltip("meta_vendedor:Q", title="Meta", format=",.2f"),
            ],
        )
    )

    venta_bar = (
        alt.Chart(df_grafico)
        .mark_bar(size=18)
        .encode(
            y=alt.Y("vendedor:N", sort=list(df_grafico["vendedor"])),
            x=alt.X("venta_real:Q"),
            color=alt.condition(
                "datum.meta_vendedor != null",
                alt.Color("semaforo:N", scale=color_scale, legend=None),
                alt.value("#1f77b4"),
            ),
            tooltip=[
                alt.Tooltip("vendedor:N", title="Vendedor"),
                alt.Tooltip("venta_real:Q", title="Venta real", format=",.2f"),
                alt.Tooltip("porcentaje_cumplimiento:Q", title="Cumplimiento (%)", format=".2f"),
            ],
        )
    )

    chart = (meta_bar + venta_bar).properties(
        height=max(320, len(df_grafico) * 38)
    )

    st.subheader(f"Cumplimiento de meta por vendedor – {mes_sel}")
    st.altair_chart(chart, use_container_width=True)

    # =====================================================
    # TABLA
    # =====================================================
    df_tabla = df_vendedor.rename(columns={
        "meta_vendedor": "Meta",
        "venta_real": "Venta",
        "costo_real": "Costo",
        "utilidad_real": "Utilidad",
        "margen_real": "Margen",
        "porcentaje_cumplimiento": "% Cumplimiento",
        "semaforo": "Semáforo",
    })

    tabla_key = f"espacio_tabla_{sucursal_sel}_{mes_sel}"

    # Creamos un hueco vacío
    placeholder = st.empty()

    # Dibujamos la tabla dentro de ese hueco
    with placeholder.container():
        mostrar_tabla_normal(
            df_tabla,
            columnas_fijas=["vendedor"],
            columnas_numericas=[
                "Meta", "Venta", "Costo", "Utilidad", "Margen", "% Cumplimiento"
            ],
            resaltar_primera_columna=True,
            height=800,
        )

