# secciones/cancelaciones.py
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
    
    # ASEGURAR NUMÉRICOS (Esto evita que Plotly cuente filas en lugar de sumar)
    df["facturas_canceladas"] = pd.to_numeric(df["facturas_canceladas"], errors="coerce").fillna(0)
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").fillna(0).astype(int)
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").fillna(0).astype(int)
    
    # Meses en español
    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    df["mes_nombre"] = df["mes"].map(meses_es)
    return df

def filtrar_datos(df):
    # Inyectamos CSS para forzar el despliegue hacia abajo
    st.markdown(
        """
        <style>
            div[data-baseweb="popover"] {
                margin-top: 4px !important;
                top: auto !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    
    with col1:
        años_disponibles = sorted(df['anio'].unique())
        año_sel = st.radio(
            "Selecciona el año",
            años_disponibles,
            index=len(años_disponibles) - 1,
            horizontal=True,
            key="cancel_anio"
        )
    
    df_filtrado = df[df['anio'] == año_sel].copy()

    with col2:
        sucursales = sorted(df_filtrado['sucursal'].dropna().unique())
        opciones_sucursal = ["Todos"] + sucursales
        sucursal_sel = st.selectbox(
            "Selecciona la sucursal",
            options=opciones_sucursal,
            index=0,
            key="cancel_sucursal"
        )

    if sucursal_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado['sucursal'] == sucursal_sel]
    
    return df_filtrado, sucursal_sel

def grafica_cancelaciones_mes(df, sucursal_label):
    # Agrupación con suma explícita
    cancelaciones_mes = (
        df.groupby(['mes', 'mes_nombre'], as_index=False)
        .agg({'facturas_canceladas': 'sum'})
        .sort_values('mes')
    )

    fig = px.bar(
        cancelaciones_mes,
        x='mes_nombre',
        y='facturas_canceladas',
        text='facturas_canceladas',
        labels={'mes_nombre': 'Mes', 'facturas_canceladas': 'Facturas'},
        title=f"📅 Cancelaciones por mes - {sucursal_label}",
        color_discrete_sequence=['#EF553B'] 
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

def grafica_top_vendedores(df, sucursal_label):
    top_vendedores = (
        df.groupby('vendedor', as_index=False)
        .agg({'facturas_canceladas': 'sum'})
        .sort_values('facturas_canceladas', ascending=False)
        .head(10)
    )

    fig = px.bar(
        top_vendedores,
        x='vendedor',
        y='facturas_canceladas',
        text='facturas_canceladas',
        title=f"👤 Top 10 Vendedores - {sucursal_label}",
        labels={'vendedor': 'Vendedor', 'facturas_canceladas': 'Facturas'}
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

def grafica_top_clientes(df, sucursal_label):
    # Primero identificamos los nombres del Top 10 real por suma
    top_nombres = df.groupby('Cliente')['facturas_canceladas'].sum().nlargest(10).index
    df_top = df[df['Cliente'].isin(top_nombres)]

    top_clientes = (
        df_top.groupby(['Cliente', 'condicion_venta'], as_index=False)
        .agg({'facturas_canceladas': 'sum'})
        .sort_values('facturas_canceladas', ascending=False)
    )

    fig = px.bar(
        top_clientes,
        x='Cliente',
        y='facturas_canceladas',
        color='condicion_venta',
        text='facturas_canceladas',
        title=f"🏢 Top 10 Clientes - {sucursal_label}",
        labels={'facturas_canceladas': 'Facturas'},
        barmode='group'
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

def grafica_top_proveedores(df, sucursal_label):
    top_nombres = df.groupby('Proveedor')['facturas_canceladas'].sum().nlargest(10).index
    df_top = df[df['Proveedor'].isin(top_nombres)]

    top_proveedores = (
        df_top.groupby(['Proveedor', 'condicion_venta'], as_index=False)
        .agg({'facturas_canceladas': 'sum'})
        .sort_values('facturas_canceladas', ascending=False)
    )

    fig = px.bar(
        top_proveedores,
        x='Proveedor',
        y='facturas_canceladas',
        color='condicion_venta',
        text='facturas_canceladas',
        title=f"🚜 Top 10 Proveedores - {sucursal_label}",
        labels={'facturas_canceladas': 'Facturas'},
        barmode='group'
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

def mostrar(config):
    st.title("🚫 Panel de Cancelaciones")
    render_descripcion()

    df_raw = cargar_datos()
    if df_raw is None:
        return

    df_filtrado, sucursal_label = filtrar_datos(df_raw)

    st.markdown("---")
    
    # Métrica de resumen para validar números
    total = df_filtrado['facturas_canceladas'].sum()
    st.metric("Total Facturas Canceladas", f"{total:,.0f}")

    grafica_cancelaciones_mes(df_filtrado, sucursal_label)
    
    col_a, col_b = st.columns(2)
    with col_a:
        grafica_top_vendedores(df_filtrado, sucursal_label)
    with col_b:
        grafica_top_clientes(df_filtrado, sucursal_label)

    st.markdown("---")
    grafica_top_proveedores(df_filtrado, sucursal_label)