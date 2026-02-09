import streamlit as st
import plotly.express as px
import pandas as pd
import datetime
import altair as alt
import pandas as pd
from utils.api_utils import obtener_vista
from utils.table_utils import mostrar_tabla_normal_cloud


# ======================================================
# 1️⃣ CARGA DE DATOS (API → DF)
# ======================================================
@st.cache_data(ttl=86400)
def cargar_datos_lineas_completo():
    try:
        df_suc = obtener_vista("vw_dashboard_metas_sucursal_por_linea")
        df_ven = obtener_vista("vw_dashboard_metas_por_linea")
        df_pro = obtener_vista("vw_dashboard_venta_linea_proveedor")
        return df_suc, df_ven, df_pro
    except Exception as e:
        st.error(f"Error al conectar con la API: {e}")
        return None, None, None

# ======================================================
# 2️⃣ LÓGICA DE FILTRADO
# ======================================================
def filtrar_datos(df, linea, anio, mes, sucursal):
    mask = (df['anio'] == anio)
    if linea != "TODAS":
        mask = mask & (df['linea'] == linea)
    if mes != "TODOS":
        mask = mask & (df['mes_nombre'] == mes)
    if sucursal != "TODAS":
        mask = mask & (df['sucursal'] == sucursal)
    return df[mask]

# ======================================================
# 3️⃣ COMPONENTES DE INTERFAZ (UI)
# ======================================================

def renderizar_filtros(df_sucursal):
    """Crea la fila de selectores y devuelve los valores seleccionados con orden cronológico."""
    st.markdown("### Filtros de Consulta")
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        lista_lineas = ["TODAS"] + sorted(df_sucursal['linea'].unique().tolist())
        linea_sel = st.selectbox("Línea", lista_lineas)

    # DataFrame de referencia para filtros dependientes
    df_ref = df_sucursal if linea_sel == "TODAS" else df_sucursal[df_sucursal['linea'] == linea_sel]

    with f2:
        lista_anios = sorted(df_ref['anio'].unique(), reverse=True)
        anio_sel = st.selectbox("Año", lista_anios)

    with f3:
        # --- Lógica de ordenamiento cronológico ---
        # Filtramos por el año seleccionado y tomamos los pares (mes, mes_nombre) únicos
        df_meses = df_ref[df_ref['anio'] == anio_sel][['mes', 'mes_nombre']].drop_duplicates()
        
        # Ordenamos por el número del mes (1, 2, 3...)
        df_meses = df_meses.sort_values('mes')
        
        # Extraemos la lista de nombres ya ordenados
        meses_disp = df_meses['mes_nombre'].tolist()
        
        mes_sel = st.selectbox("Mes", ["TODOS"] + meses_disp, index=0)

    with f4:
        lista_sucs = ["TODAS"] + sorted(df_ref['sucursal'].unique().tolist())
        sucursal_sel = st.selectbox("Sucursal", lista_sucs)

    return linea_sel, anio_sel, mes_sel, sucursal_sel

