# dashboard.py

import streamlit as st
import streamlit_authenticator as stauth

# ------------------- IMPORTS PROPIOS -------------------
from utils.config import cargar_config
from utils.api_utils import mostrar_fecha_actualizacion

# Secciones
from secciones import compras, ventas, clientes, vendedores, cancelaciones, linea

# -----------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------
st.set_page_config(
    page_title="Dashboard Refacciones",
    layout="wide"
)

# -----------------------------------------------------
# AUTENTICACIÓN
# -----------------------------------------------------
auth_config = dict(st.secrets["auth"])

credentials = {
    "usernames": {
        k: dict(v) for k, v in auth_config["credentials"]["usernames"].items()
    }
}

authenticator = stauth.Authenticate(
    credentials,
    auth_config["cookie"]["name"],
    auth_config["cookie"]["key"],
    auth_config["cookie"]["expiry_days"],
    auth_config.get("preauthorized", {}).get("emails", [])
)

# 🔑 SI NO hay estado de autenticación, mostramos login
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None

if st.session_state["authentication_status"] is None:
    name, authentication_status, username = authenticator.login(
        "Iniciar sesión",
        "main"
    )
    st.session_state["authentication_status"] = authentication_status
    st.session_state["name"] = name
    st.session_state["username"] = username

# -----------------------------------------------------
# APP PRINCIPAL
# -----------------------------------------------------
if st.session_state["authentication_status"] is True:
    user_name = st.session_state.get("name")
    config = cargar_config()

    with st.sidebar:
        # 1. Inyectamos el CSS para convertir la sidebar en un contenedor flexible
        st.markdown(
            """
            <style>
                /* Seleccionamos el contenedor interno de la sidebar */
                [data-testid="stSidebarUserContent"] {
                    display: flex;
                    flex-direction: column;
                    height: 90vh; /* Ajustamos al alto de la pantalla */
                }
                /* Creamos una clase para un div que se expandirá */
                .espaciador-flexible {
                    flex-grow: 1;
                }
            </style>
            """,
            unsafe_allow_html=True
        )

        # --- SECCIÓN SUPERIOR ---
        st.markdown(f"👋 **Bienvenida, {user_name}**")

        opcion = st.selectbox(
            "Selecciona una vista",
            [
                "Compras vs Meta",
                "Ventas",
                "Vendedores",
                "Cancelaciones",
                "Clientes / Ubicación",
                "Ventas por línea",
            ]
        )

        # 2. Insertamos el "espaciador" que empuja todo hacia abajo
        st.markdown('<div class="espaciador-flexible"></div>', unsafe_allow_html=True)

        # --- SECCIÓN INFERIOR (Todo esto quedará pegado abajo) ---
        st.divider() 

        if st.button("Limpiar datos de memoria", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        # Tu función de fecha (la caja verde)
        mostrar_fecha_actualizacion()

        # El botón de logout
        if authenticator.logout("Cerrar sesión", "sidebar"):
            st.session_state["authentication_status"] = None
            st.session_state["name"] = None
            st.session_state["username"] = None
            st.rerun()

    # ------------------- CONTENIDO PRINCIPAL -------------------
    if opcion == "Compras vs Meta":
        compras.mostrar(config)

    elif opcion == "Ventas":
        ventas.mostrar(config)

    elif opcion == "Clientes / Ubicación":
        clientes.mostrar(config)

    elif opcion == "Vendedores":
        vendedores.mostrar(config)

    elif opcion == "Cancelaciones":
        cancelaciones.mostrar(config)

    elif opcion == "Ventas por línea":
        linea.mostrar(config)

elif st.session_state["authentication_status"] is False:
    st.error("❌ Usuario o contraseña incorrectos")

else:
    st.info("🔐 Ingresa tus credenciales para continuar")

