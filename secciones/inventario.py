import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.api_utils import obtener_vista
from utils.table_utils import mostrar_tabla_matriz_html, mostrar_tabla_normal_html, mostrar_tabla_normal

# ======================================================
# TEMA GLOBAL PLOTLY (fondo oscuro, sin necesidad de config por gráfica)
# ======================================================
BG_COLOR    = "#0e1117"
PAPER_COLOR = "#0e1117"
TEXT_COLOR  = "#e0e0e0"
GRID_COLOR  = "#2a2a2a"
ZERO_COLOR  = "#444444"

def _apply_dark(fig, height=420, show_legend=False):
    """
    Aplica tema oscuro, hover mejorado y ejes con grid visible.
    Reemplaza la versión anterior de _apply_dark().
    """
    fig.update_layout(
        height=height,
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=PAPER_COLOR,
        font=dict(color=TEXT_COLOR, size=12),
        margin=dict(l=10, r=160, t=40, b=10),  # r=160 da espacio a etiquetas externas
        showlegend=show_legend,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="#444",
            font=dict(color=TEXT_COLOR, size=12),
            orientation="h",
            x=0, y=1.08,
        ),
        # ── Hover mejorado ──────────────────────────────
        hoverlabel=dict(
            bgcolor="#1e1e1e",
            bordercolor="#555",
            font=dict(color="#ffffff", size=13),
        ),
        hovermode="closest",
        # ── Ejes ────────────────────────────────────────
        xaxis=dict(
            gridcolor=GRID_COLOR,
            gridwidth=1,
            zerolinecolor=ZERO_COLOR,
            zerolinewidth=1,
            color=TEXT_COLOR,
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            gridwidth=1,
            zerolinecolor=ZERO_COLOR,
            zerolinewidth=1,
            color=TEXT_COLOR,
        ),
    )
    return fig


# ──────────────────────────────────────────────────────
# HELPER: agrega línea de referencia + anotación
# Úsalo en cualquier gráfica después de crearla
# ──────────────────────────────────────────────────────
def _add_linea_referencia(fig, valor, label, axis="x", color="#f1c40f", dash="dot",
                           rango_y=None, rango_x=None):
    """
    Agrega una línea de referencia (meta, promedio, umbral) a la figura.
 
    Parámetros:
        fig     : figura Plotly
        valor   : posición de la línea (en la unidad del eje correspondiente)
        label   : texto de la etiqueta, ej. "Meta: $12M"
        axis    : "x" para línea vertical (barras horizontales)
                  "y" para línea horizontal (barras verticales / líneas)
        color   : color de la línea y anotación
        dash    : "dot" | "dash" | "solid"
        rango_y : tuple (y0, y1) — solo si axis="x". Si None se autodetecta.
        rango_x : tuple (x0, x1) — solo si axis="y". Si None se autodetecta.
    """
    if axis == "x":
        shape = dict(type="line",
                     x0=valor, x1=valor,
                     y0=rango_y[0] if rango_y else -0.5,
                     y1=rango_y[1] if rango_y else 50,
                     line=dict(color=color, width=1.5, dash=dash))
        annotation = dict(x=valor, y=1.01, xref="x", yref="paper",
                          text=label, showarrow=False,
                          font=dict(color=color, size=11),
                          xanchor="center")
    else:
        shape = dict(type="line",
                     y0=valor, y1=valor,
                     x0=rango_x[0] if rango_x else 0,
                     x1=rango_x[1] if rango_x else 1,
                     xref="paper" if not rango_x else "x",
                     line=dict(color=color, width=1.5, dash=dash))
        annotation = dict(x=0.01, y=valor, xref="paper", yref="y",
                          text=label, showarrow=False,
                          font=dict(color=color, size=11),
                          xanchor="left", yanchor="bottom")
 
    fig.add_shape(shape)
    fig.add_annotation(annotation)
    return fig
 
 
# ──────────────────────────────────────────────────────
# HELPER: hover con cambio de color al pasar el mouse
# Para barras horizontales (go.Bar)
# ──────────────────────────────────────────────────────
def _barra_horizontal_con_hover(
    df, x_col, y_col,
    color_base="#34495e",
    color_hover="#2ecc71",
    hovertemplate=None,
    extra_text_fmt="${:,.0f}",
):
    """
    Crea una barra horizontal que cambia de color al hacer hover.
    Retorna (fig, div_id) — usa el div_id para registrar los eventos JS
    en Streamlit con st.components o simplemente usa el fig directamente.
 
    Alternativa sin JS: usa selectedpoints + clickmode (ver abajo).
    """
    valores  = df[x_col].tolist()
    etiquetas = df[y_col].tolist()
 
    if hovertemplate is None:
        hovertemplate = "<b>%{y}</b><br>Valor: $%{x:,.0f}<extra></extra>"
 
    trace = go.Bar(
        x=valores,
        y=etiquetas,
        orientation="h",
        marker=dict(
            color=color_base,
            opacity=0.85,
            line=dict(width=0),
        ),
        text=[extra_text_fmt.format(v) for v in valores],
        textposition="outside",
        textfont=dict(color="#ffffff", size=11),
        hovertemplate=hovertemplate,
        # ── Estilo al seleccionar (click) ──
        selected=dict(marker=dict(color=color_hover, opacity=1.0)),
        unselected=dict(marker=dict(opacity=0.45)),
    )
 
    fig = go.Figure(trace)
    fig.update_layout(clickmode="event+select")
    return fig


def _linea_multi_serie(df_evol, x_col, y_col, color_col,
                       height=360, mostrar_promedio=True):
    """
    Reutilizable para evolución de categorías, proveedores, JD, etc.
    Agrega área rellena ligera y línea de promedio global opcional.
    """
    fig = px.line(
        df_evol, x=x_col, y=y_col, color=color_col,
        markers=True,
        labels={x_col: "Año", y_col: "Valor (MN)", color_col: color_col.capitalize()},
    )
    fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Año: %{x}<br>Valor: $%{y:,.0f}<extra></extra>",
        line=dict(width=2),
        marker=dict(size=8, line=dict(color="#0e1117", width=1.5)),
    )
    _apply_dark(fig, height=height, show_legend=True)
 
    if mostrar_promedio:
        prom_global = df_evol[y_col].mean()
        _add_linea_referencia(
            fig, prom_global,
            label=f"Promedio global: ${prom_global:,.0f}",
            axis="y", color="#f39c12", dash="dot",
        )
    return fig

# ======================================================
# CARGA DE DATOS
# ======================================================
@st.cache_data(ttl=86400)
def cargar_datos_inventario():
    df_suc = obtener_vista("vw_valor_sucursal_entrada")
    df_cat = obtener_vista("vw_valor_sucursal_cat_entrada")
    for df in [df_suc, df_cat]:
        if not df.empty:
            df["valor_inventario_mn"] = pd.to_numeric(df["valor_inventario_mn"], errors="coerce").fillna(0)
            df["periodo"]  = df["anio"].astype(str) + "-" + df["mes_num"].astype(str).str.zfill(2)
            df["mes_anio"] = df["mes_nombre"] + " " + df["anio"].astype(str)
    return df_suc, df_cat