def renderizar_kpis(df, linea_nombre):
    """Muestra tarjetas de KPI personalizadas con títulos simplificados."""
    
    # Cálculos base
    total_venta = df['venta_real'].sum()
    utilidad = df['utilidad_real'].sum()
    margen_prom = (utilidad / total_venta) * 100 if total_venta > 0 else 0
    
    # Lógica de Meta y Cumplimiento
    if linea_nombre != "TODAS":
        total_meta = df['meta_sucursal_linea'].sum()
        if total_meta > 0:
            cumplimiento = (total_venta / total_meta) * 100
            meta_txt = f"${total_meta:,.2f}"
            cump_txt = f"{cumplimiento:.1f}%"
            
            # Colores del semáforo
            if cumplimiento >= 95: color_cump = "#28a745" # Verde
            elif cumplimiento >= 80: color_cump = "#ffc107" # Amarillo
            else: color_cump = "#dc3545" # Rojo
        else:
            meta_txt = "Sin meta"
            cump_txt = "Sin cumplimiento"
            color_cump = "#6c757d" # Gris
    else:
        meta_txt = "Sin meta"
        cump_txt = "Sin cumplimiento"
        color_cump = "#6c757d"

    # Estilo CSS (se mantiene igual, es muy sólido)
    st.markdown("""
        <style>
        .kpi-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
            border-left: 5px solid #007bff;
            margin-bottom: 10px;
        }
        .kpi-title { font-size: 13px; color: #6c757d; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
        .kpi-value { font-size: 22px; color: #212529; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""<div class="kpi-card" style="border-left-color: #007bff;">
            <div class="kpi-title">VENTA TOTAL</div>
            <div class="kpi-value">${total_venta:,.2f}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""<div class="kpi-card" style="border-left-color: #6c757d;">
            <div class="kpi-title">META</div>
            <div class="kpi-value">{meta_txt}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="kpi-card" style="border-left-color: {color_cump};">
            <div class="kpi-title">CUMPLIMIENTO</div>
            <div class="kpi-value" style="color: {color_cump};">{cump_txt}</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        # Color cian para el margen
        st.markdown(f"""<div class="kpi-card" style="border-left-color: #17a2b8;">
            <div class="kpi-title">MARGEN</div>
            <div class="kpi-value">{margen_prom:.1f}%</div>
        </div>""", unsafe_allow_html=True)

def grafico_barras_lineas(df, linea_sel):
    """Gráfico de barras horizontales estilizado con alto dinámico y tooltips limpios."""
    st.subheader(f"Resumen de Ventas por Línea")
    
    # Agrupación y orden
    df_g = df.groupby('linea')['venta_real'].sum().reset_index().sort_values('venta_real', ascending=True)
    
    # --- AJUSTE DINÁMICO DE ALTURA ---
    # Calculamos el alto: mínimo 300px, y sumamos 30px por cada línea adicional
    num_lineas = len(df_g)
    alto_dinamico = max(300, num_lineas * 35)

    fig = px.bar(
        df_g, 
        x='venta_real', 
        y='linea', 
        orientation='h',
        text='venta_real', # Usamos text en lugar de text_auto para formatearlo manualmente
        color='venta_real', 
        color_continuous_scale='Blues',
        labels={'venta_real': 'Venta Real', 'linea': 'Línea'}
    )

    # --- ESTILIZADO DE TOOLTIP Y BARRAS ---
    fig.update_traces(
        texttemplate='%{text:$,.2f}', # Formato moneda: $1,234
        textposition='outside',       # Montos fuera de la barra para que no se amontonen
        cliponaxis=False,             # Evita que el texto se corte
        hovertemplate="<b>Línea:</b> %{y}<br>" +
                      "<b>Venta:</b> %{x:$,.2f}<br>" +
                      "<extra></extra>", # Quita la leyenda extra de la derecha
        marker_line_color='rgb(8,48,107)', # Borde sutil a las barras
        marker_line_width=1.5,
        opacity=0.8
    )

    # --- DISEÑO (LAYOUT) ---
    fig.update_layout(
        height=alto_dinamico,
        margin=dict(l=10, r=50, t=30, b=10), # Margen derecho extra para el texto
        xaxis=dict(
            showgrid=True, 
            gridcolor='rgba(200, 200, 200, 0.2)', # Cuadrícula tenue
            title=None
        ),
        yaxis=dict(title=None),
        coloraxis_showscale=False, # Ocultamos la barra de colores para ganar espacio
        # bargap controla el ancho de la barra. 
        # Si hay solo una, ponemos un gap grande (0.8) para que no sea ancha.
        bargap=0.4 if num_lineas > 1 else 0.8 
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def graficos_secundarios(df_suc, df_prov):
    """Renderiza gráficos con altura dinámica y barras estilizadas."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Venta por Sucursal")
        df_s = df_suc.groupby('sucursal')['venta_real'].sum().reset_index().sort_values('venta_real', ascending=True)
        
        # --- AJUSTE DINÁMICO ---
        num_sucs = len(df_s)
        # Altura fija de 400 suele ser mucha para 1 o 2 sucursales
        alto_suc = max(250, num_sucs * 40) 
        
        max_x = df_s['venta_real'].max() * 1.25 if not df_s.empty else 100

        fig_suc = px.bar(
            df_s, x='venta_real', y='sucursal', orientation='h',
            text='venta_real', color='venta_real', color_continuous_scale='Viridis'
        )
        
        fig_suc.update_traces(
            texttemplate='%{text:$,.2f}',
            textposition='outside', 
            cliponaxis=False,
            hovertemplate="<b>Sucursal:</b> %{y}<br>" +
                          "<b>Venta:</b> %{x:$,.2f}<br>" +
                          "<extra></extra>"
        )

        fig_suc.update_layout(
            height=alto_suc, 
            showlegend=False, 
            coloraxis_showscale=False,
            margin=dict(l=10, r=80, t=30, b=10),
            xaxis=dict(range=[0, max_x], showgrid=False, visible=False),
            yaxis=dict(title=None),
            # Si hay pocas sucursales, aumentamos el hueco para que la barra sea delgada
            bargap=0.4 if num_sucs > 1 else 0.8 
        )
        st.plotly_chart(fig_suc, use_container_width=True, config={'displayModeBar': False})
        
    with col2:
        # 1. Actualizamos el título y el parámetro de nlargest
        st.subheader("Top 15 Proveedores")
        df_p = df_prov.groupby('Proveedor')['venta_real'].sum().nlargest(15).reset_index().sort_values('venta_real', ascending=True)
        
        # --- AJUSTE DINÁMICO ---
        num_provs = len(df_p)
        # Reducimos a 35 para que 15 barras queden compactas y elegantes
        alto_prov = max(250, num_provs * 35)
        
        max_x_p = df_p['venta_real'].max() * 1.25 if not df_p.empty else 100

        fig_p = px.bar(df_p, x='venta_real', y='Proveedor', orientation='h', text='venta_real')
        
        fig_p.update_traces(
            marker_color='#00CC96', 
            opacity=0.8, 
            texttemplate='%{text:$,.2f}',
            textposition='outside', 
            cliponaxis=False,
            hovertemplate="<b>Proveedor:</b> %{y}<br>" +
                          "<b>Venta:</b> %{x:$,.2f}<br>" +
                          "<extra></extra>"
        )
        
        fig_p.update_layout(
            height=alto_prov,
            margin=dict(l=10, r=80, t=30, b=10),
            xaxis=dict(range=[0, max_x_p], showgrid=False, visible=False),
            yaxis=dict(title=None),
            # Mantenemos el bargap para que las barras no se vean gordas si hay pocas
            bargap=0.4 if num_provs > 1 else 0.8
        )
        
        st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})

    # --- NOTA ACLARATORIA ---
    st.caption("⚠️ **Nota:** En el caso particular de los proveedores de la línea de llantas, "
               "aparece el monto participante de **John Deere Sales Hispanoamérica**, "
               "pero este monto no suma a las métricas de venta por sucursal y vendedor.")

