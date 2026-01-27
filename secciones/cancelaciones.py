import streamlit as st
import pandas as pd
import altair as alt
from utils.api_utils import obtener_vista

def cargar_datos():
    df = obtener_vista("vw_cancelaciones_clientes_detalle")
    if df is None or df.empty:
        return None

    # Asegurar tipos numéricos
    df["facturas_canceladas"] = pd.to_numeric(df["facturas_canceladas"], errors="coerce").fillna(0)
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").fillna(0).astype(int)
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").fillna(0).astype(int)
    
    # DICCIONARIO MAESTRO PARA MESES EN ESPAÑOL
    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    # Sobreescribimos mes_nombre basado en el número del mes
    df["mes_nombre"] = df["mes"].map(meses_es)
    
    # Limpieza de los demás strings
    columnas_txt = ["vendedor", "Cliente", "Proveedor", "sucursal", "condicion_venta"]
    for col in columnas_txt:
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
    # Lista para asegurar el orden cronológico exacto
    orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

    # Base del gráfico
    base = alt.Chart(df).encode(
        x=alt.X('mes_nombre:N', 
                sort=orden_meses, 
                title="Mes"),
        y=alt.Y('sum(facturas_canceladas):Q', 
                title="Total Facturas")
    )

    # Las barras
    bars = base.mark_bar(color='#EF553B').encode(
        tooltip=[
            alt.Tooltip('mes_nombre:N', title='Mes'),
            alt.Tooltip('sum(facturas_canceladas):Q', title='Facturas', format='.0f')
        ]
    )

    # Las etiquetas sobre las barras (Cambié el color a 'black' para contraste, o 'white' si usas tema oscuro)
    text = base.mark_text(dy=-10, color='gray', fontWeight='bold').encode(
        text=alt.Text('sum(facturas_canceladas):Q', format='.0f')
    )

    chart = (bars + text).properties(
        title="Cancelaciones por Mes",
        height=400
    ).configure_axisX(
        labelAngle=0,          # <--- Forza la posición horizontal
        labelFontSize=12       # Opcional: reduce un poco la letra si los meses chocan
    )
    
    st.altair_chart(chart, use_container_width=True)

def grafica_vendedores_altair(df):
    # Sumamos todos sin filtrar Top 10
    data = df.groupby('vendedor', as_index=False)['facturas_canceladas'].sum()
    
    # Ajustamos altura dinámica: 20px por cada vendedor para que no se amontonen
    altura = max(300, len(data) * 20)

    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('facturas_canceladas:Q', title="Total Facturas"),
        y=alt.Y('vendedor:N', sort='-x', title="Vendedor"),
        color=alt.Color('facturas_canceladas:Q', scale=alt.Scale(scheme='reds'), legend=None),
        tooltip=[
            alt.Tooltip('vendedor:N', title='Nombre del Vendedor'),
            alt.Tooltip('facturas_canceladas:Q', title='Facturas canceladas', format='.0f')
        ]
    ).properties(
        title="Cancelaciones por Vendedor (Total)",
        height=altura
    ).configure_axisY(
        labelLimit=300,  # <--- Aumenta el límite de píxeles para el nombre (ajusta según necesites)
        labelFontSize=12
    )
    
    st.altair_chart(chart, use_container_width=True)

def grafica_clientes_altair(df):
    # 1. Identificamos los 30 clientes que más suman en total
    top_30_nombres = (
        df.groupby('Cliente')['facturas_canceladas']
        .sum()
        .nlargest(30)
        .index
    )
    
    # 2. Filtramos el dataframe original para tener el detalle de esos 30
    df_top = df[df['Cliente'].isin(top_30_nombres)]
    
    # 3. Agrupamos por Cliente y Condición para la gráfica
    data = df_top.groupby(['Cliente', 'condicion_venta'], as_index=False)['facturas_canceladas'].sum()

    chart = alt.Chart(data).mark_bar().encode(
        # sort='-y' ordena por la suma total de las barras
        x=alt.X('Cliente:N', sort='-y', title="Cliente (Top 30)"),
        y=alt.Y('facturas_canceladas:Q', title="Facturas"),
        color=alt.Color('condicion_venta:N', title="Condición"),
        tooltip=['Cliente', 'condicion_venta', 'facturas_canceladas']
    ).properties(
        title="Top 30 Clientes con más Cancelaciones",
        height=450
    )

    # Aplicamos la configuración de los ejes por separado para evitar errores de concatenación
    st.altair_chart(
        chart.configure_axisX(
            labelAngle=-45, 
            labelOverlap=False,  # <--- Esto obliga a mostrar todos los nombres
            labelFontSize=10,    # Un poco más pequeña para que quepan
            labelLimit=200       # Evita que se corten si son muy largos hacia abajo
        ), 
        use_container_width=True
    )

def grafica_proveedores_altair(df):
    # 1. Identificamos los 30 proveedores que más suman en total
    top_30_nombres = (
        df.groupby('Proveedor')['facturas_canceladas']
        .sum()
        .nlargest(30)
        .index
    )
    
    # 2. Filtramos el dataframe original
    df_top = df[df['Proveedor'].isin(top_30_nombres)]
    
    # 3. Agrupamos
    data = df_top.groupby(['Proveedor', 'condicion_venta'], as_index=False)['facturas_canceladas'].sum()
    
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('Proveedor:N', sort='-y', title="Proveedor (Top 30)"),
        y=alt.Y('facturas_canceladas:Q', title="Facturas"),
        color=alt.Color('condicion_venta:N', scale=alt.Scale(scheme='category10'), title="Condición"),
        tooltip=['Proveedor', 'condicion_venta', 'facturas_canceladas']
    ).properties(
        title="Top 30 Proveedores con más Cancelaciones",
        height=450
    )

    st.altair_chart(
        chart.configure_axisX(
            labelAngle=-45, 
            labelOverlap=False,  # <--- Esto obliga a mostrar todos los nombres
            labelFontSize=10,    # Un poco más pequeña para que quepan
            labelLimit=200       # Evita que se corten si son muy largos hacia abajo
        ), 
        use_container_width=True
    )

def mostrar(config):
    st.title("Cancelaciones")
    
    df_raw = cargar_datos()
    if df_raw is None: return

    df_filtrado, sucursal_label = filtrar_datos(df_raw)
    
    # Métricas principales
    total_f = df_filtrado['facturas_canceladas'].sum()
    st.metric(f"Total Facturas Canceladas ({sucursal_label})", f"{total_f:,.0f}")

    st.markdown("---")
    

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