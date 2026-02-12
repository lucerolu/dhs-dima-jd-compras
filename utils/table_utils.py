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
        st.warning("El DataFrame está vacío.")
        return

    # --- INYECCIÓN DE CSS PARA EL HEADER BLANCO ---
    # Esto afecta a los headers de st.dataframe en la app
    st.markdown("""
        <style>
            /* Cambia el fondo del header de la tabla a blanco */
            .stDataFrame thead tr th {
                background-color: white !important;
                color: #0B083D !important;
                font-weight: bold !important;
                border-bottom: 1px solid #dee2e6 !important;
            }
            /* Opcional: quitar bordes molestos o ajustar fuentes */
            [data-testid="stTable"] {
                font-family: sans-serif;
            }
        </style>
    """, unsafe_allow_html=True)

    columnas_fijas = columnas_fijas or []
    columnas_numericas = columnas_numericas or []
    columnas_sin_degradado = columnas_sin_degradado or []

    df = df.copy()

    # Ordenamiento
    if ordenar_por and ordenar_por in df.columns:
        df = df.sort_values(by=ordenar_por, ascending=ascendente)

    # Cast numérico
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Formatos
    format_dict = {
        col: "{:,.2f}" for col in columnas_numericas if col in df.columns
    }

    # --- FUNCIONES DE ESTILO ---
    def degradado_azul(col):
        if col.name in columnas_sin_degradado:
            return ["text-align:right;"] * len(col)
        
        # Evitar errores si todo es NaN
        if col.isnull().all():
            return [""] * len(col)

        min_val = col.min(skipna=True)
        max_val = col.max(skipna=True)

        styles = []
        for v in col:
            if pd.isna(v):
                styles.append("background-color:white; color:#0B083D; text-align:right;")
                continue
            if min_val == max_val:
                styles.append("background-color:#E3F2FD; color:#0B083D; text-align:right;")
                continue

            ratio = (v - min_val) / (max_val - min_val)
            r = int(227 + ratio * (21 - 227))
            g = int(242 + ratio * (101 - 242))
            b = int(253 + ratio * (192 - 253))
            color = "white" if ratio > 0.6 else "#151342"
            styles.append(f"background-color: rgb({r},{g},{b}); color: {color}; text-align: right;")
        return styles

    def semaforo(val):
        if val == "VERDE":
            return "background-color:#1E7E34;color:white;font-weight:bold;text-align:center;"
        if val == "AMARILLO":
            return "background-color:#FFC107;color:#212529;font-weight:bold;text-align:center;"
        if val == "ROJO":
            return "background-color:#DC3545;color:white;font-weight:bold;text-align:center;"
        return "background-color:transparent;text-align:center;"

    def primera_columna_style(col):
        if not resaltar_primera_columna:
            return ["font-weight:bold; text-align:left;"] * len(col)
        return ["background-color:#0B083D;color:white;font-weight:bold;text-align:left;"] * len(col)

    # --- STYLER ---
    styler = df.style.format(format_dict, na_rep="-")

    # Aplicar estilos
    if columnas_fijas:
        styler = styler.apply(primera_columna_style, subset=[columnas_fijas[0]])

    for col in columnas_numericas:
        if col in df.columns:
            styler = styler.apply(degradado_azul, subset=[col])

    if "Semáforo" in df.columns:
        # Usamos .map en lugar de .applymap (Pandas moderno)
        styler = styler.map(semaforo, subset=["Semáforo"])

    if columna_total and columna_total in df.columns:
        styler = styler.set_properties(
            subset=[columna_total],
            **{"font-weight": "bold", "text-align": "right"}
        )

    # Altura dinámica corregida
    row_height = 35
    header_height = 45
    calculated_height = min(header_height + (row_height * len(df)), height)

    st.dataframe(
        styler,
        height=calculated_height,
        use_container_width=True,
        hide_index=True
    )