@st.cache_data(ttl=86400)
def cargar_datos_proveedor_jd():
    df_prov = obtener_vista("vw_valor_sucursal_linea_proveedor_entrada")
    df_jd   = obtener_vista("vw_jd_suc_agr_const_entrada")
    for df in [df_prov, df_jd]:
        if not df.empty:
            df["valor_inventario_mn"] = pd.to_numeric(df["valor_inventario_mn"], errors="coerce").fillna(0)
            df["periodo"]  = df["anio"].astype(str) + "-" + df["mes_num"].astype(str).str.zfill(2)
            df["mes_anio"] = df["mes_nombre"] + " " + df["anio"].astype(str)
    if not df_prov.empty:
        df_prov["cantidad_total"] = pd.to_numeric(df_prov["cantidad_total"], errors="coerce").fillna(0)
    return df_prov, df_jd


# ======================================================
# VISTA POR SUCURSAL
# ======================================================
def vista_sucursal_detallada(df_suc):
    if df_suc.empty:
        return

    # ── A. BARRAS HISTÓRICAS ─────────────────────────────
    st.subheader("Valor de Inventario Total por Sucursal (Histórico)")

    df_actual = (
        df_suc.groupby("sucursal_raw", as_index=False)["valor_inventario_mn"]
        .sum()
        .sort_values("valor_inventario_mn", ascending=True)
    )
 
    # Calcula el promedio para la línea de referencia
    promedio = df_actual["valor_inventario_mn"].mean()
 
    fig = go.Figure(go.Bar(
        x=df_actual["valor_inventario_mn"],
        y=df_actual["sucursal_raw"],
        orientation="h",
        marker=dict(color="#34495e", opacity=0.85, line=dict(width=0)),
        text=df_actual["valor_inventario_mn"].apply(lambda v: f"${v:,.2f}"),
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color="#ffffff", size=11),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Valor: $%{x:,.2f}<br>"
            "<extra></extra>"
        ),
        selected=dict(marker=dict(color="#2ecc71", opacity=1.0)),
        unselected=dict(marker=dict(opacity=0.4)),
    ))
    fig.update_layout(clickmode="event+select")
    fig.update_xaxes(autorange=True)

    _apply_dark(fig, height=max(400, len(df_actual) * 32))
 
    # ── Línea de promedio ────────────────────────────────
    _add_linea_referencia(
        fig, promedio,
        label=f"Promedio: ${promedio:,.0f}",
        axis="x", color="#3498db", dash="dash",
        rango_y=(-0.5, len(df_actual) - 0.5),
    )
 
    st.plotly_chart(fig, use_container_width=True)

    # ── B. EVOLUCIÓN ANUAL ───────────────────────────────
    st.subheader("Evolución Anual por Sucursal")
    lista_sucursales = sorted(df_suc["sucursal_raw"].unique())
    sucursal_sel = st.selectbox("Selecciona una sucursal", lista_sucursales, key="sel_suc_evol")
 
    df_ev = (
        df_suc[df_suc["sucursal_raw"] == sucursal_sel]
        .groupby("anio", as_index=False)["valor_inventario_mn"]
        .sum()
    )
    prom_ev = df_ev["valor_inventario_mn"].mean()
 
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_ev["anio"], y=df_ev["valor_inventario_mn"],
        mode="lines+markers+text",
        fill="tozeroy",
        fillcolor="rgba(46,204,113,0.08)",
        line=dict(color="#2ecc71", width=2.5),
        marker=dict(color="#27ae60", size=10, line=dict(color="#0e1117", width=2)),
        text=df_ev["valor_inventario_mn"].apply(lambda v: f"${v:,.2f}"),
        textposition="top center",
        textfont=dict(color="#ffffff", size=11),
        cliponaxis=False,
        hovertemplate=(
            "<b>Año %{x}</b><br>"
            "Valor: $%{y:,.2f}<br>"
            "vs promedio: %{customdata}<extra></extra>"
        ),
        customdata=[
            (f"+{((v-prom_ev)/prom_ev*100):.1f}%" if v >= prom_ev
             else f"{((v-prom_ev)/prom_ev*100):.1f}%")
            for v in df_ev["valor_inventario_mn"]
        ],
    ))
 
    _apply_dark(fig2, height=320)
    _add_linea_referencia(
        fig2, prom_ev,
        label=f"Promedio: ${prom_ev:,.0f}",
        axis="y", color="#3498db", dash="dash",
    )
    fig2.update_layout(xaxis=dict(tickmode="array", tickvals=df_ev["anio"].tolist()))
    st.plotly_chart(fig2, use_container_width=True)

    # ── C. TABLA MATRIZ ──────────────────────────────────
    st.subheader("Resumen Anual por Sucursal")

    df_anual = df_suc.groupby(["sucursal_raw", "anio"])["valor_inventario_mn"].sum().reset_index()
    matriz_anual = df_anual.pivot_table(
        index="sucursal_raw", columns="anio",
        values="valor_inventario_mn", aggfunc="sum"
    ).fillna(0).reset_index().rename(columns={"sucursal_raw": "Sucursal"})

    cols_anios = [c for c in matriz_anual.columns if c != "Sucursal"]
    matriz_anual["Total"] = matriz_anual[cols_anios].sum(axis=1)
    matriz_anual.columns  = [str(c) for c in matriz_anual.columns]
    cols_str = [str(c) for c in cols_anios]

    footer = {
        "Sucursal": "TOTAL",
        **{str(c): matriz_anual[str(c)].sum() for c in cols_str},
        "Total": matriz_anual["Total"].sum(),
    }
    mostrar_tabla_matriz_html(
        df=matriz_anual, color_mode="column",
        header_left=["Sucursal"], data_columns=cols_str,
        header_right=["Total"], footer_totals=footer, max_height=900,
    )