def renderizar_tablas_detalle(df_suc_f, df_prov_f):
    """Muestra tablas con comas forzadas convirtiendo los valores a string formateado."""
    
    ahora = datetime.datetime.now()
    mes_actual = ahora.month
    anio_actual = ahora.year

    # --- TABLA POR SUCURSAL ---
    with st.expander("Ver detalle de ventas por sucursal"):
        columnas_suc = {
            "periodo_jd": "Periodo",
            "sucursal": "Sucursal",
            "venta_real": "Venta",
            "costo_real": "Costo",
            "utilidad_real": "Utilidad",
            "margen_real": "Margen %"
        }
        
        df_suc_tabla = df_suc_f.groupby(['anio', 'mes', 'periodo_jd', 'sucursal']).agg({
            'venta_real': 'sum',
            'costo_real': 'sum',
            'utilidad_real': 'sum',
            'margen_real': 'mean'
        }).reset_index()

        # Filtro de meses futuros
        df_suc_tabla = df_suc_tabla[~((df_suc_tabla['anio'] == anio_actual) & (df_suc_tabla['mes'] > mes_actual))]
        df_suc_tabla = df_suc_tabla.sort_values(['anio', 'mes', 'sucursal'])

        # --- TRUCO: FORMATEO MANUAL A STRING CON COMAS ---
        # Esto garantiza que se vea la coma sin el signo $
        for col in ['venta_real', 'costo_real', 'utilidad_real']:
            df_suc_tabla[col] = df_suc_tabla[col].apply(lambda x: f"{x:,.2f}")
        
        # Formateamos el margen también por si acaso
        df_suc_tabla['margen_real'] = df_suc_tabla['margen_real'].apply(lambda x: f"{x:.2f}%")

        df_final_suc = df_suc_tabla[list(columnas_suc.keys())].rename(columns=columnas_suc)

        st.dataframe(
            df_final_suc,
            use_container_width=True,
            hide_index=True
            # Ya no necesitamos column_config complejo porque ya son strings perfectos
        )

    # --- TABLA POR PROVEEDOR ---
    with st.expander("Ver detalle de proveedores"):
        columnas_prov = {
            "periodo_jd": "Periodo",
            "Proveedor": "Proveedor",
            "venta_real": "Venta",
            "costo_real": "Costo",
            "utilidad_real": "Utilidad",
            "margen_real": "Margen %"
        }

        df_prov_tabla = df_prov_f.groupby(['anio', 'mes', 'periodo_jd', 'Proveedor']).agg({
            'venta_real': 'sum',
            'costo_real': 'sum',
            'utilidad_real': 'sum',
            'margen_real': 'mean'
        }).reset_index()

        df_prov_tabla = df_prov_tabla[~((df_prov_tabla['anio'] == anio_actual) & (df_prov_tabla['mes'] > mes_actual))]
        df_prov_tabla = df_prov_tabla.sort_values(['anio', 'mes', 'venta_real'], ascending=[True, True, False])

        # --- FORMATEO MANUAL ---
        for col in ['venta_real', 'costo_real', 'utilidad_real']:
            df_prov_tabla[col] = df_prov_tabla[col].apply(lambda x: f"{x:,.2f}")
        
        df_prov_tabla['margen_real'] = df_prov_tabla['margen_real'].apply(lambda x: f"{x:.2f}%")

        df_final_prov = df_prov_tabla[list(columnas_prov.keys())].rename(columns=columnas_prov)

        st.dataframe(
            df_final_prov,
            use_container_width=True,
            hide_index=True
        )

