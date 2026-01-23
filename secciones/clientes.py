# secciones/clientes.py

import streamlit as st
import plotly.express as px
import pandas as pd
from utils.api_utils import obtener_vista


def obtener_datos_mapa_clientes(anio_seleccionado, mes_seleccionado):
    df = obtener_vista("vw_dashboard_ubicacion_clientes_mes")

    if df.empty:
        return df, df

    # ---- Filtro por año ----
    df = df[df["anio"] == anio_seleccionado]

    # ---- Forzar coordenadas a numérico ----
    for col in [
        "cliente_latitud",
        "cliente_longitud",
        "sucursal_latitud",
        "sucursal_longitud"
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ---- Eliminar clientes sin coordenadas ----
    df = df.dropna(subset=["cliente_latitud", "cliente_longitud"])

    # ---- Filtro por mes ----
    if mes_seleccionado != "Todos":
        df = df[df["mes_nombre"] == mes_seleccionado]
    else:
        df = (
            df.groupby(
                [
                    "Estado",
                    "Ciudad",
                    "cliente_latitud",
                    "cliente_longitud",
                    "sucursal_id",
                    "sucursal",
                    "sucursal_latitud",
                    "sucursal_longitud"
                ],
                as_index=False
            )
            .agg(
                clientes_unicos=("clientes_unicos", "sum"),
                venta_total=("venta_total", "sum"),
                facturas=("facturas", "sum")
            )
        )

    df_clientes = df.copy()

    df_sucursales = (
        df[
            ["sucursal_id", "sucursal", "sucursal_latitud", "sucursal_longitud"]
        ]
        .dropna(subset=["sucursal_latitud", "sucursal_longitud"])
        .drop_duplicates()
    )

    return df_clientes, df_sucursales





def selector_periodo(df):
    """
    Selector de año y mes.
    Retorna (anio_seleccionado, mes_seleccionado)
    """
    st.markdown("### Filtros de periodo")

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


def mapa_facturacion_clientes(df_clientes, df_sucursales):
    if df_clientes.empty:
        st.warning("No hay datos para mostrar en el mapa.")
        return

    # ===============================
    # CAPA CLIENTES
    # ===============================
    fig = px.scatter_mapbox(
        df_clientes,
        lat="cliente_latitud",
        lon="cliente_longitud",
        size="venta_total",
        color="sucursal",
        size_max=45,   # 🔍 más grandes
        zoom=4,
        hover_name="Ciudad"
    )

    fig.update_traces(
        marker=dict(
            opacity=0.75,
            sizemode="area"
        ),
        customdata=df_clientes[
            [
                "Estado",
                "sucursal",
                "venta_total",
                "clientes_unicos",
                "facturas",
                "cliente_latitud",
                "cliente_longitud"
            ]
        ],
        hovertemplate=(
            "<b style='font-size:14px'>📍 %{hovertext}</b><br>"
            "<span style='color:#555'>%{customdata[0]}</span><br><br>"

            "<b>Sucursal:</b> %{customdata[1]}<br>"
            "<b>Venta:</b> $%{customdata[2]:,.2f}<br>"
            "<b>Clientes:</b> %{customdata[3]}<br>"
            "<b>Facturas:</b> %{customdata[4]}<br><br>"

            "<b>Lat:</b> %{customdata[5]:.4f}<br>"
            "<b>Lon:</b> %{customdata[6]:.4f}"
            "<extra></extra>"
        )
    )

    # ===============================
    # CAPA SUCURSALES
    # ===============================
    fig.add_scattermapbox(
        lat=df_sucursales["sucursal_latitud"],
        lon=df_sucursales["sucursal_longitud"],
        mode="markers",
        marker=dict(
            size=18,
            symbol="star",
            color="black"
        ),
        text=df_sucursales["sucursal"],
        hovertemplate=(
            "<b>Sucursal</b><br>"
            "%{text}<br><br>"
            "<b>Lat:</b> %{lat:.4f}<br>"
            "<b>Lon:</b> %{lon:.4f}"
            "<extra></extra>"
        ),
        name="Sucursales"
    )

    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend_title="Sucursal",
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
    df_clientes, df_sucursales = obtener_datos_mapa_clientes(anio_sel, mes_sel)

    st.subheader("🗺️ Clientes y sucursales")
    mapa_facturacion_clientes(df_clientes, df_sucursales)

