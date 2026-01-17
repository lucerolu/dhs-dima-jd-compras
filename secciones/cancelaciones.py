#secciones\cancelaciones.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api_utils import obtener_vista

def mostrar(config):
    st.title("👥 Cancelaciones")

    st.markdown(
        """
        Análisis de cancelaciones por:
        - Vendedor
        - Cliente
        - Proveedor 
        """
    )

    # Obtener datos
    df = obtener_vista("vw_cancelaciones_clientes_detalle")

    if df.empty:
        st.warning("No hay datos disponibles de cancelaciones.")
        return

    # ----------------------
    # Meses en español
    # ----------------------
    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    df["mes_nombre"] = df["mes"].map(meses_es)

    # ----------------------
    # Selector de año
    # ----------------------
    años_disponibles = sorted(df['anio'].unique())
    año_seleccionado = st.radio(
        "Selecciona el año",
        años_disponibles,
        index=len(años_disponibles) - 1,
        horizontal=True
    )

    df = df[df['anio'] == año_seleccionado]

    # ----------------------
    # Selector de sucursal (con TODOS)
    # ----------------------
    sucursales = sorted(df['sucursal'].dropna().unique())
    opciones_sucursal = ["Todos"] + sucursales

    sucursal_seleccionada = st.selectbox(
        "Selecciona la sucursal",
        options=opciones_sucursal,
        index=0  # "Todos" preseleccionado
    )

    if sucursal_seleccionada == "Todos":
        df_sucursal = df
    else:
        df_sucursal = df[df['sucursal'] == sucursal_seleccionada]

    # ----------------------
    # Cancelaciones por mes
    # ----------------------
    cancelaciones_mes = (
        df_sucursal.groupby(['mes', 'mes_nombre'], as_index=False)
        .agg({'facturas_canceladas': 'sum'})
        .sort_values('mes')
    )

    fig_mes = px.bar(
        cancelaciones_mes,
        x='mes_nombre',
        y='facturas_canceladas',
        text='facturas_canceladas',
        labels={'mes_nombre': 'Mes', 'facturas_canceladas': 'Facturas Canceladas'},
        title=f"Cancelaciones por mes - {sucursal_seleccionada}"
    )
    fig_mes.update_traces(textposition='outside')
    st.plotly_chart(fig_mes, use_container_width=True)

    # ----------------------
    # Top 10 vendedores
    # ----------------------
    top_vendedores = (
        df_sucursal.groupby('vendedor', as_index=False)
        .agg({'facturas_canceladas': 'sum'})
        .sort_values('facturas_canceladas', ascending=False)
        .head(10)
    )

    fig_vendedores = px.bar(
        top_vendedores,
        x='vendedor',
        y='facturas_canceladas',
        text='facturas_canceladas',
        labels={'vendedor': 'Vendedor', 'facturas_canceladas': 'Facturas Canceladas'},
        title=f"Top 10 Vendedores con más cancelaciones - {sucursal_seleccionada}"
    )
    fig_vendedores.update_traces(textposition='outside')
    st.plotly_chart(fig_vendedores, use_container_width=True)

    # ----------------------
    # Top 10 clientes
    # ----------------------
    top_clientes = (
        df_sucursal.groupby(['Cliente', 'condicion_venta'], as_index=False)
        .agg({'facturas_canceladas': 'sum'})
        .sort_values('facturas_canceladas', ascending=False)
        .head(10)
    )

    fig_clientes = px.bar(
        top_clientes,
        x='Cliente',
        y='facturas_canceladas',
        color='condicion_venta',
        text='facturas_canceladas',
        labels={
            'Cliente': 'Cliente',
            'facturas_canceladas': 'Facturas Canceladas',
            'condicion_venta': 'Condición de Venta'
        },
        title=f"Top 10 Clientes con más cancelaciones - {sucursal_seleccionada}"
    )
    fig_clientes.update_traces(textposition='outside')
    st.plotly_chart(fig_clientes, use_container_width=True)

    # ----------------------
    # Top 10 proveedores
    # ----------------------
    top_proveedores = (
        df_sucursal.groupby(['Proveedor', 'condicion_venta'], as_index=False)
        .agg({'facturas_canceladas': 'sum'})
        .sort_values('facturas_canceladas', ascending=False)
        .head(10)
    )

    fig_proveedores = px.bar(
        top_proveedores,
        x='Proveedor',
        y='facturas_canceladas',
        color='condicion_venta',
        text='facturas_canceladas',
        labels={
            'Proveedor': 'Proveedor',
            'facturas_canceladas': 'Facturas Canceladas',
            'condicion_venta': 'Condición de Venta'
        },
        title=f"Top 10 Proveedores con más cancelaciones - {sucursal_seleccionada}"
    )
    fig_proveedores.update_traces(textposition='outside')
    st.plotly_chart(fig_proveedores, use_container_width=True)
