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



def obtener_datos_mapa_sucursales(df_limpio, anio_seleccionado, mes_seleccionado):

    df = df_limpio[df_limpio["anio"] == anio_seleccionado]

    if mes_seleccionado != "Todos":
        df = df[df["mes_nombre"] == mes_seleccionado]

    df_suc = df.groupby(
        [
            "sucursal",
            "sucursal_latitud",
            "sucursal_longitud"
        ],
        as_index=False
    ).agg({
        "venta_total": "sum",
        "clientes_unicos": "sum",
        "facturas": "sum"
    })

    # limpiar coordenadas inválidas
    df_suc = df_suc[
        df_suc["sucursal_latitud"].between(-90, 90) &
        df_suc["sucursal_longitud"].between(-180, 180) &
        (df_suc["venta_total"] > 0)
    ]

    return df_suc



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


def _fig_barras_sucursal(
    df_plot,
    eje_x,
    titulo,
    formato_x,
    colorbar_title,
    custom_cols,
    hovertemplate,
):
    fig = px.bar(
        df_plot,
        x=eje_x,
        y="sucursal",
        orientation="h",
        color=eje_x,
        color_continuous_scale=px.colors.sequential.Plasma,
        text=eje_x
    )

    fig.update_traces(
        customdata=df_plot[custom_cols],
        hovertemplate=hovertemplate,
        texttemplate=f"%{{text:{formato_x}}}",
        textposition="outside",
        cliponaxis=False  # 👈 evita que se corten los números
    )

    fig.update_layout(
        title=titulo,
        yaxis_title=None,
        xaxis_title=None,
        coloraxis_colorbar=dict(
            title=colorbar_title,
            y=0.05,              # 👈 la baja
            yanchor="bottom",   # 👈 se ancla desde abajo
            len=0.8             # 👈 no ocupa todo el alto
        ),
        margin=dict(l=140, r=40, t=60, b=30),
        height=500
    )
    return fig



def grafico_barras_sucursales(df_limpio, anio_seleccionado, mes_seleccionado):

    # -----------------------------
    # Filtro periodo
    # -----------------------------
    df = df_limpio[df_limpio["anio"] == anio_seleccionado]

    if mes_seleccionado != "Todos":
        df = df[df["mes_nombre"] == mes_seleccionado]

    if df.empty:
        st.warning("No hay datos para el periodo seleccionado.")
        return

    # -----------------------------
    # Agrupación
    # -----------------------------
    df_suc = df.groupby(
        ["sucursal"],
        as_index=False
    ).agg({
        "venta_total": "sum",
        "clientes_unicos": "sum",
        "facturas": "sum"
    })

    df_suc = df_suc[df_suc["venta_total"] > 0]

    # Orden base
    df_venta = df_suc.sort_values("venta_total", ascending=True)
    df_clientes = df_suc.sort_values("clientes_unicos", ascending=True)

    # -----------------------------
    # Figuras
    # -----------------------------
    fig_venta = _fig_barras_sucursal(
        df_plot=df_venta,
        eje_x="venta_total",
        titulo="Ventas totales por sucursal",
        formato_x="$,.2f",
        colorbar_title="Venta total",
        custom_cols=["clientes_unicos", "facturas"],
        hovertemplate=(
            "<b>%{y}</b><br><br>"
            "Venta total: $%{x:,.2f}<br>"
            "Clientes únicos: %{customdata[0]:,}<br>"
            "Facturas: %{customdata[1]:,}"
            "<extra></extra>"
        )
    )

    fig_clientes = _fig_barras_sucursal(
        df_plot=df_clientes,
        eje_x="clientes_unicos",
        titulo="Clientes únicos por sucursal",
        formato_x=",",
        colorbar_title="Clientes únicos",
        custom_cols=["venta_total", "facturas"],
        hovertemplate=(
            "<b>%{y}</b><br><br>"
            "Clientes únicos: %{x:,}<br>"
            "Venta total: $%{customdata[0]:,.2f}<br>"
            "Facturas: %{customdata[1]:,}"
            "<extra></extra>"
        )
    )

    # -----------------------------
    # Layout responsive
    # -----------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(fig_venta, use_container_width=True)

    with col2:
        st.plotly_chart(fig_clientes, use_container_width=True)



def mapa_sucursales_facturacion(df_suc):

    if df_suc.empty:
        st.warning("No hay datos de sucursales para el periodo seleccionado.")
        return

    fig = px.scatter_mapbox(
        df_suc,
        lat="sucursal_latitud",
        lon="sucursal_longitud",
        size="venta_total",                     # 👈 tamaño por venta
        color="venta_total",
        color_continuous_scale=px.colors.sequential.Plasma,
        size_max=40,                            # 👈 evita burbujas gigantes
        zoom=4,
        hover_name="sucursal"
    )

    fig.update_traces(
        marker=dict(opacity=0.75),
        customdata=df_suc[
            ["venta_total", "clientes_unicos", "facturas"]
        ],
        hovertemplate=(
            "<b>🏢 %{hovertext}</b><br><br>"
            "<b>Venta total:</b> $%{customdata[0]:,.2f}<br>"
            "<b>Clientes únicos:</b> %{customdata[1]:,}<br>"
            "<b>Facturas:</b> %{customdata[2]:,}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(
            title="Venta total",
            y=0.05,
            yanchor="bottom",
            len=0.7
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"scrollZoom": True}
    )




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

    df_sucursales = obtener_datos_mapa_sucursales(
        df_limpio, anio_sel, mes_sel
    )

    st.subheader(
        f"Distribución de ventas por domicilio fiscal - {mes_sel} {anio_sel}"
    )

    mapa_facturacion_clientes(df_clientes)
    grafico_barras_sucursales(df_limpio, anio_sel, mes_sel)
    mapa_sucursales_facturacion(df_sucursales)