# ======================================================
# VISTA POR CATEGORÍA
# ======================================================
def vista_categoria_detallada(df_cat):
    if df_cat.empty:
        return

    # ── FILTROS ──────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        anios_disponibles = sorted(df_cat["anio"].dropna().unique(), reverse=True)
        anio_sel = st.selectbox("Año", anios_disponibles, key="cat_anio")
    with col2:
        meses_disp = (
            df_cat[df_cat["anio"] == anio_sel][["mes_num", "mes_nombre"]]
            .drop_duplicates().sort_values("mes_num")
        )
        opciones_mes = {r["mes_nombre"]: r["mes_num"] for _, r in meses_disp.iterrows()}
        mes_nombre_sel = st.selectbox("Mes", list(opciones_mes.keys()), key="cat_mes")
        mes_sel = opciones_mes[mes_nombre_sel]
    with col3:
        sucursales = ["Todas"] + sorted(df_cat["sucursal_raw"].unique())
        suc_sel = st.selectbox("Sucursal", sucursales, key="cat_suc")

    mask = (df_cat["anio"] == anio_sel) & (df_cat["mes_num"] == mes_sel)
    if suc_sel != "Todas":
        mask &= df_cat["sucursal_raw"] == suc_sel
    df_periodo = df_cat[mask].copy()

    CATEG_DESC = {
        0:  "CERO ACTIVIDAD ULTIMOS 24 MESES, NO RETORNABLE",
        1:  "MUY ALTA ACTIVIDAD EN EL AÑO",
        2:  "ALTA ACTIVIDAD EN EL AÑO",
        3:  "MEDIANA ACTIVIDAD EN EL AÑO",
        4:  "BAJA ACTIVIDAD EN EL AÑO",
        5:  "MUY BAJA ACTIVIDAD EN EL AÑO",
        6:  "CERO ACTIVIDAD ULTIMOS 12 MESES",
        7:  "PIEZAS NUEVAS POR STOCK INICIAL",
        8:  "PIEZAS NO MANEJADAS EN EL ALMACEN",
        9:  "CERO ACTIVIDAD ULTIMOS 24 MESES, SI RETORNABLE",
        10: "DESECHO",
    }

    # ── A. BARRAS POR CATEGORÍA ──────────────────────────
    st.subheader(f"Valor por Categoría — {mes_nombre_sel} {anio_sel}")

    if df_periodo.empty:
        st.warning("Sin datos para el período seleccionado.")
    else:
        df_cat_total = (
            df_periodo.groupby("categ", as_index=False)["valor_inventario_mn"]
            .sum()
        )
        df_cat_total["categ"] = pd.to_numeric(df_cat_total["categ"], errors="coerce")
        df_cat_total = df_cat_total.sort_values("categ", ascending=True)
        df_cat_total["etiqueta"] = df_cat_total["categ"].apply(
            lambda c: f"{int(c)} — {CATEG_DESC.get(int(c), str(int(c)))}"
        )

        fig = go.Figure(go.Bar(
            x=df_cat_total["valor_inventario_mn"],
            y=df_cat_total["etiqueta"],
            orientation="h",
            marker_color="#7d4e1e",
            text=df_cat_total["valor_inventario_mn"].apply(lambda v: f"${v:,.2f}"),
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Valor: $%{x:,.2f}<extra></extra>",
        ))
        fig.update_xaxes(autorange=True)
        fig.update_yaxes(
            type="category",
            tickmode="array",
            tickvals=df_cat_total["etiqueta"].tolist(),
            ticktext=df_cat_total["etiqueta"].tolist(),
            autorange="reversed",   # 0 arriba → 10 abajo
        )
        _apply_dark(fig, height=max(340, len(df_cat_total) * 42))
        st.plotly_chart(fig, use_container_width=True)

    # ── B. EVOLUCIÓN TEMPORAL ────────────────────────────
    st.subheader("Evolución Temporal por Categoría")

    df_evol = df_cat.copy()
    if suc_sel != "Todas":
        df_evol = df_evol[df_evol["sucursal_raw"] == suc_sel]

    df_evol_cat = (
        df_evol.groupby(["anio", "categ"], as_index=False)["valor_inventario_mn"].sum()
    )
    df_evol_cat["categ"] = pd.to_numeric(df_evol_cat["categ"], errors="coerce")
    df_evol_cat["categ_label"] = df_evol_cat["categ"].apply(
        lambda c: f"{int(c)} — {CATEG_DESC.get(int(c), str(int(c)))}"
    )

    categorias_disponibles = sorted(df_evol_cat["categ_label"].unique(),
                                    key=lambda s: int(s.split(" — ")[0]))
    cats_sel = st.multiselect(
        "Selecciona categorías a comparar",
        categorias_disponibles, default=categorias_disponibles[:5], key="cat_evol_multi",
    )

    if cats_sel:
        df_evol_filtrado = df_evol_cat[df_evol_cat["categ_label"].isin(cats_sel)]
        fig2 = px.line(
            df_evol_filtrado, x="anio", y="valor_inventario_mn",
            color="categ_label", markers=True,
            labels={"anio": "Año", "valor_inventario_mn": "Valor (MN)", "categ_label": "Categoría"},
        )
        fig2.update_traces(
            hovertemplate="<b>%{fullData.name}</b><br>Año: %{x}<br>Valor: $%{y:,.2f}<extra></extra>"
        )
        _apply_dark(fig2, height=360)
        st.plotly_chart(fig2, use_container_width=True)

    # ── C. COMPARATIVO POR SUCURSAL ──────────────────────
    st.subheader("Comparativo por Sucursal dentro de una Categoría")

    cat_opts = sorted(
        [f"{int(c)} — {CATEG_DESC.get(int(c), str(int(c)))}"
         for c in pd.to_numeric(df_cat["categ"], errors="coerce").dropna().unique()],
        key=lambda s: int(s.split(" — ")[0])
    )
    cat_comp = st.selectbox("Selecciona categoría", cat_opts, key="cat_comp_sel")
    cat_num = str(int(cat_comp.split(" — ")[0]))
    mask_comp = (
        (df_cat["anio"] == anio_sel) & (df_cat["mes_num"] == mes_sel)
        & (df_cat["categ"].astype(str) == cat_num)
    )
    df_comp = (
        df_cat[mask_comp].groupby("sucursal_raw", as_index=False)["valor_inventario_mn"]
        .sum().sort_values("valor_inventario_mn", ascending=True)
    )

    fig3 = go.Figure(go.Bar(
        x=df_comp["valor_inventario_mn"],
        y=df_comp["sucursal_raw"],
        orientation="h",
        marker_color="#1a5276",
        text=df_comp["valor_inventario_mn"].apply(lambda v: f"${v:,.2f}"),
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Valor: $%{x:,.2f}<extra></extra>",
    ))
    fig3.update_xaxes(autorange=True)
    _apply_dark(fig3, height=max(300, len(df_comp) * 30))
    st.plotly_chart(fig3, use_container_width=True)

    # ── D. TABLA MATRIZ ──────────────────────────────────
    st.subheader("Resumen Anual por Categoría")

    df_matriz = df_cat.copy()
    if suc_sel != "Todas":
        df_matriz = df_matriz[df_matriz["sucursal_raw"] == suc_sel]

    df_anual_cat = df_matriz.groupby(["categ", "anio"])["valor_inventario_mn"].sum().reset_index()
    df_anual_cat["categ"] = "Cat. " + df_anual_cat["categ"].astype(str)
    matriz = df_anual_cat.pivot_table(
        index="categ", columns="anio",
        values="valor_inventario_mn", aggfunc="sum"
    ).fillna(0).reset_index().rename(columns={"categ": "Categoría"})

    matriz["Categoría"] = matriz["Categoría"].astype(str)
    cols_anios = [c for c in matriz.columns if c != "Categoría"]
    matriz["Total"] = matriz[cols_anios].sum(axis=1)
    matriz.columns   = [str(c) for c in matriz.columns]
    cols_anios_str   = [str(c) for c in cols_anios]

    footer = {
        "Categoría": "TOTAL",
        **{str(c): matriz[str(c)].sum() for c in cols_anios_str},
        "Total": matriz["Total"].sum(),
    }
    mostrar_tabla_matriz_html(
        df=matriz, color_mode="column",
        header_left=["Categoría"], data_columns=cols_anios_str,
        header_right=["Total"], footer_totals=footer, max_height=900,
    )