def renderizar_grafico_vendedores(df_vendedores, linea_sel, mes_sel):
    if df_vendedores.empty:
        st.warning("No hay datos disponibles para los filtros seleccionados.")
        return

    df_grafico = df_vendedores.copy()
    
    # 1. Limpieza y Normalización
    df_grafico["meta_vendedor_linea"] = df_grafico["meta_vendedor_linea"].fillna(0)
    df_grafico["semaforo"] = df_grafico["semaforo"].replace({"SIN META": "SIN_META"}).fillna("SIN_META")
    df_grafico["etiqueta_vendedor"] = df_grafico["linea"] + " - " + df_grafico["vendedor"]

    # Agrupamos por vendedor
    df_grafico = df_grafico.groupby("etiqueta_vendedor").agg({
        "venta_real": "sum",
        "meta_vendedor_linea": "sum",
        "semaforo": "first"
    }).reset_index()

    # Recalcular cumplimiento
    df_grafico["porcentaje_cumplimiento"] = (df_grafico["venta_real"] / df_grafico["meta_vendedor_linea"]) * 100
    df_grafico.loc[df_grafico["meta_vendedor_linea"] == 0, "porcentaje_cumplimiento"] = 0
    
    def definir_semaforo_global(row):
        if row["meta_vendedor_linea"] == 0: return "SIN_META"
        cumplimiento = row["porcentaje_cumplimiento"]
        if cumplimiento >= 95: return "VERDE"
        if cumplimiento >= 85: return "AMARILLO"
        return "ROJO"
    
    if mes_sel == "TODOS":
        df_grafico["semaforo"] = df_grafico.apply(definir_semaforo_global, axis=1)

    # --- LÓGICA DE ORDENAMIENTO ESTÉTICO ---
    # 1. Prioridad: ¿Tiene meta? (True/False)
    # 2. Si tiene meta: Ordenar por Meta descendente
    # 3. Si NO tiene meta: Ordenar por Venta descendente
    df_grafico["tiene_meta"] = df_grafico["meta_vendedor_linea"] > 0
    df_grafico = df_grafico.sort_values(
        by=["tiene_meta", "meta_vendedor_linea", "venta_real"], 
        ascending=[False, False, False]
    )
    
    # Creamos una lista para que Altair respete este orden exacto
    orden_vendedores = df_grafico["etiqueta_vendedor"].tolist()

    # 2. Configuración de colores
    color_scale = alt.Scale(
        domain=["ROJO", "AMARILLO", "VERDE", "SIN_META"],
        range=["#DC3545", "#FFC107", "#28A745", "#1f77b4"]
    )

    # 3. Capa de la META
    meta_bar = (
        alt.Chart(df_grafico)
        .mark_bar(color="#F5F5F5", size=24, cornerRadiusEnd=2)
        .encode(
            y=alt.Y("etiqueta_vendedor:N", 
                    sort=orden_vendedores, # Usamos la lista ordenada
                    title=None,
                    axis=alt.Axis(labelLimit=1000)), # Evita que se corten los nombres
            x=alt.X("meta_vendedor_linea:Q", title="Monto ($)"),
            tooltip=[
                alt.Tooltip("etiqueta_vendedor:N", title="Vendedor"),
                alt.Tooltip("meta_vendedor_linea:Q", title="Meta Total", format=",.2f"),
            ],
        )
    )

    # 4. Capa de la VENTA
    venta_bar = (
        alt.Chart(df_grafico)
        .mark_bar(size=14, cornerRadiusEnd=2)
        .encode(
            y=alt.Y("etiqueta_vendedor:N", sort=orden_vendedores),
            x=alt.X("venta_real:Q"),
            color=alt.Color("semaforo:N", scale=color_scale, legend=None),
            tooltip=[
                alt.Tooltip("etiqueta_vendedor:N", title="Vendedor"),
                alt.Tooltip("venta_real:Q", title="Venta", format=",.2f"),
                alt.Tooltip("porcentaje_cumplimiento:Q", title="% Cumplimiento", format=".1f"),
            ],
        )
    )

    # 5. Combinar
    chart = (meta_bar + venta_bar).properties(
        height=max(350, len(df_grafico) * 40)
    ).configure_axis(
        labelFontSize=11,
        titleFontSize=12
    ).configure_view(strokeOpacity=0)

    st.subheader(f"Cumplimiento por Vendedor – {linea_sel} ({mes_sel})")
    st.altair_chart(chart, use_container_width=True)

