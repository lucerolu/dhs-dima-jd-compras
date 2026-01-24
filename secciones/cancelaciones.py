import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api_utils import obtener_vista

def render_descripcion():
    st.markdown(
        """
        **Análisis de cancelaciones**
        
        - Desglose por Vendedor, Cliente y Proveedor.
        - Filtros por año fiscal y sucursal.
        """
    )

def cargar_datos():
    df = obtener_vista("vw_cancelaciones_clientes_detalle")
    if df is None or df.empty:
        st.warning("No hay datos disponibles de cancelaciones.")
        return None

    # Limpieza de tipos de datos
    df["facturas_canceladas"] = pd.to_numeric(df["facturas_canceladas"], errors="coerce").fillna(0)
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce")
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce")

    # Normalizar textos
    columnas_texto = ["Proveedor", "Cliente", "vendedor", "sucursal", "condicion_venta"]
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    return df

def filtrar_datos(df):
    # CSS para mejorar la visibilidad de los selectores
    st.markdown("<style>div[data-baseweb='popover'] { margin-top: 4px !important; }</style>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        años_disponibles = sorted(df['anio'].dropna().unique().astype(int))
        año_sel = st.radio("Selecciona el año", años_disponibles, index=len(años_disponibles)-1, horizontal=True, key="cancel_anio")
    
    df_filtrado = df[df['anio'] == año_sel].copy()

    with col2:
        sucursales = sorted(df_filtrado['sucursal'].dropna().unique())
        opciones_sucursal = ["Todas las sucursales"] + sucursales
        sucursal_sel = st.selectbox("Selecciona la sucursal", options=opciones_sucursal, index=0, key="cancel_sucursal")

    if sucursal_sel != "Todas las sucursales":
        df_filtrado = df_filtrado[df_filtrado['sucursal'] == sucursal_sel]
    
    return df_filtrado, sucursal_sel

def grafica_cancelaciones_mes(df, sucursal_label):
    # Agrupamos por mes (número) para mantener el orden
    meses_data = df.groupby(["mes"], as_index=False)["facturas_canceladas"].sum().sort_values("mes")
    
    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    meses_data["mes_nombre"] = meses_data["mes"].map(meses_es)

    fig = px.bar(
        meses_data,
        x="mes_nombre",
        y="facturas_canceladas",
        title=f"📊 Cancelaciones por Mes – {sucursal_label}",
        text_auto='.0f',
        color_discrete_sequence=['#3366CC']
    )

    # Forzar orden cronológico en el eje X
    fig.update_xaxes(categoryorder='array', categoryarray=list(meses_es.values()))
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

def grafica_top_vendedores(df, sucursal_label):
    top_vendedores = (
        df.groupby("vendedor", as_index=False)["facturas_canceladas"]
        .sum()
        .sort_values("facturas_canceladas", ascending=False)
        .head(10)
    )

    fig = px.bar(
        top_vendedores,
        x="facturas_canceladas",
        y="vendedor",
        orientation='h', # Horizontal para leer mejor los nombres largos
        title=f"👤 Top 10 Vendedores – {sucursal_label}",
        text_auto='.0f',
        color="facturas_canceladas",
        color_continuous_scale="Blues"
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

def grafica_top_clientes(df, sucursal_label):
    # Identificar los top 10 clientes primero
    top_10_list = df.groupby("Cliente")["facturas_canceladas"].sum().nlargest(10).index
    df_top = df[df["Cliente"].isin(top_10_list)]

    # Agrupar por Cliente y Condición para la gráfica apilada o agrupada
    plot_data = df_top.groupby(["Cliente", "condicion_venta"], as_index=False)["facturas_canceladas"].sum()

    fig = px.bar(
        plot_data,
        x="Cliente",
        y="facturas_canceladas",
        color="condicion_venta",
        title=f"🏢 Top 10 Clientes – {sucursal_label}",
        barmode="group",
        text_auto='.0f'
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

def grafica_top_proveedores(df, sucursal_label):
    # Identificar los top 10 proveedores
    top_10_list = df.groupby("Proveedor")["facturas_canceladas"].sum().nlargest(10).index
    df_top = df[df["Proveedor"].isin(top_10_list)]

    plot_data = df_top.groupby(["Proveedor", "condicion_venta"], as_index=False)["facturas_canceladas"].sum()

    fig = px.bar(
        plot_data,
        x="Proveedor",
        y="facturas_canceladas",
        color="condicion_venta",
        title=f"🏭 Top 10 Proveedores – {sucursal_label}",
        barmode="group",
        text_auto='.0f'
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

def mostrar(config):
    st.title("🚫 Panel de Cancelaciones")
    render_descripcion()

    df_raw = cargar_datos()
    if df_raw is None:
        return

    df_filtrado, sucursal_label = filtrar_datos(df_raw)

    if df_filtrado.empty:
        st.info("No hay datos para los filtros seleccionados.")
        return

    st.markdown("---")
    
    # Métricas rápidas opcionales
    total_canc = df_filtrado["facturas_canceladas"].sum()
    st.metric("Total Facturas Canceladas", f"{total_canc:,.0f}")

    # Gráficas
    grafica_cancelaciones_mes(df_filtrado, sucursal_label)
    
    col_a, col_b = st.columns(2)
    with col_a:
        grafica_top_vendedores(df_filtrado, sucursal_label)
    with col_b:
        grafica_top_clientes(df_filtrado, sucursal_label)

    st.markdown("---")
    grafica_top_proveedores(df_filtrado, sucursal_label)