# ======================================================
# VISTA POR PROVEEDOR
# ======================================================
def vista_proveedor_detallada(df_prov):
    if df_prov.empty:
        st.warning("No se encontraron datos de proveedor.")
        return

    # ── FILTROS ──────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        anios = ["Todos"] + sorted(df_prov["anio"].dropna().unique(), reverse=True)
        anio_sel = st.selectbox("Año", anios, index=0, key="prov_anio")
    with col2:
        df_base_mes = df_prov if anio_sel == "Todos" else df_prov[df_prov["anio"] == anio_sel]
        meses_disp = (
            df_base_mes[["mes_num", "mes_nombre"]]
            .drop_duplicates().sort_values("mes_num")
        )
        opciones_mes = {"Todos": None}
        opciones_mes.update({r["mes_nombre"]: r["mes_num"] for _, r in meses_disp.iterrows()})
        mes_nombre_sel = st.selectbox("Mes", list(opciones_mes.keys()), index=0, key="prov_mes")
        mes_sel = opciones_mes[mes_nombre_sel]
    with col3:
        sucursales = ["Todas"] + sorted(df_prov["sucursal_raw"].unique())
        suc_sel = st.selectbox("Sucursal", sucursales, index=0, key="prov_suc")

    mask_periodo = pd.Series(True, index=df_prov.index)
    if anio_sel != "Todos":
        mask_periodo &= df_prov["anio"] == anio_sel
    if mes_sel is not None:
        mask_periodo &= df_prov["mes_num"] == mes_sel
    if suc_sel != "Todas":
        mask_periodo &= df_prov["sucursal_raw"] == suc_sel
    df_periodo = df_prov[mask_periodo].copy()

    periodo_txt = f"{mes_nombre_sel} {anio_sel}" if mes_sel else (
        str(anio_sel) if anio_sel != "Todos" else "Histórico"
    )

    # ── A. BARRAS TOP 15 ─────────────────────────────────
    st.subheader(f"Top Proveedores — {periodo_txt}")

    TOP_N = 15
    if df_periodo.empty:
        st.warning("Sin datos para el período seleccionado.")
    else:
        df_top = (
            df_periodo.groupby("proveedor", as_index=False)["valor_inventario_mn"]
            .sum().sort_values("valor_inventario_mn", ascending=True).tail(TOP_N)
        )
        fig = go.Figure(go.Bar(
            x=df_top["valor_inventario_mn"],
            y=df_top["proveedor"],
            orientation="h",
            marker_color="#7d4e1e",
            text=df_top["valor_inventario_mn"].apply(lambda v: f"${v:,.2f}"),
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Valor: $%{x:,.2f}<extra></extra>",
        ))
        fig.update_xaxes(autorange=True)
        _apply_dark(fig, height=max(320, TOP_N * 26))
        st.plotly_chart(fig, use_container_width=True)

    # ── B. TABLA ANUAL POR PROVEEDOR (AgGrid) ────────────
    st.subheader("Resumen Anual por Proveedor")

    df_mat = df_prov.copy()
    if suc_sel != "Todas":
        df_mat = df_mat[df_mat["sucursal_raw"] == suc_sel]

    df_anual_prov = df_mat.groupby(["proveedor", "anio"])["valor_inventario_mn"].sum().reset_index()
    matriz_prov = (
        df_anual_prov.pivot_table(
            index="proveedor", columns="anio",
            values="valor_inventario_mn", aggfunc="sum",
        ).fillna(0).reset_index().rename(columns={"proveedor": "Proveedor"})
    )
    cols_anios = [c for c in matriz_prov.columns if c != "Proveedor"]
    matriz_prov["Total"] = matriz_prov[cols_anios].sum(axis=1)
    matriz_prov.columns = [str(c) for c in matriz_prov.columns]
    cols_str = [str(c) for c in cols_anios]

    # Fila de totales
    fila_total = {"Proveedor": "── TOTAL ──"}
    for c in cols_str:
        fila_total[c] = matriz_prov[c].sum()
    fila_total["Total"] = matriz_prov["Total"].sum()
    df_aggrid = pd.concat(
        [matriz_prov, pd.DataFrame([fila_total])], ignore_index=True
    )

    mostrar_tabla_normal(
        df=df_aggrid,
        columnas_fijas=["Proveedor"],
        columnas_numericas=cols_str + ["Total"],
        columna_total="Total",
        height=600,
        resaltar_primera_columna=True,
    )