def renderizar_tabla_vendedores(df_vendedores):
    """
    Prepara y muestra la tabla de rendimiento de vendedores usando la utilidad centralizada.
    """
    if df_vendedores.empty:
        return

    # 1. Agrupación y preparación de datos
    # Agrupamos por vendedor para consolidar si hay registros duplicados por alguna razón
    df_tabla = df_vendedores.groupby('vendedor').agg({
        'meta_vendedor_linea': 'sum',
        'venta_real': 'sum',
        'costo_real': 'sum',
        'utilidad_real': 'sum',
        'margen_real': 'mean', # El margen se promedia
        'porcentaje_cumplimiento': 'mean', # El cumplimiento se promedia (o se puede recalcular)
        'semaforo': 'first'    # Tomamos el estado del semáforo
    }).reset_index()

    # 2. Renombrar columnas para la función mostrar_tabla_normal_cloud
    df_tabla = df_tabla.rename(columns={
        "vendedor": "Vendedor",
        "meta_vendedor_linea": "Meta",
        "venta_real": "Venta",
        "costo_real": "Costo",
        "utilidad_real": "Utilidad",
        "margen_real": "Margen %",
        "porcentaje_cumplimiento": "% Cumplimiento",
        "semaforo": "Semáforo"
    })

    # 3. Llamada a la utilidad de tabla
    st.write("#### Detalle Numérico por Vendedor")
    mostrar_tabla_normal_cloud(
        df_tabla,
        columnas_fijas=["Vendedor"],
        columnas_numericas=["Meta", "Venta", "Costo", "Utilidad", "Margen %", "% Cumplimiento"],
        #columnas_sin_degradado=["Margen %"], # A veces el margen confunde con degradado
        columna_total="Venta",
        resaltar_primera_columna=True,
        ordenar_por="Venta",
        ascendente=False
    )


