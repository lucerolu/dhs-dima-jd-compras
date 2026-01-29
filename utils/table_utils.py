# utils/table_utils.py
import pandas as pd
import numpy as np
import streamlit as st
import pandas as pd
import json
from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    JsCode,
    AgGridTheme,
    ColumnsAutoSizeMode
)

# --------------------------------------------------
# FORMATTERS
# --------------------------------------------------
value_formatter_2dec = JsCode("""
function(params) {
    if (params.value == null) return '';
    return params.value.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}
""")

semaforo_cell_style = JsCode("""
function(params) {
    if (!params.value) return {};

    if (params.value === 'VERDE') {
        return {
            backgroundColor: '#1E7E34',
            color: 'white',
            fontWeight: 'bold',
            textAlign: 'center'
        };
    }
    if (params.value === 'AMARILLO') {
        return {
            backgroundColor: '#FFC107',
            color: '#212529',
            fontWeight: 'bold',
            textAlign: 'center'
        };
    }
    if (params.value === 'ROJO') {
        return {
            backgroundColor: '#DC3545',
            color: 'white',
            fontWeight: 'bold',
            textAlign: 'center'
        };
    }
    return {};
}
""")





# --------------------------------------------------
# TABLA BASE REUTILIZABLE
# --------------------------------------------------
def mostrar_tabla_normal(
    df: pd.DataFrame,
    columnas_fijas=None,
    columnas_numericas=None,
    columnas_sin_degradado=None,
    columna_total=None,
    height=600,
    resaltar_primera_columna: bool = False
):
    if df.empty:
        return

    columnas_fijas = columnas_fijas or []
    columnas_numericas = columnas_numericas or []
    columnas_sin_degradado = columnas_sin_degradado or []

    # ---------------------------------
    # ALTURA DINÁMICA
    # ---------------------------------
    row_height = 35
    header_height = 40
    calculated_height = min(
        header_height + row_height * (len(df) + 1),
        height
    )

    gb = GridOptionsBuilder.from_dataframe(df)

    # ---------------------------------
    # CONFIGURACIÓN GENERAL
    # ---------------------------------
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=False,
        minWidth=110,
        wrapText=False
    )

    # ---------------------------------
    # 🔵 PRIMERA COLUMNA (AZUL OSCURO)
    # ---------------------------------
    for i, col in enumerate(columnas_fijas):
        if i == 0 and resaltar_primera_columna:
            gb.configure_column(
                col,
                pinned="left",
                minWidth=170,
                cellStyle={
                    "backgroundColor": "#0B083D",
                    "color": "white",
                    "fontWeight": "bold",
                    "textAlign": "left"
                }
            )
        else:
            gb.configure_column(
                col,
                pinned="left",
                minWidth=160,
                cellStyle={
                    "fontWeight": "bold",
                    "textAlign": "left"
                }
            )

    # ---------------------------------
    # 🎨 CALCULAR MIN / MAX POR COLUMNA
    # ---------------------------------
    min_max = {}
    for col in columnas_numericas:
        if col not in columnas_sin_degradado and col in df.columns:
            min_max[col] = {
                "min": float(df[col].min()),
                "max": float(df[col].max())
            }

    min_max_js = json.dumps(min_max)

    # ---------------------------------
    # 🎨 DEGRADADO AZUL (POR COLUMNA)
    # ---------------------------------
    degradado_js = JsCode(f"""
    function(params) {{
        const limits = {min_max_js};
        const col = params.colDef.field;

        if (!limits[col] || params.value == null) {{
            return {{ textAlign: 'right' }};
        }}

        const min = limits[col].min;
        const max = limits[col].max;

        if (max === min) {{
            return {{
                backgroundColor: '#E3F2FD',
                textAlign: 'right'
            }};
        }}

        const ratio = (params.value - min) / (max - min);

        const start = [227, 242, 253]; // azul claro
        const end   = [21, 101, 192];  // azul fuerte

        const r = Math.round(start[0] + ratio * (end[0] - start[0]));
        const g = Math.round(start[1] + ratio * (end[1] - start[1]));
        const b = Math.round(start[2] + ratio * (end[2] - start[2]));

        return {{
            backgroundColor: `rgb(${{r}}, ${{g}}, ${{b}})`,
            color: ratio > 0.6 ? 'white' : '#0B083D',
            textAlign: 'right'
        }};
    }}
    """)

    # ---------------------------------
    # COLUMNAS NUMÉRICAS
    # ---------------------------------
    for col in columnas_numericas:
        if col in columnas_sin_degradado:
            gb.configure_column(
                col,
                valueFormatter=value_formatter_2dec,
                cellStyle={"textAlign": "right"},
                minWidth=130
            )
        else:
            gb.configure_column(
                col,
                valueFormatter=value_formatter_2dec,
                cellStyle=degradado_js,
                minWidth=130
            )

    # ---------------------------------
    # 🚦 COLUMNA SEMÁFORO
    # ---------------------------------
    if "Semáforo" in df.columns:
        gb.configure_column(
            "Semáforo",
            minWidth=110,
            cellStyle=semaforo_cell_style,
            sortable=False
        )

    # ---------------------------------
    # TOTAL (DERECHA)
    # ---------------------------------
    if columna_total and columna_total in df.columns:
        gb.configure_column(
            columna_total,
            pinned="right",
            valueFormatter=value_formatter_2dec,
            cellStyle={
                "fontWeight": "bold",
                "textAlign": "right"
            },
            minWidth=160
        )

    # ---------------------------------
    # OPCIONES GRID
    # ---------------------------------
    grid_options = gb.build()
    grid_options.update({
        "domLayout": "normal",
        "suppressHorizontalScroll": True,
        "alwaysShowHorizontalScroll": False,
        "alwaysShowVerticalScroll": False,
        "onGridReady": JsCode("""
        function(params) {
            setTimeout(function() {
                params.api.sizeColumnsToFit();
            }, 100);
        }
        """)
    })

    # ---------------------------------
    # RENDER
    # ---------------------------------

    AgGrid(
        df,
        gridOptions=grid_options,
        theme=AgGridTheme.ALPINE,
        height=calculated_height,
        use_container_width=True,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        #key=f"aggrid_{hash(pd.util.hash_pandas_object(df).sum())}"
    )