# ======================================================
# VISTA POR LÍNEA (tab Comparativo Línea)
# ======================================================
def vista_linea_detallada(df_prov):
    """Comparativo de inventario por línea — vive en el tab Comparativo Línea."""
    if df_prov.empty:
        st.warning("No se encontraron datos.")
        return

    df_prov = df_prov.copy()
    df_prov["cantidad_total"] = pd.to_numeric(df_prov["cantidad_total"], errors="coerce").fillna(0)

    # ── FILTROS ──────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        anios = ["Todos"] + sorted(df_prov["anio"].dropna().unique(), reverse=True)
        anio_sel = st.selectbox("Año", anios, index=0, key="linea_anio")
    with col2:
        df_base_mes = df_prov if anio_sel == "Todos" else df_prov[df_prov["anio"] == anio_sel]
        meses_disp = (
            df_base_mes[["mes_num", "mes_nombre"]]
            .drop_duplicates().sort_values("mes_num")
        )
        opciones_mes = {"Todos": None}
        opciones_mes.update({r["mes_nombre"]: r["mes_num"] for _, r in meses_disp.iterrows()})
        mes_nombre_sel = st.selectbox("Mes", list(opciones_mes.keys()), index=0, key="linea_mes")
        mes_sel = opciones_mes[mes_nombre_sel]
    with col3:
        sucursales = ["Todas"] + sorted(df_prov["sucursal_raw"].unique())
        suc_sel = st.selectbox("Sucursal", sucursales, index=0, key="linea_suc")

    # Máscara período
    mask_periodo = pd.Series(True, index=df_prov.index)
    if anio_sel != "Todos":
        mask_periodo &= df_prov["anio"] == anio_sel
    if mes_sel is not None:
        mask_periodo &= df_prov["mes_num"] == mes_sel
    if suc_sel != "Todas":
        mask_periodo &= df_prov["sucursal_raw"] == suc_sel
    df_periodo = df_prov[mask_periodo].copy()

    # Título dinámico del período
    periodo_txt = f"{mes_nombre_sel} {anio_sel}" if mes_sel else (
        str(anio_sel) if anio_sel != "Todos" else "Histórico"
    )

    if df_periodo.empty:
        st.warning("Sin datos para el período seleccionado.")
        return

    # ── DRILL-DOWN POR LÍNEA ──────────────────────────────

    # Filtro de línea
    lineas_disp = sorted(df_prov["linea"].dropna().unique())
    linea_sel = st.selectbox("Selecciona una línea para analizar", lineas_disp, key="linea_drill")

    # Proveedor JOHN DEERE excluido automáticamente para Llantas
    PROVEEDOR_EXCLUIDO_LLANTAS = "JOHN DEERE SALES HISPANOAMERICA"
    es_llantas = "LLANTA" in linea_sel.upper()

    # Datos históricos completos de esa línea (usa suc_sel del filtro superior)
    mask_dd = df_prov["linea"] == linea_sel
    if suc_sel != "Todas":
        mask_dd &= df_prov["sucursal_raw"] == suc_sel
    if es_llantas:
        mask_dd &= df_prov["proveedor"] != PROVEEDOR_EXCLUIDO_LLANTAS
    df_linea_hist = df_prov[mask_dd].copy()

    if df_linea_hist.empty:
        st.warning("Sin datos para la línea seleccionada.")
        return

    if es_llantas:
        st.caption(f"ℹ️ Se excluye automáticamente el proveedor **{PROVEEDOR_EXCLUIDO_LLANTAS}** para esta línea.")

    # Datos del período seleccionado arriba para KPIs
    mask_periodo_dd = mask_periodo & (df_prov["linea"] == linea_sel)
    if suc_sel != "Todas":
        mask_periodo_dd &= df_prov["sucursal_raw"] == suc_sel
    if es_llantas:
        mask_periodo_dd &= df_prov["proveedor"] != PROVEEDOR_EXCLUIDO_LLANTAS
    df_linea_periodo = df_prov[mask_periodo_dd].copy()

    # ── KPIs rápidos ─────────────────────────────────────
    total_valor   = df_linea_periodo["valor_inventario_mn"].sum()
    total_piezas  = df_linea_periodo["cantidad_total"].sum()
    n_proveedores = df_linea_periodo["proveedor"].nunique()

    k1, k2, k3 = st.columns(3)
    k1.metric("Valor inventario",    f"${total_valor:,.0f}")
    k2.metric("Piezas en stock",     f"{total_piezas:,.0f}")
    k3.metric("Proveedores activos", str(n_proveedores))

    # ── Gráfica dual-axis: barras (valor) + línea (piezas) por proveedor ──
    st.markdown(f"#### Valor $ y Piezas por Proveedor — {periodo_txt}")
    st.caption("Barras = Valor ($) | Línea = Piezas")

    df_dist = (
        df_linea_periodo
        .groupby("proveedor", as_index=False)
        .agg(valor=("valor_inventario_mn", "sum"),
             piezas=("cantidad_total", "sum"))
        .sort_values("valor", ascending=False)
    )

    if df_dist.empty:
        st.warning("Sin datos para el período seleccionado con los filtros actuales.")
    else:
        PALETTE = [
            "#2ecc71","#3498db","#e67e22","#9b59b6","#1abc9c",
            "#e74c3c","#f1c40f","#16a085","#d35400","#8e44ad",
            "#2980b9","#27ae60","#c0392b","#f39c12","#7f8c8d",
        ]
        colores = [PALETTE[i % len(PALETTE)] for i in range(len(df_dist))]

        fig_dual = go.Figure()

        # Barras — valor (eje Y izquierdo)
        fig_dual.add_trace(go.Bar(
            name="Valor ($)",
            x=df_dist["proveedor"],
            y=df_dist["valor"],
            marker_color=colores,
            marker_opacity=0.85,
            yaxis="y1",
            hovertemplate="<b>%{x}</b><br>Valor: $%{y:,.2f}<extra></extra>",
            text=df_dist["valor"].apply(lambda v: f"${v:,.0f}"),
            textposition="outside",
            cliponaxis=False,
            textfont=dict(color="#ffffff", size=10),
        ))

        # Línea — piezas (eje Y derecho)
        fig_dual.add_trace(go.Scatter(
            name="Piezas",
            x=df_dist["proveedor"],
            y=df_dist["piezas"],
            mode="lines+markers",
            yaxis="y2",
            line=dict(color="#f1c40f", width=2.5, dash="solid"),
            marker=dict(color="#f1c40f", size=9, line=dict(color="#0e1117", width=1.5)),
            hovertemplate="<b>%{x}</b><br>Piezas: %{y:,.2f}<extra></extra>",
        ))

        n_provs = len(df_dist)
        fig_dual.update_layout(
            height=max(420, 320 + n_provs * 12),
            plot_bgcolor=BG_COLOR,
            paper_bgcolor=PAPER_COLOR,
            font=dict(color=TEXT_COLOR, size=11),
            margin=dict(l=10, r=80, t=60, b=160),
            showlegend=True,
            legend=dict(
                bgcolor="rgba(0,0,0,0)", bordercolor="#444",
                font=dict(color=TEXT_COLOR, size=12),
                orientation="v", x=1.08, xanchor="left", y=0.5, yanchor="middle",
            ),
            hoverlabel=dict(bgcolor="#1e1e1e", bordercolor="#555",
                            font=dict(color="#ffffff", size=13)),
            hovermode="x unified",
            xaxis=dict(
                gridcolor=GRID_COLOR, color=TEXT_COLOR,
                tickangle=-45, tickfont=dict(size=10),
                automargin=True,
            ),
            yaxis=dict(
                title="Valor ($)",
                gridcolor=GRID_COLOR, color=TEXT_COLOR,
                zerolinecolor=ZERO_COLOR,
            ),
            yaxis2=dict(
                title="Piezas",
                overlaying="y", side="right",
                gridcolor="rgba(0,0,0,0)",
                color="#f1c40f",
                zerolinecolor=ZERO_COLOR,
            ),
            bargap=0.25,
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    # ── Evolución histórica concentrada ──────────────────
    st.markdown(f"#### Evolución histórica — {linea_sel}")
    st.caption("Total de la línea por período (todos los proveedores activos)")

    df_evol_total = (
        df_linea_hist
        .groupby(["anio", "mes_num", "mes_nombre"], as_index=False)
        .agg(valor=("valor_inventario_mn", "sum"),
             piezas=("cantidad_total", "sum"))
        .sort_values(["anio", "mes_num"])
    )
    df_evol_total["periodo"] = df_evol_total["mes_nombre"] + " " + df_evol_total["anio"].astype(str)

    if not df_evol_total.empty:
        fig_evol = go.Figure()
        fig_evol.add_trace(go.Bar(
            name="Valor ($)",
            x=df_evol_total["periodo"],
            y=df_evol_total["valor"],
            marker_color="#1a6e3b",
            marker_opacity=0.8,
            yaxis="y1",
            hovertemplate="<b>%{x}</b><br>Valor: $%{y:,.2f}<extra></extra>",
        ))
        fig_evol.add_trace(go.Scatter(
            name="Piezas",
            x=df_evol_total["periodo"],
            y=df_evol_total["piezas"],
            mode="lines+markers",
            yaxis="y2",
            line=dict(color="#f1c40f", width=2.5),
            marker=dict(color="#f1c40f", size=8, line=dict(color="#0e1117", width=1.5)),
            hovertemplate="<b>%{x}</b><br>Piezas: %{y:,.2f}<extra></extra>",
        ))
        fig_evol.update_layout(
            height=380,
            plot_bgcolor=BG_COLOR, paper_bgcolor=PAPER_COLOR,
            font=dict(color=TEXT_COLOR, size=11),
            margin=dict(l=10, r=80, t=40, b=120),
            showlegend=True,
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#444",
                        font=dict(color=TEXT_COLOR, size=12),
                        orientation="h", x=0, y=1.08),
            hoverlabel=dict(bgcolor="#1e1e1e", bordercolor="#555",
                            font=dict(color="#ffffff", size=13)),
            hovermode="x unified",
            xaxis=dict(gridcolor=GRID_COLOR, color=TEXT_COLOR,
                       tickangle=-45, tickfont=dict(size=10), automargin=True),
            yaxis=dict(title="Valor ($)", gridcolor=GRID_COLOR, color=TEXT_COLOR,
                       zerolinecolor=ZERO_COLOR),
            yaxis2=dict(title="Piezas", overlaying="y", side="right",
                        gridcolor="rgba(0,0,0,0)", color="#f1c40f",
                        zerolinecolor=ZERO_COLOR),
            bargap=0.2,
        )
        st.plotly_chart(fig_evol, use_container_width=True)

    # ── Tabla dinámica: Proveedor × Año ($ y Piezas) ─────
    st.markdown(f"#### Resumen anual por proveedor — {linea_sel}")
    st.caption("Filas = Proveedor | Columnas = Año dividido en Valor $ y Piezas")

    df_tabla = (
        df_linea_hist
        .groupby(["proveedor", "anio"], as_index=False)
        .agg(valor=("valor_inventario_mn", "sum"),
             piezas=("cantidad_total", "sum"))
    )

    if not df_tabla.empty:
        anios_tabla = sorted(df_tabla["anio"].unique())
        provs_tabla = sorted(df_tabla["proveedor"].unique())

        # Construir dict de lookup rápido — valores escalares, no Series
        df_lookup = df_tabla.groupby(["proveedor", "anio"]).agg(
            valor=("valor", "sum"), piezas=("piezas", "sum")
        ).reset_index()
        lookup = {
            (row["proveedor"], row["anio"]): {"valor": row["valor"], "piezas": row["piezas"]}
            for _, row in df_lookup.iterrows()
        }

        # Totales por columna
        tot_val  = {a: df_tabla[df_tabla["anio"]==a]["valor"].sum()  for a in anios_tabla}
        tot_pzs  = {a: df_tabla[df_tabla["anio"]==a]["piezas"].sum() for a in anios_tabla}
        tot_val_total  = df_tabla["valor"].sum()
        tot_pzs_total  = df_tabla["piezas"].sum()

        # ── CSS ──────────────────────────────────────────
        html = """
        <style>
        .pvt-wrap { width:100%; }
        .pvt {
            border-collapse: collapse;
            font-family: sans-serif; font-size: 0.80rem;
            white-space: nowrap; width: 100%;
        }
        .pvt th, .pvt td {
            border: 1px solid #2a2a6e;
            padding: 7px 10px;
        }
        /* ── HEADER R1 ─────────────────────────── */
        .pvt thead tr.r1 th {
            background: #0B083D !important; color: #fff !important;
            font-weight: 700; text-align: center;
            position: sticky; top: 0; z-index: 20;
        }
        .pvt thead tr.r1 th.h-prov {
            text-align: left; min-width: 220px;
            position: sticky; left: 0; top: 0; z-index: 31;
        }
        .pvt thead tr.r1 th.h-tot-val {
            position: sticky; right: 82px; top: 0; z-index: 22;
            background: #0B083D !important; color: #fff !important;
        }
        .pvt thead tr.r1 th.h-tot-pzs {
            position: sticky; right: 0; top: 0; z-index: 22;
            background: #0B083D !important; color: #fff !important;
        }
        /* ── HEADER R2 ─────────────────────────── */
        .pvt thead tr.r2 th {
            background: #1a1a3e !important; color: #a0a0ff !important;
            font-weight: 600; font-size: 0.75rem; text-align: right;
            position: sticky; top: 35px; z-index: 20;
        }
        .pvt thead tr.r2 th.h-prov {
            text-align: left;
            position: sticky; left: 0; top: 35px; z-index: 31;
            background: #1a1a3e !important;
        }
        .pvt thead tr.r2 th.h-tot-val {
            position: sticky; right: 82px; top: 35px; z-index: 22;
            background: #1a1a3e !important; color: #a0a0ff !important;
        }
        .pvt thead tr.r2 th.h-tot-pzs {
            position: sticky; right: 0; top: 35px; z-index: 22;
            background: #1a1a3e !important; color: #a0a0ff !important;
        }
        /* ── COLUMNA PROVEEDOR/SUCURSAL FIJA ────── */
        .pvt td.prov {
            position: sticky; left: 0; z-index: 10;
            background: #0B083D !important; color: #fff;
            font-weight: 600; min-width: 220px; max-width: 260px;
            white-space: normal; word-break: break-word; line-height: 1.3;
        }
        /* ── CELDAS NUMÉRICAS ───────────────────── */
        .pvt td.val  { text-align: right; color: #e0e0e0; }
        .pvt td.pzs  { text-align: right; color: #f1c40f; }
        /* ── TOTALES — sticky derecha ───────────── */
        .pvt td.tot-val {
            text-align: right; color: #fff; font-weight: 700;
            background: #0d1b2a !important;
            position: sticky; right: 90px; z-index: 10;
            min-width: 110px; width: 110px;
        }
        .pvt td.tot-pzs {
            text-align: right; color: #f1c40f; font-weight: 700;
            background: #0d1b2a !important;
            position: sticky; right: 0; z-index: 10;
            min-width: 90px; width: 90px;
        }
        /* ── FILA TOTAL INFERIOR ────────────────── */
        .pvt tfoot td {
            background: #0B083D !important; color: #fff;
            font-weight: 700; text-align: right;
            position: sticky; bottom: 0; z-index: 10;
        }
        .pvt tfoot td.prov {
            text-align: left;
            position: sticky; left: 0; bottom: 0; z-index: 25;
        }
        .pvt tfoot td.pzs   { color: #f1c40f; }
        .pvt tfoot td.tot-val {
            position: sticky; right: 90px; bottom: 0; z-index: 25;
            background: #0B083D !important;
            min-width: 110px; width: 110px;
        }
        .pvt tfoot td.tot-pzs {
            position: sticky; right: 0; bottom: 0; z-index: 25;
            background: #0B083D !important; color: #f1c40f;
            min-width: 90px; width: 90px;
        }
        /* ── HEADER TOTALES width/right ─────────── */
        .pvt thead th.h-tot-val {
            min-width: 110px; width: 110px; right: 90px;
        }
        .pvt thead th.h-tot-pzs {
            min-width: 90px; width: 90px; right: 0;
        }
        /* ── FILAS ALTERNAS ─────────────────────── */
        .pvt tbody tr:nth-child(even) td { background: #121212; }
        .pvt tbody tr:nth-child(odd)  td { background: #1a1a1a; }
        .pvt tbody tr:hover td { background: #1e2d40 !important; }
        .pvt-wrap * { box-sizing: border-box; }
        .pvt-scroll { max-height: 750px; overflow: auto;
                      border: 1px solid #2a2a6e; border-radius: 4px; }
        .pvt-scroll::-webkit-scrollbar { width:6px; height:6px; }
        .pvt-scroll::-webkit-scrollbar-thumb { background:#444; border-radius:6px; }
        </style>
        """

        # ── THEAD ─────────────────────────────────────────
        html += '<div class="pvt-wrap"><div class="pvt-scroll"><table class="pvt"><thead>'

        # Fila 1: Proveedor | años | Total
        html += '<tr class="r1">'
        html += '<th class="h-prov">Proveedor</th>'
        for i, a in enumerate(anios_tabla):
            sep = ' sep' if i == 0 else ''
            html += f'<th colspan="2" class="{sep}">{a}</th>'
        html += '<th class="h-tot-val sep">Total $</th>'
        html += '<th class="h-tot-pzs">Total Piezas</th>'
        html += '</tr>'

        # Fila 2: vacío | $ Piezas por año | $ Piezas total
        html += '<tr class="r2">'
        html += '<th class="h-prov"></th>'
        for i, a in enumerate(anios_tabla):
            sep = ' sep' if i == 0 else ''
            html += f'<th class="{sep}">$</th><th>Piezas</th>'
        html += '<th class="h-tot-val sep">$</th><th class="h-tot-pzs">Piezas</th>'
        html += '</tr></thead>'

        # ── TBODY ─────────────────────────────────────────
        html += '<tbody>'
        for prov in provs_tabla:
            tot_p_val = sum(lookup.get((prov, a), {}).get("valor",  0) for a in anios_tabla)
            tot_p_pzs = sum(lookup.get((prov, a), {}).get("piezas", 0) for a in anios_tabla)
            html += '<tr>'
            html += f'<td class="prov">{prov}</td>'
            for i, a in enumerate(anios_tabla):
                rec = lookup.get((prov, a))
                v = rec["valor"]  if rec is not None else 0
                p = rec["piezas"] if rec is not None else 0
                sep = ' sep' if i == 0 else ''
                v_str = f'${v:,.2f}' if v else '—'
                p_str = f'{p:,.2f}'  if p else '—'
                html += f'<td class="val{sep}">{v_str}</td>'
                html += f'<td class="pzs">{p_str}</td>'
            html += f'<td class="tot-val">${tot_p_val:,.2f}</td>'
            html += f'<td class="tot-pzs">{tot_p_pzs:,.2f}</td>'
            html += '</tr>'
        html += '</tbody>'

        # ── TFOOT ─────────────────────────────────────────
        html += '<tfoot><tr>'
        html += '<td class="prov">TOTAL</td>'
        for i, a in enumerate(anios_tabla):
            sep = ' sep' if i == 0 else ''
            html += f'<td class="val{sep}">${tot_val[a]:,.2f}</td>'
            html += f'<td class="pzs">{tot_pzs[a]:,.2f}</td>'
        html += f'<td class="tot-val">${tot_val_total:,.2f}</td>'
        html += f'<td class="tot-pzs">{tot_pzs_total:,.2f}</td>'
        html += '</tr></tfoot>'

        html += '</table></div></div>'
        st.write(html, unsafe_allow_html=True)

    # ── Tabla dinámica: Sucursal × Año ($ y Piezas) ──────
    st.markdown(f"#### Resumen anual por sucursal — {linea_sel}")
    st.caption("Filas = Sucursal | Columnas = Año dividido en Valor $ y Piezas")

    df_tabla_suc = (
        df_linea_hist
        .groupby(["sucursal_raw", "anio"], as_index=False)
        .agg(valor=("valor_inventario_mn", "sum"),
             piezas=("cantidad_total", "sum"))
    )

    if not df_tabla_suc.empty:
        anios_suc   = sorted(df_tabla_suc["anio"].unique())
        sucs_tabla  = sorted(df_tabla_suc["sucursal_raw"].unique())

        df_lookup_suc = df_tabla_suc.groupby(["sucursal_raw", "anio"]).agg(
            valor=("valor", "sum"), piezas=("piezas", "sum")
        ).reset_index()
        lookup_suc = {
            (row["sucursal_raw"], row["anio"]): {"valor": row["valor"], "piezas": row["piezas"]}
            for _, row in df_lookup_suc.iterrows()
        }

        tot_val_suc   = {a: df_tabla_suc[df_tabla_suc["anio"]==a]["valor"].sum()  for a in anios_suc}
        tot_pzs_suc   = {a: df_tabla_suc[df_tabla_suc["anio"]==a]["piezas"].sum() for a in anios_suc}
        tot_val_suc_t = df_tabla_suc["valor"].sum()
        tot_pzs_suc_t = df_tabla_suc["piezas"].sum()

        hsuc = """
        <style>
        /* Overrides específicos para tabla de sucursales */
        .pvt-suc td.prov, .pvt-suc thead th.h-prov {
            min-width: 80px !important; max-width: 110px !important;
        }
        /* Anchos fijos en columnas totales para que right sea predecible */
        .pvt td.tot-val, .pvt thead th.h-tot-val,
        .pvt tfoot td.tot-val {
            min-width: 110px; width: 110px;
        }
        .pvt td.tot-pzs, .pvt thead th.h-tot-pzs,
        .pvt tfoot td.tot-pzs {
            min-width: 90px; width: 90px;
        }
        /* right debe coincidir exactamente con width de tot-pzs */
        .pvt td.tot-val      { right: 90px; }
        .pvt thead th.h-tot-val { right: 90px; }
        .pvt tfoot td.tot-val   { right: 90px; }
        /* Quitar bordes blancos extra del contenedor Streamlit */
        .pvt-wrap * { box-sizing: border-box; }
        .pvt-scroll { border: 1px solid #2a2a6e; border-radius: 4px; }
        </style>
        <div class="pvt-wrap"><div class="pvt-scroll"><table class="pvt pvt-suc"><thead>"""

        # Fila 1
        hsuc += '<tr class="r1">'
        hsuc += '<th class="h-prov">Sucursal</th>'
        for i, a in enumerate(anios_suc):
            sep = ' sep' if i == 0 else ''
            hsuc += f'<th colspan="2" class="{sep}">{a}</th>'
        hsuc += '<th class="h-tot-val sep">Total $</th>'
        hsuc += '<th class="h-tot-pzs">Total Piezas</th>'
        hsuc += '</tr>'

        # Fila 2
        hsuc += '<tr class="r2"><th class="h-prov"></th>'
        for i, a in enumerate(anios_suc):
            sep = ' sep' if i == 0 else ''
            hsuc += f'<th class="{sep}">$</th><th>Piezas</th>'
        hsuc += '<th class="h-tot-val sep">$</th><th class="h-tot-pzs">Piezas</th>'
        hsuc += '</tr></thead><tbody>'

        for suc in sucs_tabla:
            tot_s_val = sum(lookup_suc.get((suc, a), {}).get("valor",  0) for a in anios_suc)
            tot_s_pzs = sum(lookup_suc.get((suc, a), {}).get("piezas", 0) for a in anios_suc)
            hsuc += '<tr>'
            hsuc += f'<td class="prov">{suc}</td>'
            for i, a in enumerate(anios_suc):
                rec = lookup_suc.get((suc, a))
                v = rec["valor"]  if rec is not None else 0
                p = rec["piezas"] if rec is not None else 0
                sep = ' sep' if i == 0 else ''
                v_str = f'${v:,.2f}' if v else '—'
                p_str = f'{p:,.2f}'  if p else '—'
                hsuc += f'<td class="val{sep}">{v_str}</td>'
                hsuc += f'<td class="pzs">{p_str}</td>'
            hsuc += f'<td class="tot-val">${tot_s_val:,.2f}</td>'
            hsuc += f'<td class="tot-pzs">{tot_s_pzs:,.2f}</td>'
            hsuc += '</tr>'

        hsuc += '</tbody><tfoot><tr>'
        hsuc += '<td class="prov">TOTAL</td>'
        for i, a in enumerate(anios_suc):
            sep = ' sep' if i == 0 else ''
            hsuc += f'<td class="val{sep}">${tot_val_suc[a]:,.2f}</td>'
            hsuc += f'<td class="pzs">{tot_pzs_suc[a]:,.2f}</td>'
        hsuc += f'<td class="tot-val">${tot_val_suc_t:,.2f}</td>'
        hsuc += f'<td class="tot-pzs">{tot_pzs_suc_t:,.2f}</td>'
        hsuc += '</tr></tfoot></table></div></div>'

        st.write(hsuc, unsafe_allow_html=True)



