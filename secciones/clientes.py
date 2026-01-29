# secciones/clientes.py

import streamlit as st
import plotly.express as px
import pandas as pd
from utils.api_utils import obtener_vista


# ======================================================
# 1️⃣ CARGA BASE (API → DF) | cache 24h
# ======================================================
@st.cache_data(ttl=86400)
def cargar_clientes_base():
    df = obtener_vista("vw_dashboard_ubicacion_clientes_mes")
    if df.empty:
        raise ValueError("Vista clientes vacía, no se cachea")
    return df


# ======================================================
# 2️⃣ LIMPIEZA PESADA | cache 24h
# ======================================================
@st.cache_data(ttl=86400)
def preparar_clientes_limpio(df_base: pd.DataFrame) -> pd.DataFrame:
    df = df_base.copy()

    # Validación geográfica
    df = df[
        (df["cliente_latitud"].between(-90, 90)) &
        (df["cliente_longitud"].between(-180, 180)) &
        (df["cliente_latitud"] != 0) &
        (df["cliente_longitud"] != 0)
    ]

    # Redondeo para estabilidad del mapa
    df["cliente_latitud"] = df["cliente_latitud"].round(5)
    df["cliente_longitud"] = df["cliente_longitud"].round(5)

    return df


# ======================================================
# 3️⃣ FILTRO + AGRUPACIÓN (rápido, sin cache)
# ======================================================
def obtener_datos_mapa_clientes(df_limpio, anio_seleccionado, mes_seleccionado):

    df = df_limpio[df_limpio["anio"] == anio_seleccionado]

    if mes_seleccionado != "Todos":
        df = df[df["mes_nombre"] == mes_seleccionado]

    df_clientes = df.groupby(
        ["Estado", "Ciudad", "cliente_latitud", "cliente_longitud"],
        as_index=False
    ).agg({
        "clientes_unicos": "sum",
        "venta_total": "sum",
        "facturas": "sum"
    })

    return df_clientes


# ======================================================
# SELECTORES
# ======================================================
def selector_periodo(df):
    st.markdown("### Filtros de periodo")
    anios = sorted(df["anio"].dropna().unique().tolist(), reverse=True)
    anio_sel = st.selectbox("Año", anios, index=0)

    df_anio = df[df["anio"] == anio_sel]
    meses = ["Todos"] + sorted(df_anio["mes_nombre"].dropna().unique().tolist())
    mes_sel = st.selectbox("Mes", meses, index=0)

    return anio_sel, mes_sel


# ======================================================
# MAPA
# ======================================================
def mapa_facturacion_clientes(df_clientes):
    if df_clientes.empty:
        st.warning("No hay datos para mostrar en las coordenadas seleccionadas.")
        return

    df_clientes = df_clientes[df_clientes["venta_total"] > 0]

    fig = px.scatter_mapbox(
        df_clientes,
        lat="cliente_latitud",
        lon="cliente_longitud",
        size=df_clientes["venta_total"].clip(upper=500000),
        color="venta_total",
        color_continuous_scale=px.colors.sequential.Plasma,
        zoom=4,
        hover_name="Ciudad"
    )

    fig.update_traces(
        marker=dict(opacity=0.8),
        customdata=df_clientes[
            ["Estado", "venta_total", "clientes_unicos", "facturas",
             "cliente_latitud", "cliente_longitud"]
        ],
        hovertemplate=(
            "<b>📍 %{hovertext}</b><br>"
            "%{customdata[0]}<br><br>"
            "<b>Venta:</b> $%{customdata[1]:,.2f}<br>"
            "<b>Clientes:</b> %{customdata[2]}<br>"
            "<b>Facturas:</b> %{customdata[3]}<br><br>"
            "<b>Lat:</b> %{customdata[4]:.4f}<br>"
            "<b>Lon:</b> %{customdata[5]:.4f}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        margin=dict(r=0, t=0, l=0, b=0),
        coloraxis_colorbar=dict(title="Venta Total")
    )

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})


# ======================================================
# MAIN
# ======================================================
def mostrar(config):

    st.title("Clientes / Ubicación")
    st.markdown("***** En producción *********")

    # 🔥 WARM-UP (solo una vez por sesión)
    if "warmup_clientes" not in st.session_state:
        df_base = cargar_clientes_base()
        preparar_clientes_limpio(df_base)
        st.session_state["warmup_clientes"] = True

    # Uso normal
    df_base = cargar_clientes_base()
    df_limpio = preparar_clientes_limpio(df_base)

    anio_sel, mes_sel = selector_periodo(df_limpio)

    df_clientes = obtener_datos_mapa_clientes(
        df_limpio, anio_sel, mes_sel
    )

    st.subheader(
        f"Distribución de ventas por domicilio fiscal - {mes_sel} {anio_sel}"
    )

    mapa_facturacion_clientes(df_clientes)
