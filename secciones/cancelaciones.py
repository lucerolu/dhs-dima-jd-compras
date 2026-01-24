# secciones/cancelaciones.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api_utils import obtener_vista

# ---------------------------------
# Descripción del dashboard
# ---------------------------------
def render_descripcion():
    st.markdown(
        """
        **Análisis de cancelaciones**
        
        - Desglose por Vendedor, Cliente y Proveedor.
        - Filtros por año fiscal y sucursal.
        """
    )

# ---------------------------------
# Cargar y normalizar datos
# ---------------------------------
def cargar_datos():
    df = obtener_vista("vw_cancelaciones_clientes_detalle")
    if df.empty:
        st.warning("No hay datos disponibles de cancelaciones.")
        return None

    # --- Campos numéricos
    df["facturas_canceladas"] = pd.to_numeric(df["facturas_canceladas"], errors="coerce").fillna(0).astype(int)
    df["refacciones_canceladas"] = pd.to_numeric(df.get("refacciones_canceladas", 0), errors="coerce").fillna(0).astype(int)
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce")

    # --- Normalizar textos
    for col in ["Proveedor", "Cliente", "vendedor", "sucursal", "condicion_venta"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # --- Meses en español (por si alguna fila no tiene)
    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    df["mes_nombre"] = df["mes"].map(meses_es).fillna("Mes inválido")

    return df

# ---------------------------------
# Filtros año y sucursal
# ---------------------------------
def filtrar_datos(df):
    st.markdown(
        """
        <style>
            div[data-baseweb="popover"] { margin-top: 4px !important; top: auto !important; }
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
            index=len(años_disponibles)-1,
            horizontal=True,
            key="cancel_anio"
        )

    df_filtrado = df[df['anio'] == año_sel]

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

    label = "Todas las sucursales" if sucursal_sel == "Todos" else sucursal_sel
    return df_filtrado, label

# ---------------------------------
# Gráficas
# ---------------------------------
def grafica_cancelaciones_mes(df, sucursal_label):
    cancelaciones_mes = df.groupby("mes", as_index=False)["facturas_canceladas"].sum().sort_values("mes")
    cancelaciones_mes["mes_nombre"] = cancelaciones_mes["mes"].map({
        1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",7:"Julio",
        8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
    })

    fig = px.bar(
        cancelaciones_mes,
        x="mes_nombre",
        y="facturas_canceladas",
        title=f"Cancelaciones por mes – {sucursal_label}"
    )

    fig.update_traces(
        texttemplate="%{y:,}",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Facturas: %{y:,}<extra></extra>"
    )

    fig.update_layout(yaxis=dict(tickformat=","))

    st.plotly_chart(fig, use_container_width=True)

def grafica_top_vendedores(df, sucursal_label):
    top_vendedores = df.groupby("vendedor", as_index=False)["facturas_canceladas"].sum().sort_values("facturas_canceladas", ascending=False).head(10)

    fig = px.bar(
        top_vendedores,
        x="vendedor",
        y="facturas_canceladas",
        title=f"👤 Top 10 Vendedores – {sucursal_label}"
    )

    fig.update_traces(
        texttemplate="%{y:,}",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Facturas: %{y:,}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

def grafica_top_clientes(df, sucursal_label):
    base = df.groupby(["Cliente","condicion_venta"], as_index=False)["facturas_canceladas"].sum()
    top_clientes = base.groupby("Cliente", as_index=False)["facturas_canceladas"].sum().sort_values("facturas_canceladas", ascending=False).head(10).merge(base, on="Cliente")

    fig = px.bar(
        top_clientes,
        x="Cliente",
        y="facturas_canceladas_y",
        color="condicion_venta",
        title=f"🏢 Top 10 Clientes – {sucursal_label}"
    )

    fig.update_traces(
        texttemplate="%{y:,}",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Facturas: %{y:,}<br>Condición: %{legendgroup}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

def grafica_top_proveedores(df, sucursal_label):
    base = df.groupby(["Proveedor","condicion_venta"], as_index=False)["facturas_canceladas"].sum()
    top_proveedores = base.groupby("Proveedor", as_index=False)["facturas_canceladas"].sum().sort_values("facturas_canceladas", ascending=False).head(10).merge(base, on="Proveedor")

    fig = px.bar(
        top_proveedores,
        x="Proveedor",
        y="facturas_canceladas_y",
        color="condicion_venta",
        title=f"🏭 Top 10 Proveedores – {sucursal_label}"
    )

    fig.update_traces(
        texttemplate="%{y:,}",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Facturas: %{y:,}<br>Condición: %{legendgroup}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------
# Función principal
# ---------------------------------
def mostrar(config):
    st.title("Cancelaciones")
    render_descripcion()

    # 1️⃣ Carga de datos
    df_raw = cargar_datos()
    if df_raw is None:
        return

    # 2️⃣ Aplicar filtros
    df_filtrado, sucursal_label = filtrar_datos(df_raw)

    st.markdown("---")

    # 3️⃣ Graficar
    grafica_cancelaciones_mes(df_filtrado, sucursal_label)

    col_a, col_b = st.columns(2)
    with col_a:
        grafica_top_vendedores(df_filtrado, sucursal_label)
    with col_b:
        grafica_top_clientes(df_filtrado, sucursal_label)

    st.markdown("---")
    grafica_top_proveedores(df_filtrado, sucursal_label)
