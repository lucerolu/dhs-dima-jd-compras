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
        return None

    # ASEGURAR NUMÉRICOS: Crucial para que Plotly no use el índice
    df["facturas_canceladas"] = pd.to_numeric(df["facturas_canceladas"], errors="coerce").fillna(0)
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").fillna(0).astype(int)
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").fillna(0).astype(int)

    # Limpieza de textos
    for col in ["Proveedor", "Cliente", "vendedor", "sucursal", "condicion_venta"]:
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

def grafica_cancelaciones_mes(df, sucursal_label):
    meses_data = df.groupby("mes")["facturas_canceladas"].sum().reset_index().sort_values("mes")
    
    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    meses_data["mes_nombre"] = meses_data["mes"].map(meses_es)

    fig = px.bar(
        meses_data,
        x="mes_nombre",
        y="facturas_canceladas",
        title=f"📅 Cancelaciones por Mes – {sucursal_label}",
        text="facturas_canceladas", # Referencia explícita
    )
    fig.update_traces(textposition="outside", marker_color='#1f77b4')
    fig.update_layout(xaxis={'categoryorder':'array', 'categoryarray': list(meses_es.values())})
    st.plotly_chart(fig, use_container_width=True)

def grafica_top_vendedores(df, sucursal_label):
    top_vendedores = df.groupby("vendedor")["facturas_canceladas"].sum().reset_index().sort_values("facturas_canceladas", ascending=False).head(10)

    fig = px.bar(
        top_vendedores,
        x="facturas_canceladas",
        y="vendedor",
        orientation='h',
        title=f"👤 Top 10 Vendedores – {sucursal_label}",
        text="facturas_canceladas"
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

def grafica_top_clientes(df, sucursal_label):
    top_10_names = df.groupby("Cliente")["facturas_canceladas"].sum().nlargest(10).index
    df_top = df[df["Cliente"].isin(top_10_names)]
    plot_data = df_top.groupby(["Cliente", "condicion_venta"])["facturas_canceladas"].sum().reset_index()

    fig = px.bar(
        plot_data,
        x="Cliente",
        y="facturas_canceladas",
        color="condicion_venta",
        title=f"🏢 Top 10 Clientes – {sucursal_label}",
        barmode="group",
        text="facturas_canceladas"
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

def grafica_top_proveedores(df, sucursal_label):
    # Corregido: Ahora usa reset_index y text="facturas_canceladas" para evitar la escalera
    top_10_list = df.groupby("Proveedor")["facturas_canceladas"].sum().nlargest(10).index
    df_top = df[df["Proveedor"].isin(top_10_list)]
    plot_data = df_top.groupby(["Proveedor", "condicion_venta"])["facturas_canceladas"].sum().reset_index()

    fig = px.bar(
        plot_data,
        x="Proveedor",
        y="facturas_canceladas",
        color="condicion_venta",
        title=f"🏭 Top 10 Proveedores – {sucursal_label}",
        barmode="group",
        text="facturas_canceladas"
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

def mostrar(config):
    st.title("🚫 Panel de Cancelaciones")
    render_descripcion()
    df_raw = cargar_datos()
    if df_raw is None: return

    df_filtrado, sucursal_label = filtrar_datos(df_raw)
    if df_filtrado.empty:
        st.info("No hay datos para esta selección.")
        return

    st.markdown("---")
    total_canc = df_filtrado["facturas_canceladas"].sum()
    st.metric("Total Facturas Canceladas", f"{total_canc:,.0f}")

    grafica_cancelaciones_mes(df_filtrado, sucursal_label)
    
    col_a, col_b = st.columns(2)
    with col_a:
        grafica_top_vendedores(df_filtrado, sucursal_label)
    with col_b:
        grafica_top_clientes(df_filtrado, sucursal_label)

    st.markdown("---")
    grafica_top_proveedores(df_filtrado, sucursal_label)