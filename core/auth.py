"""
Control de acceso por rol.
Las contraseñas se leen desde .streamlit/secrets.toml (en producción)
o desde variables de entorno de desarrollo.
"""

import streamlit as st

# ── Definición de roles ───────────────────────────────────────────────────────
ROLES = {
    "rey": {
        "nombre": "Su Majestad el Rey (Profesor/a)",
        "pagina_nombre": "Rey — Vista Maestra",
        "pagina_path": "pages/1_rey.py",
        "color": "#C9A24A",
        "provincia": None,
        "permisos": ["ver_todo", "editar_funciones", "añadir_propiedades", "intervenir"],
    },
    "gobierno": {
        "nombre": "Gobierno de Funcionalia",
        "pagina_nombre": "Gobierno",
        "pagina_path": "pages/2_gobierno.py",
        "color": "#8B5A3C",
        "provincia": None,
        "permisos": ["proponer_leyes", "ver_colectivos_nacionales", "gestionar_presupuesto"],
    },
    "magnitudia": {
        "nombre": "Provincia de Magnitudia",
        "pagina_nombre": "Magnitudia",
        "pagina_path": "pages/3_Magnitudia.py",
        "color": "#A68556",
        "provincia": "magnitudia",
        "permisos": ["ver_ciudadanos_propios", "crear_colectivos", "crear_asociaciones"],
    },
    "intervalia": {
        "nombre": "Provincia de Intervalia",
        "pagina_nombre": "Intervalia",
        "pagina_path": "pages/4_Intervalia.py",
        "color": "#C97B4A",
        "provincia": "intervalia",
        "permisos": ["ver_ciudadanos_propios", "crear_colectivos", "crear_asociaciones"],
    },
    "brevitas": {
        "nombre": "Provincia de Brevitas",
        "pagina_nombre": "Brevitas",
        "pagina_path": "pages/5_Brevitas.py",
        "color": "#B5533C",
        "provincia": "brevitas",
        "permisos": ["ver_ciudadanos_propios", "crear_colectivos", "crear_asociaciones"],
    },
    "poder_judicial": {
        "nombre": "Poder Judicial (CGPJ)",
        "pagina_nombre": "Poder Judicial",
        "pagina_path": "pages/6_poder_judicial.py",
        "color": "#6B4A5C",
        "provincia": None,
        "permisos": ["validar_asociaciones", "añadir_propiedades", "ver_todo_matematico"],
    },
    "congreso": {
        "nombre": "Congreso de los Diputados",
        "pagina_nombre": "Congreso",
        "pagina_path": "pages/5_congreso.py",
        "color": "#D4A24C",
        "provincia": None,
        "permisos": ["votar_leyes", "ver_leyes_pendientes"],
    },
}

# Contraseñas por defecto para desarrollo (cámbielas en producción via secrets.toml)
_PASSWORDS_DEFAULT = {
    "rey": "rey2024",
    "gobierno": "gobierno2024",
    "magnitudia": "magna2024",
    "intervalia": "inter2024",
    "brevitas": "brevi2024",
    "poder_judicial": "judicial2024",
    "congreso": "congreso2024",
}


def _get_password(rol: str) -> str:
    """Lee la contraseña desde secrets.toml si existe, sino usa el valor por defecto."""
    try:
        return st.secrets.get(f"PASSWORD_{rol.upper()}", _PASSWORDS_DEFAULT[rol])
    except Exception:
        return _PASSWORDS_DEFAULT[rol]


def verificar_credenciales(rol: str, password: str) -> bool:
    if rol not in ROLES:
        return False
    return password == _get_password(rol)


def requiere_rol(*roles_permitidos):
    """
    Guard para páginas de Streamlit.
    Uso al inicio de cada página:
        requiere_rol("rey", "poder_judicial")
    Si el rol no coincide, detiene la ejecución con st.stop().
    El rey con modo intervención activo tiene acceso a cualquier página.
    """
    rol_actual = st.session_state.get("rol")
    # El rey con intervención activa bypasea todos los guards
    if rol_actual == "rey" and st.session_state.get("intervenir"):
        return
    if rol_actual not in roles_permitidos:
        st.error("Acceso restringido. No tienes permiso para ver esta pantalla.")
        st.info("Vuelve a la página principal e inicia sesión con el rol correcto.")
        if st.button("Ir al inicio"):
            st.switch_page("main.py")
        st.stop()


def tiene_permiso(permiso: str) -> bool:
    rol = st.session_state.get("rol")
    if not rol or rol not in ROLES:
        return False
    return permiso in ROLES[rol].get("permisos", [])


def redirigir_a_pantalla(rol: str):
    """Redirige al usuario a su pantalla correspondiente."""
    if rol in ROLES:
        st.switch_page(ROLES[rol]["pagina_path"])
