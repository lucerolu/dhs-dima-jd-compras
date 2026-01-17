# secciones/compras.py

import streamlit as st
import streamlit.components.v1 as components
import altair as alt
import pandas as pd
from utils.api_utils import obtener_vista
from utils.table_utils import mostrar_tabla_matriz
from datetime import datetime



def agregar_semaforo(df):
    df = df.copy()
    df["semaforo"] = df["porcentaje_avance"].apply(
        lambda x: "Verde" if x >= 100 else "Amarillo" if x >= 90 else "Rojo"
    )
    return df


def color_semaforo(pct):
    if pct >= 100:
        return "#2ecc71"  # verde
    elif pct >= 90:
        return "#f1c40f"  # amarillo
    else:
        return "#e74c3c"  # rojo

def mostrar_tarjetas_mes_actual(df_mes):
    st.subheader("📆 Mes actual")

    cols = st.columns(len(df_mes))

    for col, (_, row) in zip(cols, df_mes.iterrows()):
        pct = row["porcentaje_avance"]
        color = color_semaforo(pct)

        with col:
            components.html(
                f"""
                <div style="
                    background-color:#0e1117;
                    border-radius:16px;
                    padding:26px;
                    border-left:10px solid {color};
                    color:white;
                    display:flex;
                    flex-direction:column;
                    justify-content:space-between;
                    gap:14px;
                    font-family:Arial, sans-serif;
                ">


                    <!-- TÍTULO -->
                    <div style="
                        font-size:22px;
                        font-weight:700;
                        margin-bottom:16px;
                    ">
                        {row['division_nombre']}
                    </div>

                    <!-- DATOS -->
                    <div>
                        <div style="margin-bottom:12px;">
                            <div style="font-size:15px;opacity:0.7;">
                                Compra
                            </div>
                            <div style="font-size:20px;font-weight:700;">
                                ${row['compra_real']:,.0f}
                            </div>
                        </div>

                        <div>
                            <div style="font-size:15px;opacity:0.7;">
                                Meta
                            </div>
                            <div style="font-size:20px;font-weight:700;">
                                ${row['meta_monto']:,.0f}
                            </div>
                        </div>
                    </div>

                    <!-- PORCENTAJE -->
                    <div style="
                        font-size:34px;
                        font-weight:800;
                        color:{color};
                        text-align:right;
                        margin-top:10px;
                    ">
                        {pct:.1f}%
                    </div>
                </div>
                """,
                height=280
            )


def grafico_ejecucion_vs_meta_mes_actual(df_mes):
    st.subheader("📊 Avance de la meta actual")

    df_g = df_mes.sort_values("porcentaje_avance")

    # Línea de meta
    linea_meta = alt.Chart(df_g).mark_rule(
        color="white",
        strokeDash=[4, 4],
        size=3
    ).encode(
        x=alt.X("meta_monto:Q"),
        y=alt.Y("division_nombre:N"),
        tooltip=[
            alt.Tooltip("division_nombre:N", title="División"),
            alt.Tooltip("meta_monto:Q", title="Meta", format=",.2f"),
        ]
    )

    # Barras de ejecución
    barras = (
        alt.Chart(df_g)
        .transform_calculate(
            faltante_abs="abs(datum.diferencia_vs_meta)"
        )
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            y=alt.Y(
                "division_nombre:N",
                title="División",
                sort="-x"
            ),
            x=alt.X(
                "compra_real:Q",
                title="Monto ($)",
                axis=alt.Axis(format=",.0f")
            ),
            color=alt.Color(
                "semaforo:N",
                scale=alt.Scale(
                    domain=["Rojo", "Amarillo", "Verde"],
                    range=["#e74c3c", "#f1c40f", "#2ecc71"]
                ),
                legend=None
            ),
            tooltip=[
                alt.Tooltip("division_nombre:N", title="División"),
                alt.Tooltip("compra_real:Q", title="Compra real", format=",.2f"),
                alt.Tooltip("meta_monto:Q", title="Meta", format=",.2f"),
                alt.Tooltip("faltante_abs:Q", title="Faltante", format=",.2f"),
                alt.Tooltip("porcentaje_avance:Q", title="Cumplimiento (%)", format=".1f"),
            ]
        )
    )

    chart = (barras + linea_meta).properties(height=300)

    st.altair_chart(chart, use_container_width=True)