def mostrar_tabla_matriz(
    df: pd.DataFrame,
    header_left: list,
    data_columns: list,
    header_right: list = None,
    footer_totals: dict = None,
    max_height: int = 600
):
    if df.empty:
        return

    header_right = header_right or []

    # ----------------------------
    # ALTURAS BASE
    # ----------------------------
    row_height = 35
    header_height = 42
    footer_height = 35 if footer_totals else 0

    # 🔑 BUFFER REAL DE AG GRID
    # (scroll horizontal + pinned container + padding interno)
    aggrid_buffer = 24 if footer_totals else 10

    dynamic_height = (
        header_height +
        (len(df) * row_height) +
        footer_height +
        aggrid_buffer
    )

    final_height = min(dynamic_height, max_height)

    gb = GridOptionsBuilder.from_dataframe(df)

    # ----------------------------
    # CONFIG GENERAL
    # ----------------------------
    gb.configure_default_column(
        resizable=True,
        sortable=False,
        filter=False,
        minWidth=120,
        wrapText=False
    )

    # ----------------------------
    # HEADER LEFT
    # ----------------------------
    for col in header_left:
        gb.configure_column(
            col,
            pinned="left",
            minWidth=170,
            cellStyle={
                "fontWeight": "bold",
                "backgroundColor": "#0B083D",
                "color": "white",
                "textAlign": "left"
            }
        )

    # ----------------------------
    # ESCALA GLOBAL PARA DEGRADADO
    # ----------------------------
    valores = df[data_columns].values.flatten()
    valores = valores[~pd.isna(valores)]

    min_val = float(valores.min()) if len(valores) else 0
    max_val = float(valores.max()) if len(valores) else 1

    blue_gradient_js = JsCode(f"""
        function(params) {{
            if (params.node.rowPinned) {{
                return null;
            }}

            if (params.value === null || params.value === undefined) {{
                return null;
            }}

            const min = {min_val};
            const max = {max_val};

            if (max === min) {{
                return {{
                    backgroundColor: '#E3F2FD',
                    textAlign: 'right'
                }};
            }}

            const ratio = (params.value - min) / (max - min);

            const start = [227, 242, 253];
            const end   = [21, 101, 192];

            const r = Math.round(start[0] + ratio * (end[0] - start[0]));
            const g = Math.round(start[1] + ratio * (end[1] - start[1]));
            const b = Math.round(start[2] + ratio * (end[2] - start[2]));

            return {{
                backgroundColor: `rgb(${{r}}, ${{g}}, ${{b}})`,
                color: ratio > 0.6 ? 'white' : '#0B083D',
                textAlign: 'right'
            }};
        }}
        """)



    # ----------------------------
    # DATA
    # ----------------------------
    for col in data_columns:
        gb.configure_column(
            col,
            valueFormatter=value_formatter_2dec,
            cellStyle=blue_gradient_js,
            minWidth=130
        )

    # ----------------------------
    # HEADER RIGHT
    # ----------------------------
    for col in header_right:
        gb.configure_column(
            col,
            pinned="right",
            valueFormatter=value_formatter_2dec,
            cellStyle={
                "fontWeight": "bold",
                "backgroundColor": "#0B083D",
                "color": "white",
                "textAlign": "right"
            },
            minWidth=160
        )

    grid_options = gb.build()

    # ----------------------------
    # FOOTER
    # ----------------------------

    if footer_totals:
        grid_options["pinnedBottomRowData"] = [footer_totals]

    # Aplicar estilo directo al footer
    grid_options["getRowStyle"] = JsCode("""
    function(params) {
        if (params.node.rowPinned === 'bottom') {
            return {
                backgroundColor: '#0B083D',
                color: 'white',
                fontWeight: 'bold',
                textAlign: 'right'
            }
        }
    }
    """)

    # ----------------------------
    # ALTURAS CONTROLADAS
    # ----------------------------
    grid_options["rowHeight"] = row_height
    grid_options["pinnedRowHeight"] = footer_height or row_height
    grid_options["domLayout"] = "normal"
    grid_options["alwaysShowHorizontalScroll"] = False

    AgGrid(
        df,
        gridOptions=grid_options,
        theme=AgGridTheme.ALPINE,
        height=final_height,
        use_container_width=True,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True
    )






