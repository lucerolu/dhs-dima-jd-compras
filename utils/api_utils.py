# utils/api_utils.py

import requests
import pandas as pd
import streamlit as st
from datetime import datetime
from babel.dates import format_datetime


# =========================================================
# FUNCIÓN PARA OBTENER HEADERS (SECRETS SEGUROS)
# =========================================================
def _get_api_config():
    api_secrets = st.secrets["api"]

    return {
        "API_BASE": api_secrets["API_BASE_COMPRAS_API"],
        "HEADERS": {
            "X-API-Key": api_secrets["API_TOKEN_COMPRAS_API"]
        },
        "API_BASE_LEGACY": api_secrets["API_BASE"],
        "API_TOKEN_LEGACY": api_secrets["API_TOKEN"],
    }


# =========================================================
# FUNCIÓN GENÉRICA PARA OBTENER CUALQUIER VISTA
# =========================================================
#@st.cache_data(ttl=86400, show_spinner="Cargando datos diarios...")
def obtener_vista(nombre_vista: str) -> pd.DataFrame:
    config = _get_api_config()
    url = f"{config['API_BASE']}/api/view/{nombre_vista}"

    try:
        response = requests.get(
            url,
            headers=config["HEADERS"],
            timeout=120  # ⬅️ mejor menor
        )
        response.raise_for_status()
        data = response.json()

        return pd.DataFrame(data) if data else pd.DataFrame()

    except requests.exceptions.Timeout:
        st.error(f"⏱️ Timeout al consultar {nombre_vista}")
        return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Error al cargar la vista {nombre_vista}: {e}")
        return pd.DataFrame()



# =========================================================
# FECHA DE ACTUALIZACIÓN (API LEGACY)
# =========================================================
def mostrar_fecha_actualizacion():
    config = _get_api_config()

    url = f"{config['API_BASE_LEGACY']}/ultima_actualizacion"
    headers = {
        "Authorization": f"Bearer {config['API_TOKEN_LEGACY']}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        fecha_dt = datetime.fromisoformat(data["fecha"])

        fecha_formateada = format_datetime(
            fecha_dt,
            "d 'de' MMMM 'de' yyyy, h:mm a",
            locale="es"
        )

        st.markdown(
            f"""
            <div style="background-color:#DFF2BF;
                        color:#4F8A10;
                        padding:10px;
                        border-radius:5px;
                        margin-bottom:10px;">
                🕒 <b>Última actualización de datos:</b> {fecha_formateada}<br>
                📋 <i>{data.get("descripcion", "")}</i>
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception:
        st.warning("No se pudo obtener la fecha de actualización")

