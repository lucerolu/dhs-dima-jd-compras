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
            cellStyle={"fontWeight": "bold", "textAlign": "left"}
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
            cellStyle={"fontWeight": "bold", "textAlign": "right"},
            minWidth=160
        )

    # ---------------------------------
    # OPCIONES DEL GRID
    # ---------------------------------
    grid_options = gb.build()
    grid_options.update({
        "domLayout": "normal",
        "suppressHorizontalScroll": True,
        "alwaysShowHorizontalScroll": False,
        "alwaysShowVerticalScroll": False,
        "onGridReady": JsCode("""
        function(params) {
            // Ajusta columnas al ancho real del contenedor, incluso si sidebar cambia
            setTimeout(function() { params.api.sizeColumnsToFit(); }, 100);
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
        fit_columns_on_grid_load=False,  # 👈 desactivamos para que no interfiera
        allow_unsafe_jscode=True
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
    # DATA
    # ----------------------------
    for col in data_columns:
        gb.configure_column(
            col,
            valueFormatter=value_formatter_2dec,
            cellStyle={"textAlign": "right"},
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

    grid_options["getRowClass"] = JsCode("""
    function(params) {
        if (params.node.rowPinned === 'bottom') {
            return 'footer-row';
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