def _barras_agrupadas_jd(df_suc_tipo, escala_colores=None, height=None):
    if escala_colores is None:
        escala_colores = {"Agricola": "#2ecc71", "Construccion": "#f1c40f"}

    fig = px.bar(
        df_suc_tipo,
        x="valor_inventario_mn", y="sucursal_raw",
        color="agr_constr_raw", barmode="group",
        orientation="h",
        color_discrete_map=escala_colores,
        labels={
            "valor_inventario_mn": "Valor (MN)",
            "sucursal_raw": "Sucursal",
            "agr_constr_raw": "Tipo",
        },
        text=df_suc_tipo["valor_inventario_mn"].apply(lambda v: f"${v:,.0f}"),
    )
    
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color="#ffffff", size=10),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Tipo: %{fullData.name}<br>"
            "Valor: $%{x:,.0f}<extra></extra>"
        ),
        marker=dict(opacity=0.85),
        selected=dict(marker=dict(opacity=1.0)),
        unselected=dict(marker=dict(opacity=0.4)),
    )
    fig.update_xaxes(autorange=True)
    
    fig.update_layout(clickmode="event+select")
    
    _apply_dark(
        fig, 
        height=height or max(320, len(df_suc_tipo["sucursal_raw"].unique()) * 55),
        show_legend=True,
    )
    return fig


