import streamlit as st
import plotly.express as px
import pandas as pd
from utils.api_utils import obtener_vista

def obtener_datos_mapa_clientes(anio_seleccionado, mes_seleccionado):
    df = obtener_vista("vw_dashboard_ubicacion_clientes_mes")
    if df.empty: 
        return pd.DataFrame()

    # ---- 1. Filtro y Limpieza de Coordenadas de Clientes ----
    df = df[df["anio"] == anio_seleccionado].copy()
    
        # ---- Validación geográfica y corrección de coordenadas ----

    # Rango geográfico válido
    df = df[
        (df["cliente_latitud"].between(-90, 90)) &
        (df["cliente_longitud"].between(-180, 180))
    ]

    # Eliminar ceros
    df = df[
        (df["cliente_latitud"] != 0) &
        (df["cliente_longitud"] != 0)
    ]

    # Detectar lat/lon invertidos (caso típico)
    mask_invertidos = df["cliente_latitud"].abs() > 90
    df.loc[mask_invertidos, ["cliente_latitud", "cliente_longitud"]] = (
        df.loc[mask_invertidos, ["cliente_longitud", "cliente_latitud"]].values
    )

    # Redondear para estabilidad del mapa
    df["cliente_latitud"] = df["cliente_latitud"].round(5)
    df["cliente_longitud"] = df["cliente_longitud"].round(5)


    # ---- Filtro por mes ----
    if mes_seleccionado != "Todos":
        df = df[df["mes_nombre"] == mes_seleccionado]

    # ---- Agrupación por Ubicación de Cliente ----
    # Agrupamos para sumar ventas si hay múltiples registros en la misma ciudad/coordenada
    df_clientes = df.groupby(
        ["Estado", "Ciudad", "cliente_latitud", "cliente_longitud"],
        as_index=False
    ).agg({
        "clientes_unicos": "sum",
        "venta_total": "sum",
        "facturas": "sum"
    })

    return df_clientes

def selector_periodo(df):
    st.markdown("### Filtros de periodo")
    anios = sorted(df["anio"].dropna().unique().tolist(), reverse=True)
    anio_sel = st.selectbox("Año", anios, index=0)

    df_anio = df[df["anio"] == anio_sel]
    meses = ["Todos"] + sorted(df_anio["mes_nombre"].dropna().unique().tolist())
    mes_sel = st.selectbox("Mes", meses, index=0)

    return anio_sel, mes_sel

def mapa_facturacion_clientes(df_clientes):
    if df_clientes.empty:
        st.warning("No hay datos para mostrar en las coordenadas seleccionadas.")
        return

    # Creamos el mapa base de clientes
    fig = px.scatter_mapbox(
        df_clientes,
        lat="cliente_latitud",
        lon="cliente_longitud",
        size="venta_total",
        color="venta_total", # Color basado en volumen de venta
        color_continuous_scale=px.colors.sequential.Plasma,
        size_max=35,
        zoom=4,
        hover_name="Ciudad"
    )

    # Configuración del Tooltip (Custom Data)
    fig.update_traces(
        marker=dict(opacity=0.8),
        customdata=df_clientes[
            [
                "Estado",           # [0]
                "venta_total",      # [1]
                "clientes_unicos",  # [2]
                "facturas",         # [3]
                "cliente_latitud",  # [4]
                "cliente_longitud"  # [5]
            ]
        ],
        hovertemplate=(
            "<b style='font-size:14px'>📍 %{hovertext}</b><br>"
            "<span style='color:#555'>%{customdata[0]}</span><br><br>"
            
            "<b>Venta:</b> $%{customdata[1]:,.2f}<br>"
            "<b>Clientes:</b> %{customdata[2]}<br>"
            "<b>Facturas:</b> %{customdata[3]}<br><br>"
            
            "<b>Lat:</b> %{customdata[4]:.4f}<br>"
            "<b>Lon:</b> %{customdata[5]:.4f}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_showscale=True,
        coloraxis_colorbar=dict(title="Venta Total")
    )

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

def mostrar(config):
    st.title("Clientes / Ubicación")

    st.markdown("Análisis geográfico de facturación por ubicación de clientes.")

    df_base = obtener_vista("vw_dashboard_ubicacion_clientes_mes")
    if df_base.empty:
        st.warning("No hay datos disponibles.")
        return

    anio_sel, mes_sel = selector_periodo(df_base)
    df_clientes = obtener_datos_mapa_clientes(anio_sel, mes_sel)

    st.subheader(f"Distribución de ventas por domicilio fiscal - {mes_sel} {anio_sel}")
    mapa_facturacion_clientes(df_clientes)
