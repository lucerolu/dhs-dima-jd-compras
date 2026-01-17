# secciones/ventas.py

import streamlit as st
import pandas as pd
import altair as alt

from utils.api_utils import obtener_vista
from utils.table_utils import mostrar_tabla_normal
from utils.table_utils import mostrar_tabla_matriz


def render_descripcion():
    st.markdown(
        """
        **Resumen de ventas JD**
        
        - Acumulado del año fiscal (empezando desde noviembre)
        - No incluye venta de refacciones de servicio
        """
    )

def cargar_datos():
    df = obtener_vista("vw_facturacion_sucursal_mes_jd")
    df_meta = obtener_vista("vw_dashboard_meta_sucursal")

    if df.empty:
        st.warning("No hay datos disponibles para ventas.")
        return None, None

    if df_meta.empty:
        st.warning("No hay datos de metas disponibles.")
        return None, None

    df["venta_real"] = pd.to_numeric(df["venta_real"], errors="coerce").fillna(0)

    return df, df_meta

def preparar_anio_fiscal(df, df_meta):
    anio_fiscal_actual = df["anio_fiscal_jd"].max()

    df_fiscal = df[df["anio_fiscal_jd"] == anio_fiscal_actual]

    df_meta_fiscal = df_meta[
        df_meta["anio_fiscal_jd"] == anio_fiscal_actual
    ].copy()

    df_meta_fiscal["venta_real"] = pd.to_numeric(
        df_meta_fiscal["venta_real"], errors="coerce"
    ).fillna(0)

    df_meta_fiscal["meta"] = pd.to_numeric(
        df_meta_fiscal["meta"], errors="coerce"
    ).fillna(0)

    return df_fiscal, df_meta_fiscal, anio_fiscal_actual

def preparar_mensual(df_fiscal, df_meta_fiscal):
    mensual = (
        df_fiscal
        .groupby(
            ["anio_fiscal_jd", "orden_mes_fiscal", "periodo_jd"],
            as_index=False
        )
        .agg({
            "venta_real": "sum",
            "costo_real": "sum",
            "utilidad_real": "sum"
        })
        .sort_values("orden_mes_fiscal")
    )

    mensual["margen_pct"] = (
        mensual["utilidad_real"] / mensual["venta_real"] * 100
    ).where(mensual["venta_real"] > 0)

    meta_mensual = (
        df_meta_fiscal
        .groupby("periodo_jd", as_index=False)
        .agg({
            "venta_real": "sum",
            "meta": "sum"
        })
    )

    meta_mensual["cumplimiento_meta_pct"] = (
        meta_mensual["venta_real"] / meta_mensual["meta"] * 100
    ).where(meta_mensual["meta"] > 0)

    mensual = mensual.merge(
        meta_mensual[[
            "periodo_jd",
            "meta",
            "cumplimiento_meta_pct"
        ]],
        on="periodo_jd",
        how="left"
    )

    return mensual


def render_kpis(mensual, anio_fiscal_actual):
    venta_acumulada = mensual["venta_real"].sum()
    mes_actual = mensual.iloc[-1]
    venta_mes_actual = mes_actual["venta_real"]

    if len(mensual) > 1:
        venta_mes_anterior = mensual.iloc[-2]["venta_real"]
        variacion_pct = (
            (venta_mes_actual - venta_mes_anterior)
            / venta_mes_anterior * 100
            if venta_mes_anterior > 0 else None
        )
    else:
        variacion_pct = None

    # Contenedor principal
    with st.container():
        st.markdown(
            """
            <style>
            .kpi-card {
                background-color: #f5f5f5;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            .kpi-label {
                font-size: 16px;
                color: #555;
                margin-bottom: 5px;
            }
            .kpi-value {
                font-size: 28px;
                font-weight: bold;
                color: #111;
            }
            .kpi-delta {
                font-size: 28px;
                color: #1E7E34;  /* verde por defecto */
            }
            .kpi-delta.neg {
                color: #DC3545;  /* rojo si es negativo */
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns(3, gap="medium")

        # Venta acumulada
        col1.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">💰 Venta acumulada al año {anio_fiscal_actual}</div>
                <div class="kpi-value">${venta_acumulada:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)

        # Venta mes actual
        col2.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">📅 Venta mes actual ({mes_actual['periodo_jd']})</div>
                <div class="kpi-value">${venta_mes_actual:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)

        # Variación vs mes anterior
        if variacion_pct is None:
            delta_html = "—"
        else:
            color_class = "neg" if variacion_pct < 0 else ""
            delta_html = f'<span class="kpi-delta {color_class}">{variacion_pct:,.2f} %</span>'

        col3.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">📊 Variación vs mes anterior</div>
                <div class="kpi-value">{delta_html}</div>
            </div>
        """, unsafe_allow_html=True)