def mostrar_tabla_normal_cloud(
    df: pd.DataFrame,
    columnas_fijas=None,
    columnas_numericas=None,
    columnas_sin_degradado=None,
    columna_total=None,
    height=600,
    resaltar_primera_columna: bool = False,
    ordenar_por: str | None = None,
    ascendente: bool = False
):
    if df.empty:
        return

    columnas_fijas = columnas_fijas or []
    columnas_numericas = columnas_numericas or []
    columnas_sin_degradado = columnas_sin_degradado or []

    df = df.copy()

    # -----------------------------
    # ORDENAMIENTO
    # -----------------------------
    if ordenar_por and ordenar_por in df.columns:
        df = df.sort_values(by=ordenar_por, ascending=ascendente)

    # -----------------------------
    # CAST NUMÉRICO SEGURO
    # -----------------------------
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # -----------------------------
    # FORMATOS (NaN -> None)
    # -----------------------------
    format_dict = {
        col: "{:,.2f}" for col in columnas_numericas if col in df.columns
    }

    # -----------------------------
    # 🎨 DEGRADADO AZUL (por columna)
    # -----------------------------
    def degradado_azul(col):
        if col.name in columnas_sin_degradado:
            return ["text-align:right;"] * len(col)

        min_val = col.min(skipna=True)
        max_val = col.max(skipna=True)

        styles = []
        for v in col:
            if pd.isna(v):
                styles.append(
                    "background-color:white; color:#0B083D; text-align:right;"
                )
                continue

            if min_val == max_val:
                styles.append(
                    "background-color:#E3F2FD; color:#0B083D; text-align:right;"
                )
                continue

            ratio = (v - min_val) / (max_val - min_val)

            r = int(227 + ratio * (21 - 227))
            g = int(242 + ratio * (101 - 242))
            b = int(253 + ratio * (192 - 253))

            color = "white" if ratio > 0.6 else "#151342"

            styles.append(
                f"""
                background-color: rgb({r},{g},{b});
                color: {color};
                text-align: right;
                """
            )

        return styles

    # -----------------------------
    # 🚦 SEMÁFORO
    # -----------------------------
    def semaforo(val):
        if val == "VERDE":
            return "background-color:#1E7E34;color:white;font-weight:bold;text-align:center;"
        if val == "AMARILLO":
            return "background-color:#FFC107;color:#212529;font-weight:bold;text-align:center;"
        if val == "ROJO":
            return "background-color:#DC3545;color:white;font-weight:bold;text-align:center;"
        return "background-color:white;text-align:center;"

    # -----------------------------
    # 🔵 PRIMERA COLUMNA
    # -----------------------------
    def primera_columna_style(col):
        if not resaltar_primera_columna:
            return ["font-weight:bold; text-align:left;"] * len(col)

        return [
            "background-color:#0B083D;color:white;font-weight:bold;text-align:left;"
        ] * len(col)

    # -----------------------------
    # STYLER BASE
    # -----------------------------
    styler = (
        df.style
        .format(format_dict, na_rep="None")
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("background-color", "#706A6ABB"),
                    ("color", "#0B083D"),
                    ("font-weight", "bold"),
                    ("text-align", "center")
                ]
            }
        ])
    )

    # Primera columna
    if columnas_fijas:
        styler = styler.apply(
            primera_columna_style,
            subset=[columnas_fijas[0]]
        )

    # Degradados numéricos
    for col in columnas_numericas:
        if col in df.columns:
            styler = styler.apply(
                degradado_azul,
                subset=[col]
            )

    # Semáforo
    if "Semáforo" in df.columns:
        styler = styler.applymap(semaforo, subset=["Semáforo"])

    # Total
    if columna_total and columna_total in df.columns:
        styler = styler.set_properties(
            subset=[columna_total],
            **{"font-weight": "bold", "text-align": "right"}
        )

    # -----------------------------
    # ALTURA DINÁMICA
    # -----------------------------
    row_height = 35
    header_height = 40
    internal_padding = 35

    calculated_height = min(
        header_height + row_height * (len(df) + 1) - internal_padding,
        height  # respeta el máximo que tú pases
    )


    # -----------------------------
    # RENDER
    # -----------------------------
    st.dataframe(
        styler,
        height=calculated_height,
        use_container_width=True,
        hide_index=True
    )
