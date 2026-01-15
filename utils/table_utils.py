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
def mostrar_tabla_normal(
    df: pd.DataFrame,
    columnas_fijas=None,
    columnas_numericas=None,
    columna_total=None,
    height=600,
    mostrar_totales=False,
    resaltar_primera_columna: bool = False
):
    if df.empty:
        return

    columnas_fijas = columnas_fijas or []
    columnas_numericas = columnas_numericas or []

    # ---------------------------------
    # ALTURA DINÁMICA (evita espacio blanco)
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
    # COLUMNAS FIJAS (LEFT)
    # ---------------------------------
    for i, col in enumerate(columnas_fijas):
        cell_class = []

        if resaltar_primera_columna and i == 0:
            cell_class.append("header-left")

        gb.configure_column(
            col,
            pinned="left",
            minWidth=160,
            cellClass=" ".join(cell_class) if cell_class else None,
            cellStyle={
                "fontWeight": "bold",
                "textAlign": "left"
            }
        )

    # ---------------------------------
    # COLUMNAS NUMÉRICAS
    # ---------------------------------
    for col in columnas_numericas:
        gb.configure_column(
            col,
            valueFormatter=value_formatter_2dec,
            cellClass="data-cell",
            cellStyle={"textAlign": "right"},
            minWidth=130
        )

    # ---------------------------------
    # COLUMNA TOTAL (RIGHT)
    # ---------------------------------
    if columna_total and columna_total in df.columns:
        gb.configure_column(
            columna_total,
            pinned="right",
            valueFormatter=value_formatter_2dec,
            cellClass="header-right",
            cellStyle={
                "fontWeight": "bold",
                "textAlign": "right"
            },
            minWidth=160
        )

    # ---------------------------------
    # OPCIONES DEL GRID
    # ---------------------------------
    grid_options = gb.build()
    grid_options.update({
        "domLayout": "normal",
        "suppressHorizontalScroll": False,
        "alwaysShowHorizontalScroll": False,
        "alwaysShowVerticalScroll": False
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
        fit_columns_on_grid_load=False,  # 👈 CLAVE
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,  # 👈 CLAVE
        allow_unsafe_jscode=True
    )



def mostrar_tabla_matriz(
    df: pd.DataFrame,
    header_left: list,
    data_columns: list,
    header_right: list = None,
    footer_totals: dict = None,
    height: int = 600
):
    if df.empty:
        return

    header_right = header_right or []

    gb = GridOptionsBuilder.from_dataframe(df)

    # ----------------------------
    # CONFIG GENERAL
    # ----------------------------
    gb.configure_default_column(
        resizable=True,
        sortable=False,
        filter=False,
        minWidth=110,
        wrapText=False
    )

    # ----------------------------
    # HEADER LEFT (INFO)
    # ----------------------------
    for col in header_left:
        gb.configure_column(
            col,
            pinned="left",
            minWidth=160,
            cellClass="header-left",
            cellStyle={
                "fontWeight": "bold",
                "backgroundColor": "#0B083D",
                "color": "white",
                "textAlign": "left"
            }
        )

    # ----------------------------
    # DATA COLUMNS
    # ----------------------------
    for col in data_columns:
        gb.configure_column(
            col,
            valueFormatter=value_formatter_2dec,
            cellClass="data-cell",
            cellStyle={"textAlign": "right"},
            minWidth=130
        )

    # ----------------------------
    # HEADER RIGHT (TOTALES H)
    # ----------------------------
    for col in header_right:
        gb.configure_column(
            col,
            pinned="right",
            valueFormatter=value_formatter_2dec,
            cellClass="header-right",
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
    # FOOTER (TOTALES V)
    # ----------------------------
    if footer_totals:
        grid_options["pinnedBottomRowData"] = [footer_totals]

    # ----------------------------
    # SCROLL & LAYOUT
    # ----------------------------
    grid_options.update({
        "domLayout": "normal",
        "suppressHorizontalScroll": False,
        "alwaysShowHorizontalScroll": False,
        "alwaysShowVerticalScroll": False
    })

    AgGrid(
        df,
        gridOptions=grid_options,
        theme=AgGridTheme.ALPINE,
        height=height,
        use_container_width=True,
        fit_columns_on_grid_load=False,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        allow_unsafe_jscode=True
    )
