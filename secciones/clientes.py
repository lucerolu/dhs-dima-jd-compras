# secciones/clientes.py

import streamlit as st
import plotly.express as px
import pandas as pd
from utils.api_utils import obtener_vista


def obtener_datos_mapa_clientes(anio_seleccionado, mes_seleccionado):
    """
    Obtiene y prepara los datos para el mapa de clientes.
    """
    df = obtener_vista("vw_dashboard_ubicacion_clientes_mes")

    if df.empty:
        return df

    # ---- Filtro por año (obligatorio) ----
    df = df[df["anio"] == anio_seleccionado]

    # ---- Filtro por mes ----
    if mes_seleccionado != "Todos":
        df = df[df["mes_nombre"] == mes_seleccionado]

    else:
        # Agrupamos todos los meses del año
        df = (
            df.groupby(
                ["Estado", "Ciudad", "latitud", "longitud"],
                as_index=False
            )
            .agg(
                clientes_unicos=("clientes_unicos", "sum"),
                venta_total=("venta_total", "sum"),
                facturas=("facturas", "sum")
            )
        )

    return df


def selector_periodo(df):
    """
    Selector de año y mes.
    Retorna (anio_seleccionado, mes_seleccionado)
    """
    st.markdown("### 📅 Filtros de periodo")

    # ---- Selector de año ----
    anios = sorted(df["anio"].dropna().unique().tolist(), reverse=True)

    anio_sel = st.selectbox(
        "Año",
        anios,
        index=0
    )

    # ---- Selector de mes (depende del año) ----
    df_anio = df[df["anio"] == anio_sel]

    meses = (
        ["Todos"]
        + sorted(df_anio["mes_nombre"].dropna().unique().tolist())
    )

    mes_sel = st.selectbox(
        "Mes",
        meses,
        index=0
    )

    return anio_sel, mes_sel


def mapa_facturacion_clientes(df):
    if df.empty:
        st.warning("No hay datos para mostrar en el mapa.")
        return

    fig = px.scatter_mapbox(
        df,
        lat="latitud",
        lon="longitud",
        size="venta_total",
        color="venta_total",
        color_continuous_scale=[
            (0.0, "#2ECC71"),
            (0.5, "#F1C40F"),
            (1.0, "#E74C3C"),
        ],
        size_max=35,
        zoom=4,
        hover_name="Ciudad"
    )

    fig.update_traces(
        customdata=df[
            ["Estado", "venta_total", "clientes_unicos", "facturas", "latitud", "longitud"]
        ],
        hovertemplate=(
            "<b style='font-size:14px'>📍 %{hovertext}</b><br>"
            "<span style='color:#5178ed'>%{customdata[0]}</span><br>"
            
            "<b>Venta:</b> $%{customdata[1]:,.2f}<br>"
            "<b>Clientes:</b> %{customdata[2]}<br>"
            "<b>Facturas:</b> %{customdata[3]}<br>"
            
            "<b>Latitud:</b> %{customdata[4]:.4f}<br>"
            "<b>Longitud:</b> %{customdata[5]:.4f}"
            "<extra></extra>"
        ),
        marker=dict(opacity=0.7)
    )

    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="Venta total"),
        dragmode="zoom"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"scrollZoom": True}
    )



def mostrar(config):
    st.title("👥 Clientes / Ubicación")

    st.markdown(
        """
        Análisis geográfico de clientes considerando:
        - Facturación
        - Clientes únicos
        - Facturas emitidas
        """
    )

    # Vista base para filtros
    df_base = obtener_vista("vw_dashboard_ubicacion_clientes_mes")

    if df_base.empty:
        st.warning("No hay datos disponibles de clientes.")
        return

    # =========================
    # Selectores
    # =========================
    anio_sel, mes_sel = selector_periodo(df_base)

    # =========================
    # Datos del mapa
    # =========================
    df_mapa = obtener_datos_mapa_clientes(anio_sel, mes_sel)

    st.subheader("🗺️ Facturación y clientes por ubicación")
    mapa_facturacion_clientes(df_mapa)
