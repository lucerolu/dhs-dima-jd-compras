import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api_utils import obtener_vista

def cargar_datos():
    # Usamos la vista detalle que tiene todas las dimensiones necesarias
    df = obtener_vista("vw_cancelaciones_clientes_detalle")
    
    if df is None or df.empty:
        st.warning("No se encontraron datos en la vista de cancelaciones.")
        return None

    # --- LIMPIEZA DE DATOS CRUCIAL ---
    # Aseguramos que los números sean números (evita el error de la escalera)
    df["facturas_canceladas"] = pd.to_numeric(df["facturas_canceladas"], errors="coerce").fillna(0)
    df["refacciones_canceladas"] = pd.to_numeric(df["refacciones_canceladas"], errors="coerce").fillna(0)
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").fillna(0).astype(int)
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").fillna(0).astype(int)

    # Normalizamos textos para que "Contado" y "CONTADO" sean lo mismo
    for col in ["vendedor", "Cliente", "Proveedor", "sucursal", "condicion_venta"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
    
    return df

def filtrar_datos(df):
    # CSS para que el selector no se corte
    st.markdown("<style>div[data-baseweb='popover'] { margin-top: 4px !important; }</style>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        años = sorted(df['anio'].unique())
        año_sel = st.radio("Año Fiscal", años, index=len(años)-1, horizontal=True, key="c_anio")
    
    df_f = df[df['anio'] == año_sel].copy()

    with col2:
        sucursales = sorted(df_f['sucursal'].dropna().unique())
        sucursal_sel = st.selectbox("Sucursal", ["TODAS LAS SUCURSALES"] + sucursales, key="c_suc")

    if sucursal_sel != "TODAS LAS SUCURSALES":
        df_f = df_f[df_f['sucursal'] == sucursal_sel]
    
    return df_f, sucursal_sel

def grafica_mes(df, label):
    # Agregamos por mes y mes_nombre
    data = df.groupby(['mes', 'mes_nombre'], as_index=False)['facturas_canceladas'].sum().sort_values('mes')
    
    fig = px.bar(
        data, x='mes_nombre', y='facturas_canceladas',
        text='facturas_canceladas', title=f"📅 Cancelaciones Mensuales - {label}",
        color_discrete_sequence=['#EF553B']
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

def grafica_vendedores(df, label):
    # Sumamos facturas por vendedor
    data = df.groupby('vendedor', as_index=False)['facturas_canceladas'].sum().sort_values('facturas_canceladas', ascending=False).head(10)
    
    fig = px.bar(
        data, x='facturas_canceladas', y='vendedor',
        orientation='h', text='facturas_canceladas',
        title=f"👤 Top 10 Vendedores - {label}",
        color='facturas_canceladas', color_continuous_scale='Reds'
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

def grafica_clientes(df, label):
    # Identificar Top 10 Clientes por suma total
    top_10 = df.groupby('Cliente')['facturas_canceladas'].sum().nlargest(10).index
    df_top = df[df['Cliente'].isin(top_10)]
    
    # Agrupar por Cliente y Condición
    data = df_top.groupby(['Cliente', 'condicion_venta'], as_index=False)['facturas_canceladas'].sum()

    fig = px.bar(
        data, x='Cliente', y='facturas_canceladas',
        color='condicion_venta', text='facturas_canceladas',
        title=f"🏢 Top 10 Clientes - {label}",
        barmode='group'
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

def grafica_proveedores(df, label):
    top_10 = df.groupby('Proveedor')['facturas_canceladas'].sum().nlargest(10).index
    df_top = df[df['Proveedor'].isin(top_10)]
    
    data = df_top.groupby(['Proveedor', 'condicion_venta'], as_index=False)['facturas_canceladas'].sum()

    fig = px.bar(
        data, x='Proveedor', y='facturas_canceladas',
        color='condicion_venta', text='facturas_canceladas',
        title=f"🚜 Top 10 Proveedores - {label}",
        barmode='group'
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

def mostrar(config):
    st.title("🚫 Análisis de Cancelaciones")
    
    df_raw = cargar_datos()
    if df_raw is None: return

    df_filtrado, sucursal_label = filtrar_datos(df_raw)

    # Métricas de encabezado
    c1, c2 = st.columns(2)
    total_f = df_filtrado['facturas_canceladas'].sum()
    total_r = df_filtrado['refacciones_canceladas'].sum()
    c1.metric("Facturas Canceladas", f"{total_f:,.0f}")
    c2.metric("Refacciones Involucradas", f"{total_r:,.0f}")

    st.markdown("---")
    grafica_mes(df_filtrado, sucursal_label)
    
    col_a, col_b = st.columns(2)
    with col_a:
        grafica_vendedores(df_filtrado, sucursal_label)
    with col_b:
        grafica_clientes(df_filtrado, sucursal_label)

    st.markdown("---")
    grafica_proveedores(df_filtrado, sucursal_label)