def grafica_venta_vs_meta(mensual):
    st.subheader("📈 Venta vs Meta por mes")
    grafica_df = mensual[[
        "periodo_jd",
        "venta_real",
        "meta",
        "cumplimiento_meta_pct"
    ]].dropna(subset=["meta"])


    grafica_long = grafica_df.melt(
        id_vars=["periodo_jd", "cumplimiento_meta_pct"],
        value_vars=["venta_real", "meta"],
        var_name="Tipo",
        value_name="Monto"
    )

    grafica_long["Tipo"] = grafica_long["Tipo"].map({
        "venta_real": "Venta real",
        "meta": "Meta"
    })

    chart = (
        alt.Chart(grafica_long)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "periodo_jd:N",
                title="Periodo",
                sort=list(mensual["periodo_jd"]),
                axis=alt.Axis(labelAngle=0)
            ),
            y=alt.Y(
                "Monto:Q",
                title="Monto ($)"
            ),
            color=alt.Color(
                "Tipo:N",
                legend=alt.Legend(title="")
            ),
            tooltip=[
                alt.Tooltip("periodo_jd:N", title="Periodo"),
                alt.Tooltip("Tipo:N", title="Tipo"),
                alt.Tooltip("Monto:Q", title="Monto", format=",.2f"),
                alt.Tooltip(
                    "cumplimiento_meta_pct:Q",
                    title=" Cumplimiento (%)",
                    format=".2f"
                )
            ]
        )
        .properties(height=420)
    )

    st.altair_chart(chart, use_container_width=True)


def tabla_ventas_mes_a_mes(mensual):
    mensual["% Variación"] = mensual["venta_real"].pct_change() * 100

    tabla = mensual[[
        "periodo_jd",
        "venta_real",
        "meta",
        "costo_real",
        "utilidad_real",
        "margen_pct",
        "% Variación",
        "cumplimiento_meta_pct"
    ]].rename(columns={
        "periodo_jd": "Periodo",
        "venta_real": "Venta",
        "meta": "Meta",
        "costo_real": "Costo",
        "utilidad_real": "Utilidad",
        "margen_pct": "Margen %",
        "cumplimiento_meta_pct": "% Cumplimiento Meta"
    })

    st.subheader("📊 Ventas mes a mes")

    mostrar_tabla_normal(
        df=tabla,
        columnas_fijas=["Periodo"],
        columnas_numericas=[
            "Venta",
            "Meta",
            "Costo",
            "Utilidad",
            "Margen %",
            "% Variación",
            "% Cumplimiento Meta"
        ],
        height=520
    )

    

