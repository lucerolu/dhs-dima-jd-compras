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
    # Sumamos todos sin filtrar Top 10
    data = df.groupby('vendedor', as_index=False)['facturas_canceladas'].sum()
    
    # Ajustamos altura dinámica: 20px por cada vendedor para que no se amontonen
    altura = max(300, len(data) * 20)

    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('facturas_canceladas:Q', title="Total Facturas"),
        y=alt.Y('vendedor:N', sort='-x', title="Vendedor"),
        color=alt.Color('facturas_canceladas:Q', scale=alt.Scale(scheme='reds'), legend=None),
        tooltip=['vendedor', 'facturas_canceladas']
    ).properties(
        title="👤 Cancelaciones por Vendedor (Total)",
        height=altura
    )
    
    st.altair_chart(chart, use_container_width=True)

def grafica_clientes_altair(df):
    # Graficamos todos los clientes agrupados por condición
    data = df.groupby(['Cliente', 'condicion_venta'], as_index=False)['facturas_canceladas'].sum()

    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('Cliente:N', sort='-y', title="Cliente"),
        y=alt.Y('facturas_canceladas:Q', title="Facturas"),
        color=alt.Color('condicion_venta:N', title="Condición"),
        tooltip=['Cliente', 'condicion_venta', 'facturas_canceladas']
    ).properties(
        title="🏢 Cancelaciones por Cliente y Condición",
        height=400
    ).configure_axisX(
        labelAngle=-45 # Inclinamos los nombres para que quepan todos
    )

    st.altair_chart(chart, use_container_width=True)

def grafica_proveedores_altair(df):
    # Agregamos la de proveedores que pediste
    data = df.groupby(['Proveedor', 'condicion_venta'], as_index=False)['facturas_canceladas'].sum()
    
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('Proveedor:N', sort='-y', title="Proveedor"),
        y=alt.Y('facturas_canceladas:Q', title="Facturas"),
        color=alt.Color('condicion_venta:N', scale=alt.Scale(scheme='category10')),
        tooltip=['Proveedor', 'condicion_venta', 'facturas_canceladas']
    ).properties(
        title="🚜 Cancelaciones por Proveedor",
        height=400
    ).configure_axisX(
        labelAngle=-45
    )

    st.altair_chart(chart, use_container_width=True)

def mostrar(config):
    st.title("🚫 Panel de Cancelaciones")
    
    df_raw = cargar_datos()
    if df_raw is None: return

    df_filtrado, sucursal_label = filtrar_datos(df_raw)
    
    # Métricas principales
    total_f = df_filtrado['facturas_canceladas'].sum()
    st.metric(f"Total Facturas Canceladas ({sucursal_label})", f"{total_f:,.0f}")

    st.markdown("---")
    
    # Una gráfica debajo de la otra para máxima visibilidad
    st.subheader("Análisis Temporal")
    grafica_mes_altair(df_filtrado)
    
    st.markdown("---")
    st.subheader("Desglose por Vendedor")
    grafica_vendedores_altair(df_filtrado)
    
    st.markdown("---")
    st.subheader("Desglose por Cliente")
    grafica_clientes_altair(df_filtrado)

    st.markdown("---")
    st.subheader("Desglose por Proveedor")
    grafica_proveedores_altair(df_filtrado)