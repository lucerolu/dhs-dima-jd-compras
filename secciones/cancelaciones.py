import streamlit as st
import pandas as pd
import altair as alt
from utils.api_utils import obtener_vista

def cargar_datos():
    df = obtener_vista("vw_cancelaciones_clientes_detalle")
    if df is None or df.empty:
        return None

    # FORZADO DE TIPOS: Altair necesita saber qué es número y qué es texto
    df["facturas_canceladas"] = pd.to_numeric(df["facturas_canceladas"], errors="coerce").fillna(0)
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").fillna(0).astype(int)
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").fillna(0).astype(int)
    
    # Limpieza de strings
    for col in ["vendedor", "Cliente", "Proveedor", "sucursal", "condicion_venta", "mes_nombre"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
    
    return df

def filtrar_datos(df):
    col1, col2 = st.columns(2)
    with col1:
        años = sorted(df['anio'].unique())
        año_sel = st.radio("Año", años, index=len(años)-1, horizontal=True)
    
    df_f = df[df['anio'] == año_sel].copy()

    with col2:
        sucursales = sorted(df_f['sucursal'].unique())
        sucursal_sel = st.selectbox("Sucursal", ["TODAS"] + sucursales)

    if sucursal_sel != "TODAS":
        df_f = df_f[df_f['sucursal'] == sucursal_sel]
    
    return df_f, sucursal_sel

def grafica_mes_altair(df):
    # Altair agrupa automáticamente si se lo pedimos con 'sum(facturas_canceladas)'
    chart = alt.Chart(df).mark_bar(color='#EF553B').encode(
        x=alt.X('mes_nombre:N', sort=['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 
                                     'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'],
                title="Mes"),
        y=alt.Y('sum(facturas_canceladas):Q', title="Total Facturas"),
        tooltip=['mes_nombre', 'sum(facturas_canceladas)']
    ).properties(title="📅 Cancelaciones por Mes", height=400)
    
    # Añadir etiquetas de texto sobre las barras
    text = chart.mark_text(dy=-10, color='white').encode(
        text=alt.Text('sum(facturas_canceladas):Q', format='.0f')
    )
    
    st.altair_chart(chart + text, use_container_width=True)

def grafica_vendedores_altair(df):
    # Top 10 Vendedores
    top_vendedores = df.groupby('vendedor')['facturas_canceladas'].sum().nlargest(10).reset_index()
    
    chart = alt.Chart(top_vendedores).mark_bar().encode(
        x=alt.X('facturas_canceladas:Q', title="Facturas"),
        y=alt.Y('vendedor:N', sort='-x', title="Vendedor"),
        color=alt.Color('facturas_canceladas:Q', scale=alt.Scale(scheme='reds')),
        tooltip=['vendedor', 'facturas_canceladas']
    ).properties(title="👤 Top 10 Vendedores")
    
    st.altair_chart(chart, use_container_width=True)

def grafica_clientes_altair(df):
    top_10 = df.groupby('Cliente')['facturas_canceladas'].sum().nlargest(10).index
    df_top = df[df['Cliente'].isin(top_10)]

    chart = alt.Chart(df_top).mark_bar().encode(
        x=alt.X('condicion_venta:N', title=None),
        y=alt.Y('sum(facturas_canceladas):Q', title="Facturas"),
        color='condicion_venta:N',
        column=alt.Column('Cliente:N', title="Top 10 Clientes", header=alt.Header(labelAngle=-45, labelAlign='right')),
        tooltip=['Cliente', 'condicion_venta', 'sum(facturas_canceladas)']
    ).properties(width=80, height=300)

    st.altair_chart(chart, use_container_width=True)

def mostrar(config):
    st.title("🚫 Panel de Cancelaciones (Altair Engine)")
    
    df_raw = cargar_datos()
    if df_raw is None: return

    df_filtrado, sucursal_label = filtrar_datos(df_raw)
    
    # Métrica de validación
    st.metric("Total Real (Suma)", f"{df_filtrado['facturas_canceladas'].sum():,.0f}")

    st.markdown("---")
    grafica_mes_altair(df_filtrado)
    
    col_a, col_b = st.columns(2)
    with col_a:
        grafica_vendedores_altair(df_filtrado)
    with col_b:
        # Simplificamos para evitar errores de renderizado
        grafica_clientes_altair(df_filtrado)