def grafica_meta_horizontal(mensual):
    st.subheader("🎯 Cumplimiento de meta global por mes")

    # Copiamos el DF mensual
    grafica_mes = mensual.copy()

    grafica_mes = grafica_mes[[
        "periodo_jd",
        "venta_real",
        "meta",
        "cumplimiento_meta_pct",
        "orden_mes_fiscal"  # añadimos para ordenar correctamente
    ]].dropna(subset=["meta"])

    # Ordenamos según la tabla
    grafica_mes = grafica_mes.sort_values("orden_mes_fiscal")

    # Regla de color estilo semáforo
    grafica_mes["color"] = grafica_mes["cumplimiento_meta_pct"].apply(
        lambda x: "VERDE" if x >= 100 else "AMARILLO" if x >= 90 else "ROJO"
    )

    # Escala de colores
    color_scale = alt.Scale(
        domain=["ROJO", "AMARILLO", "VERDE"],
        range=["#DC3545", "#FFC107", "#1E7E34"]
    )

    # Barra de META (fondo gris) más delgada
    meta_bar = (
        alt.Chart(grafica_mes)
        .mark_bar(color="#E0E0E0", opacity=0.7, size=26)  # size más delgado
        .encode(
            y=alt.Y("periodo_jd:N", sort=list(grafica_mes["periodo_jd"]), title="Mes"),
            x=alt.X("meta:Q", title="Monto ($)"),
            tooltip=[
                alt.Tooltip("periodo_jd:N", title="Mes"),
                alt.Tooltip("meta:Q", title="Meta", format=",.2f")
            ]
        )
    )

    # Barra de CUMPLIMIENTO (venta real)
    venta_bar = (
        alt.Chart(grafica_mes)
        .mark_bar(size=18)
        .encode(
            y=alt.Y("periodo_jd:N", sort=list(grafica_mes["periodo_jd"])),
            x=alt.X("venta_real:Q"),
            color=alt.Color("color:N", scale=color_scale, legend=None),
            tooltip=[
                alt.Tooltip("periodo_jd:N", title="Mes"),
                alt.Tooltip("venta_real:Q", title="Venta", format=",.2f"),
                alt.Tooltip("cumplimiento_meta_pct:Q", title="Cumplimiento (%)", format=".2f")
            ]
        )
    )

    # Combinamos las barras
    chart = (
        (meta_bar + venta_bar)
        .properties(height=max(320, len(grafica_mes) * 38))
    )

    st.altair_chart(chart, use_container_width=True)


def grafica_venta_sucursal_vs_meta(df_meta_fiscal):
    st.subheader("🏬 Venta por sucursal vs meta")

    sucursales = sorted(df_meta_fiscal["sucursal"].dropna().unique())
    sucursal_sel = st.selectbox(
        "Selecciona una sucursal",
        sucursales,
        key="sucursal_venta_meta"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    df_sucursal = df_meta_fiscal[
        df_meta_fiscal["sucursal"] == sucursal_sel
    ]

    mensual_sucursal = (
        df_sucursal
        .groupby(
            ["periodo_jd", "orden_mes_fiscal"],
            as_index=False
        )
        .agg({
            "venta_real": "sum",
            "meta": "sum"
        })
        .sort_values("orden_mes_fiscal")
    )

    mensual_sucursal["cumplimiento_meta_pct"] = (
        mensual_sucursal["venta_real"]
        / mensual_sucursal["meta"].replace(0, None)
        * 100
    )

    grafica_long = mensual_sucursal.melt(
        id_vars=["periodo_jd", "cumplimiento_meta_pct"],
        value_vars=["venta_real", "meta"],
        var_name="Tipo",
        value_name="Monto"
    )

    grafica_long["Tipo"] = grafica_long["Tipo"].map({
        "venta_real": "Venta",
        "meta": "Meta"
    })

    chart = (
        alt.Chart(grafica_long)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "periodo_jd:N",
                sort=list(mensual_sucursal["periodo_jd"]),
                axis=alt.Axis(labelAngle=0),
                title="Periodo"
            ),
            y=alt.Y(
                "Monto:Q",
                title="Monto ($)"
            ),
            color=alt.Color(
                "Tipo:N",
                legend=alt.Legend(title="")
            ),
            tooltip=[
                alt.Tooltip("periodo_jd:N", title="Periodo"),
                alt.Tooltip("Tipo:N", title="Tipo"),
                alt.Tooltip("Monto:Q", title="Monto", format=",.2f"),
                alt.Tooltip("% Cumplimiento Meta:Q", title="Cumplimiento (%)", format=".2f")
            ]
        )
        .properties(height=420)
    )

    st.altair_chart(chart, use_container_width=True)
    #return mensual_sucursal


