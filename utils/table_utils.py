# utils/table_utils.py

import pandas as pd
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

# --------------------------------------------------
# TABLA BASE REUTILIZABLE
# --------------------------------------------------
def mostrar_tabla_aggrid(
    df: pd.DataFrame,
    columnas_fijas=None,
    columnas_numericas=None,
    columna_total=None,
    height=600,
    mostrar_totales=False
):
    if df.empty:
        return

    columnas_fijas = columnas_fijas or []
    columnas_numericas = columnas_numericas or []

    gb = GridOptionsBuilder.from_dataframe(df)

    # ----------------------------
    # CONFIGURACIÓN GENERAL
    # ----------------------------
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=False,
        minWidth=110
    )

    # ----------------------------
    # COLUMNAS FIJAS
    # ----------------------------
    for col in columnas_fijas:
        gb.configure_column(
            col,
            pinned="left",
            minWidth=160,
            cellStyle={
                "fontWeight": "bold",
                "backgroundColor": "#0B083D",
                "color": "white"
            }
        )

    # ----------------------------
    # COLUMNAS NUMÉRICAS
    # ----------------------------
    for col in columnas_numericas:
        gb.configure_column(
            col,
            valueFormatter=value_formatter_2dec,
            cellStyle={"textAlign": "right"},
            minWidth=130
        )

    # ----------------------------
    # COLUMNA TOTAL
    # ----------------------------
    if columna_total and columna_total in df.columns:
        gb.configure_column(
            columna_total,
            valueFormatter=value_formatter_2dec,
            cellStyle={
                "fontWeight": "bold",
                "backgroundColor": "#0B083D",
                "color": "white",
                "textAlign": "right"
            },
            minWidth=160
        )

    # ----------------------------
    # OPCIONES DEL GRID
    # ----------------------------
    grid_options = gb.build()
    grid_options["domLayout"] = "normal"
    grid_options["suppressHorizontalScroll"] = False
    grid_options["alwaysShowHorizontalScroll"] = True
    grid_options["alwaysShowVerticalScroll"] = True

    # ----------------------------
    # RENDER
    # ----------------------------
    AgGrid(
        df,
        gridOptions=grid_options,
        theme=AgGridTheme.ALPINE,
        height=height,
        fit_columns_on_grid_load=False,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        allow_unsafe_jscode=True,
        use_container_width=True
    )