# ======================================================
# 4️⃣ ORQUESTADOR PRINCIPAL
# ======================================================
def mostrar(config):
    st.title("Ventas por Línea")
    
    # 1. Carga
    df_sucursal, df_vendedor, df_prov = cargar_datos_lineas_completo()
    if df_sucursal is None or df_sucursal.empty:
        st.warning("No hay datos disponibles.")
        return

    # 2. Filtros
    linea_sel, anio_sel, mes_sel, sucursal_sel = renderizar_filtros(df_sucursal)

    # 3. Procesamiento (AQUÍ FILTRAMOS LAS TRES VISTAS)
    df_s_f = filtrar_datos(df_sucursal, linea_sel, anio_sel, mes_sel, sucursal_sel)
    df_p_f = filtrar_datos(df_prov, linea_sel, anio_sel, mes_sel, sucursal_sel)
    # Creamos la variable que te faltaba:
    df_v_f = filtrar_datos(df_vendedor, linea_sel, anio_sel, mes_sel, sucursal_sel)

    if df_s_f.empty:
        st.info("No se encontraron registros para la selección actual.")
        return

    st.divider()

    # 4. Visualización
    # Gráfico de barras principal (Venta por Línea)
    grafico_barras_lineas(df_s_f, linea_sel)
    
    #st.divider()
    
    # Números clave (Tarjetas)
    renderizar_kpis(df_s_f, linea_sel)
    

    # --- NUEVA SECCIÓN: CUMPLIMIENTO DE VENDEDORES ---
    # Es recomendable ponerlo antes de las tablas de detalle
    #renderizar_grafico_vendedores(df_v_f, linea_sel, mes_sel)

    # Gráficos de Sucursal y Proveedores (los que hicimos con barras horizontales)
    graficos_secundarios(df_s_f, df_p_f)
    
    # Tablas de detalle (las que formateamos con comas y sin $)
    renderizar_tablas_detalle(df_s_f, df_p_f)

    if linea_sel != "TODAS":
        # Mostramos el gráfico que ya tenías
        renderizar_grafico_vendedores(df_v_f, linea_sel, mes_sel)
        
        # Agregamos la nueva tabla debajo en un expander para limpieza visual
        with st.expander("Ver tabla de cumplimiento por vendedor"):
            renderizar_tabla_vendedores(df_v_f)
    else:
        st.subheader("Cumplimiento por Vendedor")
        st.info("**Selecciona una Línea específica** para ver el ranking de vendedores y su detalle de cumplimiento.")
        
    