def matriz_ventas_sucursal(df_fiscal):
    st.subheader("📊 Venta mensual por sucursal")

    ventas_sucursal_mes = (
        df_fiscal
        .groupby(
            ["orden_mes_fiscal", "periodo_jd", "sucursal"],
            as_index=False
        )
        .agg({"venta_real": "sum"})
    )

    matriz = (
        ventas_sucursal_mes
        .pivot(
            index=["orden_mes_fiscal", "periodo_jd"],
            columns="sucursal",
            values="venta_real"
        )
        .fillna(0)
        .reset_index()
        .sort_values("orden_mes_fiscal")
    )

    matriz = matriz.drop(columns=["orden_mes_fiscal"])

    # ➜ Cambiar nombre visual de la columna
    matriz = matriz.rename(columns={"periodo_jd": "Mes"})

    data_columns = [c for c in matriz.columns if c != "Mes"]

    # TOTAL por fila
    matriz["Total"] = matriz[data_columns].sum(axis=1)

    # TOTAL por columna (footer)
    footer_totals = {
        "Mes": "TOTAL",
        **{col: matriz[col].sum() for col in data_columns},
        "Total": matriz["Total"].sum()
    }

    valores = matriz[data_columns].values.flatten()
    valores = valores[~pd.isna(valores)]

    min_val = float(valores.min()) if len(valores) else 0
    max_val = float(valores.max()) if len(valores) else 1

    mostrar_tabla_matriz(
        df=matriz,
        header_left=["Mes"],
        data_columns=data_columns,
        header_right=["Total"],
        footer_totals=footer_totals,
        max_height=520
    )