# ======================================================
# VISTA JD
# ======================================================
def vista_jd_detallada(df_jd):
    if df_jd.empty:
        st.warning("No se encontraron datos de JD.")
        return

    COLORES_TIPO = {"Agrícola": "#27ae60", "Construcción": "#3498db"}

    # ── FILTROS ──────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        anios_jd = sorted(df_jd["anio"].dropna().unique(), reverse=True)
        anio_jd  = st.selectbox("Año", anios_jd, key="jd_anio")
    with col2:
        meses_jd = (
            df_jd[df_jd["anio"] == anio_jd][["mes_num", "mes_nombre"]]
            .drop_duplicates().sort_values("mes_num")
        )
        opc_mes_jd = {r["mes_nombre"]: r["mes_num"] for _, r in meses_jd.iterrows()}
        mes_jd_nombre = st.selectbox("Mes", list(opc_mes_jd.keys()), key="jd_mes")
        mes_jd = opc_mes_jd[mes_jd_nombre]
    with col3:
        tipos_ret = ["Todos"] + sorted(df_jd["tipo_retorno"].dropna().unique())
        tipo_sel  = st.selectbox("Tipo de retorno", tipos_ret, key="jd_tipo")

    mask_jd = (df_jd["anio"] == anio_jd) & (df_jd["mes_num"] == mes_jd)
    if tipo_sel != "Todos":
        mask_jd &= df_jd["tipo_retorno"] == tipo_sel
    df_periodo_jd = df_jd[mask_jd].copy()

    # ── A. BARRAS AGRUPADAS POR SUCURSAL Y TIPO ──────────
    st.subheader(f"Valor por Sucursal y Tipo — {mes_jd_nombre} {anio_jd}")

    if df_periodo_jd.empty:
        st.warning("Sin datos para el período seleccionado.")
    else:
        df_suc_tipo = (
            df_periodo_jd.groupby(["sucursal_raw", "agr_constr_raw"], as_index=False)
            ["valor_inventario_mn"].sum()
        )

        # Colores: verde=Agrícola, amarillo=Construcción, blanco=NaN/otros
        tipos_uniq = df_suc_tipo["agr_constr_raw"].fillna("Sin clasificar").unique()
        COLOR_MAP = {}
        for t in tipos_uniq:
            tu = str(t).upper()
            if "AGRI" in tu or "AGRÍ" in tu:
                COLOR_MAP[t] = "#27ae60"
            elif "CONST" in tu:
                COLOR_MAP[t] = "#f1c40f"
            elif "GOLF" in tu:
                COLOR_MAP[t] = "#3498db"
            else:
                COLOR_MAP[t] = "#ecf0f1"
        df_suc_tipo["agr_constr_raw"] = df_suc_tipo["agr_constr_raw"].fillna("Sin clasificar")

        fig = go.Figure()
        for tipo in df_suc_tipo["agr_constr_raw"].unique():
            df_t = df_suc_tipo[df_suc_tipo["agr_constr_raw"] == tipo].sort_values("valor_inventario_mn")
            fig.add_trace(go.Bar(
                name=tipo,
                x=df_t["valor_inventario_mn"],
                y=df_t["sucursal_raw"],
                orientation="h",
                marker_color=COLOR_MAP.get(tipo, "#ecf0f1"),
                marker_opacity=0.87,
                text=df_t["valor_inventario_mn"].apply(lambda v: f"${v:,.0f}"),
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>Tipo: %{fullData.name}<br>Valor: $%{x:,.2f}<extra></extra>",
            ))

        fig.update_xaxes(autorange=True)
        _apply_dark(
            fig,
            height=max(340, df_suc_tipo["sucursal_raw"].nunique() * 55),
            show_legend=True,
        )
        fig.update_layout(barmode="group", hovermode="y unified")
        st.plotly_chart(fig, use_container_width=True)

    # ── B. TABLA MATRIZ ──────────────────────────────────
    st.subheader("Resumen Anual por Sucursal y Tipo")

    df_mat_jd = df_jd.copy()
    if tipo_sel != "Todos":
        df_mat_jd = df_mat_jd[df_mat_jd["tipo_retorno"] == tipo_sel]

    df_anual_jd = (
        df_mat_jd.groupby(["sucursal_raw", "agr_constr_raw", "anio"])
        ["valor_inventario_mn"].sum().reset_index()
    )
    df_anual_jd["idx"] = (
        df_anual_jd["sucursal_raw"] + " | " + df_anual_jd["agr_constr_raw"].fillna("—")
    )

    matriz_jd = (
        df_anual_jd.pivot_table(
            index="idx", columns="anio",
            values="valor_inventario_mn", aggfunc="sum",
        ).fillna(0).reset_index().rename(columns={"idx": "Sucursal / Tipo"})
    )
    cols_anios_jd = [c for c in matriz_jd.columns if c != "Sucursal / Tipo"]
    matriz_jd["Total"] = matriz_jd[cols_anios_jd].sum(axis=1)
    matriz_jd.columns  = [str(c) for c in matriz_jd.columns]
    cols_jd_str = [str(c) for c in cols_anios_jd]

    footer_jd = {
        "Sucursal / Tipo": "TOTAL",
        **{str(c): matriz_jd[str(c)].sum() for c in cols_jd_str},
        "Total": matriz_jd["Total"].sum(),
    }
    mostrar_tabla_matriz_html(
        df=matriz_jd, color_mode="column",
        header_left=["Sucursal / Tipo"], data_columns=cols_jd_str,
        header_right=["Total"], footer_totals=footer_jd, max_height=900,
    )


# ======================================================
# FUNCIÓN PRINCIPAL
# ======================================================
def mostrar(config=None): # Agregado None por si acaso
    st.title("Valor de Inventario")

    # Carga de datos
    df_suc, df_cat = cargar_datos_inventario()
    df_prov, df_jd = cargar_datos_proveedor_jd() # Corregido: solo 2 variables

    if df_suc.empty:
        st.warning("No se encontraron datos de inventario.")
        return

    tab_suc, tab_cat, tab_jd, tab_linea = st.tabs([
        "Vista por Sucursal",
        "Categoría",
        "Vista JD",
        "Línea",
    ])

    with tab_suc:
        vista_sucursal_detallada(df_suc)
    
    with tab_cat:
        vista_categoria_detallada(df_cat)
    
    with tab_jd:
        vista_jd_detallada(df_jd)
        
    with tab_linea:
        vista_linea_detallada(df_prov)