def mostrar_tabla_matriz_html(
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
    
    # --- CÁLCULO DE ESCALA GLOBAL PARA DEGRADADO ---
    valores = df[data_columns].values.flatten()
    valores = valores[~pd.isna(valores)].astype(float)
    min_val = valores.min() if valores.size > 0 else 0
    max_val = valores.max() if valores.size > 0 else 1

    def get_color(val):
        if pd.isna(val): return "background-color: #ffffff; color: #0B083D;"
        ratio = (float(val) - min_val) / (max_val - min_val) if max_val != min_val else 0
        r = int(227 + ratio * (21 - 227))
        g = int(242 + ratio * (101 - 242))
        b = int(253 + ratio * (192 - 253))
        text_color = "white" if ratio > 0.6 else "#0B083D"
        return f"background-color: rgb({r},{g},{b}); color: {text_color};"

    # --- CONSTRUCCIÓN DEL HTML ---
    html = f"""
    <style>
        .table-outer-wrapper {{
            width: 100%;
            background-color: transparent;
            padding-bottom: 2px;
        }}
        .table-container {{
            height: auto;
            max-height: {max_height}px;
            overflow: auto;
            border: none;
            position: relative;
            background-color: transparent;
        }}
        table {{
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 0.85rem;
            background-color: white;
            border: 1px solid #f0f2f6;
        }}
        /* Estilo General del Header (Blanco) */
        thead th {{
            position: sticky;
            top: 0;
            background-color: white !important;
            color: #0B083D !important;
            z-index: 10;
            border-bottom: 2px solid #e6e9ef;
            border-right: 1px solid #f0f2f6;
            padding: 12px 10px;
            text-align: center;
        }}
        /* Header Pinned (Izquierda y Derecha pero en Blanco) */
        thead th.pinned-header-left {{
            position: sticky;
            left: 0;
            z-index: 20; /* Mayor que el resto del header */
            border-right: 2px solid #e6e9ef !important;
        }}
        thead th.pinned-header-right {{
            position: sticky;
            right: 0;
            z-index: 20;
            border-left: 2px solid #e6e9ef !important;
        }}
        
        /* Celdas del Cuerpo Pinned (Azules) */
        .sticky-left {{
            position: sticky;
            left: 0;
            background-color: #0B083D !important;
            color: white !important;
            font-weight: bold;
            z-index: 5;
            border-right: 2px solid #e6e9ef !important;
        }}
        .sticky-right {{
            position: sticky;
            right: 0;
            background-color: #0B083D !important;
            color: white !important;
            font-weight: bold;
            z-index: 5;
            border-left: 2px solid #e6e9ef !important;
        }}

        /* Footer Fijo */
        tfoot td {{
            position: sticky;
            bottom: 0;
            background-color: #0B083D !important;
            color: white !important;
            font-weight: bold;
            z-index: 10;
            padding: 10px;
            border-top: 2px solid #e6e9ef;
        }}
        /* Esquinas del Footer */
        tfoot td.sticky-left {{ z-index: 15; }}
        tfoot td.sticky-right {{ z-index: 15; }}

        td {{
            padding: 8px 12px;
            border-bottom: 1px solid #f0f2f6;
            border-right: 1px solid #f0f2f6;
            white-space: nowrap;
            background-color: white; 
            color: #0B083D;
        }}

        .table-container::-webkit-scrollbar {{ width: 7px; height: 7px; }}
        .table-container::-webkit-scrollbar-track {{ background: transparent; }}
        .table-container::-webkit-scrollbar-thumb {{ background: #d1d5db; border-radius: 10px; }}
        .table-container::-webkit-scrollbar-thumb:hover {{ background: #9ca3af; }}
    </style>
    <div class="table-outer-wrapper">
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        {"".join([
                            f'<th class="'
                            f'{"pinned-header-left" if c in header_left else "pinned-header-right" if c in header_right else ""}'
                            f'">{c}</th>' 
                            for c in df.columns
                        ])}
                    </tr>
                </thead>
                <tbody>
    """

    for _, row in df.iterrows():
        html += "<tr>"
        for col in df.columns:
            val = row[col]
            clase = ""
            if col in header_left: clase = "sticky-left"
            elif col in header_right: clase = "sticky-right"
            
            display_val = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
            if pd.isna(val): display_val = "-"

            if col in data_columns:
                estilo_celda = get_color(val)
            else:
                estilo_celda = "background-color: white;" if clase == "" else ""

            html += f'<td class="{clase}" style="{estilo_celda}">{display_val}</td>'
        html += "</tr>"

    if footer_totals:
        html += "<tfoot><tr>"
        for col in df.columns:
            clase = ""
            if col in header_left: clase = "sticky-left"
            elif col in header_right: clase = "sticky-right"
            val = footer_totals.get(col, "")
            display_val = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
            html += f'<td class="{clase}">{display_val}</td>'
        html += "</tr></tfoot>"

    html += "</table></div></div>"
    
    st.write(html, unsafe_allow_html=True)





def mostrar_tabla_html_pro(
    df: pd.DataFrame,
    columnas_fijas=None, # Las que van en azul marino a la izquierda
    columnas_numericas=None,
    columnas_sin_degradado=None,
    resaltar_primera_columna: bool = False,
    max_height: int = 600,
    footer_totals: dict = None
):
    if df.empty:
        return

    columnas_fijas = columnas_fijas or []
    columnas_numericas = columnas_numericas or []
    columnas_sin_degradado = columnas_sin_degradado or []

    # --- LÓGICA DE COLORES (POR COLUMNA) ---
    def get_color_columna(val, col_name):
        if pd.isna(val) or col_name in columnas_sin_degradado:
            return "background-color: white; color: #0B083D;"
        
        # Obtener min/max solo de esta columna para el degradado
        col_data = df[col_name]
        min_v = col_data.min()
        max_v = col_data.max()
        
        if min_v == max_v:
            return "background-color: #E3F2FD; color: #0B083D;"
            
        ratio = (float(val) - min_v) / (max_v - min_v) if max_v != min_v else 0
        r = int(227 + ratio * (21 - 227))
        g = int(242 + ratio * (101 - 242))
        b = int(253 + ratio * (192 - 253))
        text_color = "white" if ratio > 0.6 else "#0B083D"
        return f"background-color: rgb({r},{g},{b}); color: {text_color};"

    def get_semaforo(val):
        colors = {
            "VERDE": "background-color:#1E7E34;color:white;",
            "AMARILLO": "background-color:#FFC107;color:#212529;",
            "ROJO": "background-color:#DC3545;color:white;"
        }
        return colors.get(val, "background-color:transparent;") + "font-weight:bold;text-align:center;"

    # --- CONSTRUCCIÓN DEL HTML ---
    html = f"""
    <style>
        .table-outer-wrapper {{ width: 100%; background-color: transparent; padding-bottom: 2px; }}
        .table-container {{ 
            height: auto; max-height: {max_height}px; overflow: auto; 
            position: relative; background-color: transparent; 
        }}
        table {{ 
            border-collapse: separate; border-spacing: 0; width: 100%; 
            font-family: 'Segoe UI', sans-serif; font-size: 0.85rem; 
            background-color: white; border: 1px solid #f0f2f6;
        }}
        
        /* Headers */
        thead th {{
            position: sticky; top: 0; background-color: white !important;
            color: #0B083D; z-index: 10; border-bottom: 2px solid #e6e9ef;
            border-right: 1px solid #f0f2f6; padding: 12px 10px; text-align: center;
        }}
        thead th.sticky-col {{ 
            position: sticky; left: 0; z-index: 20; 
            border-right: 2px solid #e6e9ef !important; 
        }}

        /* Filas Ancladas (Izquierda) */
        .sticky-left-cell {{
            position: sticky; left: 0; background-color: #0B083D !important;
            color: white !important; font-weight: bold; z-index: 5;
            border-right: 2px solid #e6e9ef !important;
        }}

        /* Footer */
        tfoot td {{
            position: sticky; bottom: 0; background-color: #0B083D !important;
            color: white !important; font-weight: bold; z-index: 10;
            padding: 10px; border-top: 2px solid #e6e9ef;
        }}
        tfoot td.sticky-left-cell {{ z-index: 15; }}

        td {{ 
            padding: 8px 12px; border-bottom: 1px solid #f0f2f6; 
            border-right: 1px solid #f0f2f6; white-space: nowrap; 
        }}

        /* Scrollbar custom */
        .table-container::-webkit-scrollbar {{ width: 7px; height: 7px; }}
        .table-container::-webkit-scrollbar-thumb {{ background: #d1d5db; border-radius: 10px; }}
    </style>
    <div class="table-outer-wrapper">
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        {"".join([f'<th class="{"sticky-col" if c in columnas_fijas else ""}">{c}</th>' for c in df.columns])}
                    </tr>
                </thead>
                <tbody>
    """

    for _, row in df.iterrows():
        html += "<tr>"
        for col in df.columns:
            val = row[col]
            clase = "sticky-left-cell" if col in columnas_fijas else ""
            
            # Estilo dinámico
            estilo = ""
            if col == "Semáforo":
                estilo = get_semaforo(val)
            elif col in columnas_numericas:
                estilo = get_color_columna(val, col) + "text-align: right;"
            elif col in columnas_fijas:
                # Si no queremos que la primera columna sea azul marino, quitamos esta clase
                if not resaltar_primera_columna:
                    clase = "" 
                    estilo = "font-weight: bold; background-color: white;"
            else:
                estilo = "background-color: white; color: #0B083D;"

            display_val = f"{val:,.2f}" if isinstance(val, (int, float)) and col != "Semáforo" else str(val)
            if pd.isna(val) or val == "None": display_val = "-"

            html += f'<td class="{clase}" style="{estilo}">{display_val}</td>'
        html += "</tr>"

    if footer_totals:
        html += "<tfoot><tr>"
        for col in df.columns:
            clase = "sticky-left-cell" if col in columnas_fijas else ""
            val = footer_totals.get(col, "")
            display_val = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
            html += f'<td class="{clase}">{display_val}</td>'
        html += "</tr></tfoot>"

    html += "</table></div></div>"
    st.write(html, unsafe_allow_html=True)





def mostrar_tabla_normal_html(
    df: pd.DataFrame,
    columnas_fijas=None,
    columnas_numericas=None,
    columnas_sin_degradado=None,
    columna_total=None,
    max_height=600,
    resaltar_primera_columna: bool = False
):
    if df.empty:
        return

    columnas_fijas = columnas_fijas or []
    columnas_numericas = columnas_numericas or []
    columnas_sin_degradado = columnas_sin_degradado or []

    # --- LÓGICA DE DEGRADADO POR COLUMNA ---
    stats_columnas = {}
    for col in columnas_numericas:
        if col in df.columns and col not in columnas_sin_degradado:
            col_data = pd.to_numeric(df[col], errors='coerce')
            stats_columnas[col] = {
                "min": col_data.min(),
                "max": col_data.max()
            }

    def get_color_por_columna(val, col_name):
        if col_name not in stats_columnas or pd.isna(val):
            return "background-color: white; color: #0B083D;"
        stats = stats_columnas[col_name]
        min_v, max_v = stats["min"], stats["max"]
        if max_v == min_v:
            return "background-color: #E3F2FD; color: #0B083D;"
        ratio = (float(val) - min_v) / (max_v - min_v)
        r = int(227 + ratio * (21 - 227))
        g = int(242 + ratio * (101 - 242))
        b = int(253 + ratio * (192 - 253))
        text_color = "white" if ratio > 0.6 else "#0B083D"
        return f"background-color: rgb({r},{g},{b}); color: {text_color};"

    # --- CSS ---
    html = f"""
    <style>
        .table-outer-wrapper {{ width: 100%; background-color: transparent; }}
        .table-container {{
            height: auto;
            max-height: {max_height}px;
            overflow: auto;
            position: relative;
        }}
        table {{
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            font-family: sans-serif;
            font-size: 0.85rem;
            background-color: white;
            border: 1px solid #d1d5db;
        }}
        th, td {{
            border: 1px solid #d1d5db !important;
            padding: 8px 12px;
            white-space: nowrap;
        }}
        thead th {{
            position: sticky;
            top: 0;
            background-color: white !important;
            color: #0B083D !important;
            z-index: 10;
            text-align: left;
        }}
        thead th:first-child {{ text-align: right !important; }}
        .h-pinned-left {{ position: sticky; left: 0; z-index: 20; border-right: 2px solid #d1d5db !important; }}
        .h-pinned-right {{ position: sticky; right: 0; z-index: 20; border-left: 2px solid #d1d5db !important; }}
        .cell-pinned-left {{ position: sticky; left: 0; z-index: 5; font-weight: bold; border-right: 2px solid #d1d5db !important; }}
        .cell-pinned-right {{ position: sticky; right: 0; z-index: 5; font-weight: bold; border-left: 2px solid #d1d5db !important; background-color: #F8F9FA !important; }}
        .table-container::-webkit-scrollbar {{ width: 7px; height: 7px; }}
        .table-container::-webkit-scrollbar-thumb {{ background: #d1d5db; border-radius: 10px; }}
    </style>
    <div class="table-outer-wrapper">
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        {"".join([f'<th class="{"h-pinned-left" if c in columnas_fijas else "h-pinned-right" if c == columna_total else ""}" style="text-align: {"right" if i == 0 else "left"}">{c}</th>' for i, c in enumerate(df.columns)])}
                    </tr>
                </thead>
                <tbody>
    """

    # --- CUERPO ---
    for _, row in df.iterrows():
        html += "<tr>"
        for i, col in enumerate(df.columns):
            val = row[col]
            clase = ""
            estilo_extra = ""
            alineacion = "text-align: right;" if i == 0 else "text-align: left;"
            
            # 1. Lógica de Semáforo
            if col == "Semáforo":
                color_bg = "white"
                color_txt = "#0B083D"
                val_str = str(val).upper()
                if "VERDE" in val_str: color_bg = "#28a745"; color_txt = "white"
                elif "AMARILLO" in val_str: color_bg = "#ffc107"; color_txt = "#0B083D"
                elif "ROJO" in val_str: color_bg = "#dc3545"; color_txt = "white"
                estilo_extra = f"background-color: {color_bg}; color: {color_txt}; font-weight: bold; text-align: center;"
            
            # 2. Determinar anclajes
            elif col in columnas_fijas:
                clase = "cell-pinned-left"
                if i == 0 and resaltar_primera_columna:
                    estilo_extra = f"background-color: #0B083D; color: white; {alineacion}"
                else:
                    estilo_extra = f"background-color: white; color: #0B083D; {alineacion}"
            elif col == columna_total:
                clase = "cell-pinned-right"
                estilo_extra = f"color: #0B083D; {alineacion}"

            # 3. Determinar Degradado
            if col in columnas_numericas and col not in columnas_sin_degradado and col != "Semáforo":
                estilo_extra += get_color_por_columna(val, col)
                estilo_extra += alineacion 
            elif not estilo_extra:
                estilo_extra = f"background-color: white; color: #0B083D; {alineacion}"

            # Formato de visualización
            if pd.isna(val):
                display_val = "-"
            elif isinstance(val, (int, float)):
                if "%" in col or "Variación" in col:
                    v = val * 100 if abs(val) <= 1.5 else val
                    display_val = f"{v:,.1f}%"
                else:
                    display_val = f"{val:,.2f}"
            else:
                display_val = str(val)
            
            html += f'<td class="{clase}" style="{estilo_extra}">{display_val}</td>'
        html += "</tr>"

    html += "</tbody></table></div></div>"
    st.write(html, unsafe_allow_html=True)