def detalle_sucursal_por_mes(df_fiscal, df_meta_fiscal):
    st.subheader("🏬 Desempeño por sucursal")

    # -------------------------------
    # SELECTOR DE MES (ORDEN FISCAL)
    # -------------------------------
    meses_disponibles = (
        df_fiscal
        .sort_values("orden_mes_fiscal")
        [["periodo_jd", "orden_mes_fiscal"]]
        .drop_duplicates()
    )

    periodo_sel = st.selectbox(
        "Selecciona el mes",
        meses_disponibles["periodo_jd"].tolist(),
        index=len(meses_disponibles) - 1  # último mes disponible
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------
    # FILTRO POR MES
    # -------------------------------
    df_mes = df_fiscal[
        df_fiscal["periodo_jd"] == periodo_sel
    ].copy()

    df_meta_mes = df_meta_fiscal[
        df_meta_fiscal["periodo_jd"] == periodo_sel
    ].copy()

    # -------------------------------
    # MERGE REALES + META
    # -------------------------------
    tabla_sucursal = (
        df_mes
        .merge(
            df_meta_mes[[
                "sucursal_id",
                "meta",
                "porcentaje_cumplimiento",
                "semaforo"
            ]],
            on="sucursal_id",
            how="left"
        )
    )

    # -------------------------------
    # LIMPIEZA Y FORMATO FINAL
    # -------------------------------
    tabla = tabla_sucursal[[
        "sucursal",
        "venta_real",
        "costo_real",
        "utilidad_real",
        "margen_porcentaje",
        "meta",
        "porcentaje_cumplimiento",
        "semaforo"
    ]].rename(columns={
        "sucursal": "Sucursal",
        "venta_real": "Venta",
        "costo_real": "Costo",
        "utilidad_real": "Utilidad",
        "margen_porcentaje": "Margen %",
        "meta": "Meta",
        "porcentaje_cumplimiento": "% Cumplimiento",
        "semaforo": "Semáforo"
    })

    # Aseguramos tipos numéricos
    for col in ["Venta", "Costo", "Utilidad", "Margen %", "Meta", "% Cumplimiento"]:
        tabla[col] = pd.to_numeric(tabla[col], errors="coerce").fillna(0)

    # Orden opcional (por venta o cumplimiento)
    tabla = tabla.sort_values("Venta", ascending=False)

    # -------------------------------
    # RENDER TABLA
    # -------------------------------
    mostrar_tabla_normal(
        df=tabla,
        columnas_fijas=["Sucursal"],
        columnas_numericas=[
            "Venta",
            "Costo",
            "Utilidad",
            "Margen %",
            "Meta",
            "% Cumplimiento"
        ],

        height=520,
        resaltar_primera_columna=True
    )


    return tabla_sucursal, periodo_sel



def grafica_cumplimiento_sucursal(tabla_sucursal, periodo_sel):
    st.subheader(f"🎯 Cumplimiento de meta por sucursal – {periodo_sel}")

    grafica_sucursal = tabla_sucursal[[
        "sucursal",
        "venta_real",
        "meta",
        "porcentaje_cumplimiento"
    ]].dropna(subset=["meta"])

    grafica_sucursal = grafica_sucursal.sort_values(
        "porcentaje_cumplimiento",
        ascending=False
    )

    grafica_sucursal["color"] = grafica_sucursal["porcentaje_cumplimiento"].apply(
        lambda x: "VERDE" if x >= 100 else "AMARILLO" if x >= 90 else "ROJO"
    )

    color_scale = alt.Scale(
        domain=["ROJO", "AMARILLO", "VERDE"],
        range=["#DC3545", "#FFC107", "#1E7E34"]
    )

    meta_bar = (
        alt.Chart(grafica_sucursal)
        .mark_bar(color="#E0E0E0", opacity=0.9)
        .encode(
            y=alt.Y("sucursal:N", sort=list(grafica_sucursal["sucursal"])),
            x=alt.X("meta:Q", title="Monto ($)", axis=alt.Axis(format=",.2f"))
        )
    )

    venta_bar = (
        alt.Chart(grafica_sucursal)
        .mark_bar(size=18)
        .encode(
            y=alt.Y("sucursal:N", sort=list(grafica_sucursal["sucursal"])),
            x=alt.X("venta_real:Q"),
            color=alt.Color("color:N", scale=color_scale, legend=None),
            tooltip=[
                alt.Tooltip("sucursal:N", title="Sucursal"),
                alt.Tooltip("venta_real:Q", title="Venta", format=",.2f"),
                alt.Tooltip("porcentaje_cumplimiento:Q", title="Cumplimiento (%)", format=".2f")
            ]
        )
    )

    chart = (meta_bar + venta_bar).properties(
        height=max(320, len(grafica_sucursal) * 38)
    )

    st.altair_chart(chart, use_container_width=True)


def tabla_detalle_mensual_sucursal(mensual_sucursal):
    st.subheader("📋 Detalle mensual de venta vs meta")

    # Renombramos columnas para presentación
    tabla = mensual_sucursal[[
        "periodo_jd",
        "venta_real",
        "meta",
        "cumplimiento_meta_pct"
    ]].rename(columns={
        "periodo_jd": "Periodo",
        "venta_real": "Venta",
        "meta": "Meta",
        "cumplimiento_meta_pct": "% Cumplimiento"
    })

    # Aseguramos tipos numéricos
    for col in ["Venta", "Meta", "% Cumplimiento"]:
        tabla[col] = pd.to_numeric(tabla[col], errors="coerce").fillna(0)

    # Mostramos con la plantilla de tabla preestablecida
    mostrar_tabla_normal(
        df=tabla,
        columnas_fijas=["Periodo"],
        columnas_numericas=["Venta", "Meta", "% Cumplimiento"],
        height=400,
        resaltar_primera_columna=True
    )







def mostrar(config):
    st.title("📈 Ventas")

    render_descripcion()

    # -----------------------------
    # CARGA DE DATOS
    # -----------------------------
    df, df_meta = cargar_datos()
    if df is None or df_meta is None:
        return

    # -----------------------------
    # PREPARACIÓN AÑO FISCAL
    # -----------------------------
    df_fiscal, df_meta_fiscal, anio_fiscal_actual = preparar_anio_fiscal(df, df_meta)

    # -----------------------------
    # AGRUPACIÓN MENSUAL
    # -----------------------------
    mensual = preparar_mensual(df_fiscal, df_meta_fiscal)

    # -----------------------------
    # KPIs
    # -----------------------------
    render_kpis(mensual, anio_fiscal_actual)
    st.markdown("---")

    # -----------------------------
    # GRÁFICAS Y TABLAS
    # -----------------------------
    grafica_venta_vs_meta(mensual)
    tabla_ventas_mes_a_mes(mensual)

    grafica_meta_horizontal(mensual)

    matriz_ventas_sucursal(df_fiscal)

    grafica_venta_sucursal_vs_meta(df_meta_fiscal)



    #mensual_sucursal = grafica_venta_sucursal_vs_meta(df_meta_fiscal)
    #tabla_detalle_mensual_sucursal(mensual_sucursal)

    #matriz_ventas_sucursal(df_fiscal)

    tabla_sucursal, periodo_sel = detalle_sucursal_por_mes(
        df_fiscal,
        df_meta_fiscal
    )

    grafica_cumplimiento_sucursal(tabla_sucursal, periodo_sel)

    
