def grafico_cumplimiento_historico(df):
    st.subheader("📈 Cumplimiento de meta por mes (%)")

    df_hist = df[df["compra_real"] > 0].copy()
    df_hist["orden_mes"] = df_hist["anio_jd"] * 100 + df_hist["mes_jd"]
    df_hist = df_hist.sort_values("orden_mes")

    # Escala de colores fija por división
    escala_colores = alt.Scale(
        domain=["Agrícola", "Construcción"],
        range=["#367C2B", "#FFA500"]
    )

    # Líneas de cumplimiento por división
    lineas = (
        alt.Chart(df_hist)
        .transform_calculate(
            faltante_abs="abs(datum.meta_monto - datum.compra_real)"
        )
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "periodo_label:N",
                title="Mes",
                sort=alt.SortField(field="orden_mes", order="ascending"),
                axis=alt.Axis(labelAngle=0)
            ),
            y=alt.Y(
                "porcentaje_avance:Q",
                title="Cumplimiento (%)",
                axis=alt.Axis(format=".0f")
            ),
            color=alt.Color(
                "division_nombre:N",
                title="División",
                scale=escala_colores
            ),
            tooltip=[
                alt.Tooltip("division_nombre:N", title="División"),
                alt.Tooltip("periodo_label:N", title="Mes"),
                alt.Tooltip("porcentaje_avance:Q", title="Cumplimiento (%)", format=".1f"),
                alt.Tooltip("compra_real:Q", title="Compra", format=",.2f"),
                alt.Tooltip("meta_monto:Q", title="Meta", format=",.2f"),
                alt.Tooltip("faltante_abs:Q", title="Faltante para la meta", format=",.2f"),
            ]
        )
    )

    # Línea de meta general (100%)
    linea_meta = (
        alt.Chart(pd.DataFrame({"meta_pct": [100]}))
        .mark_rule(
            strokeDash=[6, 4],
            strokeWidth=2,
            color="#DFE4E9"
        )
        .encode(
            y="meta_pct:Q",
            tooltip=[alt.Tooltip("meta_pct:Q", title="Meta (%)", format=".0f")]
        )
    )

    chart = (lineas + linea_meta).properties(height=360).interactive()

    st.altair_chart(chart, use_container_width=True)
    st.caption("🔹 Línea punteada gris = Meta general de cumplimiento (100%)")


def grafico_meta_vs_compra_por_division(df, division):
    st.subheader(f"📊 Meta vs Compra mensual – {division}")

    df_div = df[df["division_nombre"] == division].copy()

    if df_div.empty:
        st.info(f"No hay datos para la división {division}.")
        return

    # Omitir meses con meta pero sin avance
    df_div = df_div[
        ~((df_div["meta_monto"] > 0) & (df_div["compra_real"] == 0))
    ]

    df_div["orden_mes"] = df_div["anio_jd"] * 100 + df_div["mes_jd"]
    df_div = df_div.sort_values("orden_mes")

    df_long = df_div.melt(
        id_vars=["periodo_label", "orden_mes"],
        value_vars=["meta_monto", "compra_real"],
        var_name="tipo",
        value_name="monto"
    )

    df_long["tipo"] = df_long["tipo"].map({
        "meta_monto": "Meta",
        "compra_real": "Compra real"
    })

    colores_division = {
        "Agrícola": "#367C2B",
        "Construcción": "#FFA500"
    }

    escala_colores = alt.Scale(
        domain=["Meta", "Compra real"],
        range=["#D5DBDB", colores_division.get(division, "#999999")]
    )

    orden_meses = (
    df_div.sort_values("orden_mes")["periodo_label"]
    .unique()
    .tolist()
    )

    barras = alt.Chart(df_long).mark_bar(
        height=18,
        cornerRadius=3
    ).encode(
        y=alt.Y(
            "periodo_label:N",
            title="Mes",
            sort=orden_meses,
            scale=alt.Scale(paddingInner=0, paddingOuter=0.25)
        ),
        yOffset=alt.YOffset(
            "tipo:N",
            scale=alt.Scale(paddingInner=0.05)
        ),
        x=alt.X(
            "monto:Q",
            title="Monto ($)",
            axis=alt.Axis(format=",.0f")
        ),
        color=alt.Color(
            "tipo:N",
            scale=escala_colores,
            legend=alt.Legend(title="")
        )
    )

    lineas_mes = alt.Chart(df_div).mark_rule(
        strokeDash=[3, 4],
        strokeWidth=1,
        color="#3A3A3A"
    ).encode(
        y=alt.Y(
            "periodo_label:N",
            sort=orden_meses
        ),
        yOffset=alt.value(0.5)
    )

    chart = (lineas_mes + barras).properties(height=340)


    st.altair_chart(chart, use_container_width=True)



def mostrar(config):
    st.title("🛒 Compras vs Meta")

    df = obtener_vista("vw_division_vs_meta_jd")

    if df.empty:
        st.warning("No hay datos disponibles de compras.")
        return

    hoy = datetime.today()
    df_mes = df[
        (df["anio_jd"] == hoy.year) &
        (df["mes_jd"] == hoy.month)
    ]

    if df_mes.empty:
        st.info("No hay datos para el mes actual.")
        return

    
    df_mes = agregar_semaforo(df_mes)

    # 1️⃣ Snapshot actual
    mostrar_tarjetas_mes_actual(df_mes)

    # 2️⃣ Ejecución vs Meta (mes actual)
    grafico_ejecucion_vs_meta_mes_actual(df_mes)

    # 3️⃣ Tendencia histórica
    grafico_cumplimiento_historico(df)

    grafico_meta_vs_compra_por_division(df, "Agrícola")
    grafico_meta_vs_compra_por_division(df, "Construcción")
