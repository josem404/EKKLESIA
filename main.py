"""
EKKLESIA — Motor de "La Riqueza de las Funciones"
Pantalla de login y router de roles.
"""

import streamlit as st
from core.auth import ROLES, verificar_credenciales
from core.theme import aplicar_css_global, aplicar_fondo_main

st.set_page_config(
    page_title="EKKLESIA — Funcionalia",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed",
)
aplicar_css_global()
aplicar_fondo_main()

# ── Ocultar navegación nativa de Streamlit para no-autenticados ──────────────
if "rol" not in st.session_state or st.session_state.rol is None:
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)


def pantalla_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # ── Recuadro 1: título ──────────────────────────────────────────────
        st.markdown("""
        <div class="ekk-glass" style="text-align:center; padding: 1.4rem 1.8rem;">
            <h2 style="margin:0 0 0.3rem 0; font-size:1.9rem; letter-spacing:0.02em;"> ⚖️ EKKLESIA</h2>
            <div style="font-size:1.2rem; opacity:0.85;">Estado de Funcionalia</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Recuadro 2: formulario (glass aplicado por CSS a stForm) ────────
        with st.form("login_form", clear_on_submit=False):
            st.markdown("**Identifícate para acceder a tu pantalla:**")
            rol_seleccionado = st.selectbox(
                "Rol institucional",
                options=list(ROLES.keys()),
                format_func=lambda k: ROLES[k]["nombre"],
            )
            password = st.text_input(
                "Contraseña",
                type="password",
                placeholder="Introduce la contraseña de acceso",
            )
            submitted = st.form_submit_button(
                "Acceder",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if verificar_credenciales(rol_seleccionado, password):
                st.session_state.rol = rol_seleccionado
                st.session_state.provincia = ROLES[rol_seleccionado].get("provincia")
                st.success(f"Bienvenido/a — {ROLES[rol_seleccionado]['nombre']}")
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")

        # ── Recuadro 3: pie ─────────────────────────────────────────────────
        st.markdown("""
        <div class="ekk-glass" style="text-align:center; padding: 0.7rem 1.4rem;">
            <small>Cada dispositivo debe identificarse con su rol antes de participar.</small>
        </div>
        """, unsafe_allow_html=True)


def pantalla_principal():
    rol  = st.session_state.rol
    info = ROLES[rol]

    # Dividir nombre en parte principal y paréntesis (si lo hay)
    _nombre_parts = info['nombre'].split(' (', 1)
    _nombre_principal = _nombre_parts[0]
    _nombre_sub = (f'<div style="font-size:1rem;opacity:0.75;margin-top:0.15rem;">({_nombre_parts[1]}</div>'
                   if len(_nombre_parts) > 1 else '')
    _nav_style = "margin-top:0.8rem;background:rgba(201,123,74,0.14);border-left:3px solid rgba(201,123,74,0.7);border-radius:0 8px 8px 0;padding:0.5rem 1rem;font-size:0.92rem;text-align:left;"
    _bienvenida_html = (
        f'<div class="ekk-glass" style="text-align:center;">'
        f'<h2 style="margin:0 0 0.3rem 0;font-size:1.9rem;letter-spacing:0.02em;"> ⚖️ EKKLESIA</h2>'
        f'<div style="font-size:1.2rem;font-weight:600;">{_nombre_principal}</div>'
        f'{_nombre_sub}'
        f'<div style="{_nav_style}">Accede a tu pantalla desde el menú lateral izquierdo → '
        f'<strong>{info["pagina_nombre"]}</strong></div>'
        f'</div>'
    )

    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        # ── Recuadro 1: bienvenida ──────────────────────────────────────────
        st.markdown(_bienvenida_html, unsafe_allow_html=True)

        # ── Recuadro 2: estado global ───────────────────────────────────────
        try:
            from core.db import get_estado_global
            estado  = get_estado_global()
            turno   = estado.get("turno", 1)
            bloques = estado.get("total_bloques", 300)
            leyes   = estado.get("leyes_promulgadas", 0)
            asocs   = estado.get("asociaciones", 0)
            st.markdown(f"""
            <div class="ekk-glass">
                <h3 style="margin:0 0 1rem 0;">Estado de Funcionalia</h3>
                <div style="
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 0.6rem;
                    text-align: center;
                ">
                    <div>
                        <div style="font-size:2rem;font-weight:700;color:#C97B4A;">{turno}</div>
                        <small>Turno actual</small>
                    </div>
                    <div>
                        <div style="font-size:2rem;font-weight:700;color:#C97B4A;">{bloques}</div>
                        <small>Total bloques</small>
                    </div>
                    <div>
                        <div style="font-size:2rem;font-weight:700;color:#C97B4A;">{leyes}</div>
                        <small>Leyes promulgadas</small>
                    </div>
                    <div>
                        <div style="font-size:2rem;font-weight:700;color:#C97B4A;">{asocs}</div>
                        <small>Asociaciones</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.markdown("""
            <div class="ekk-glass">
                <p style="margin:0;">
                    Base de datos no configurada. Configura Supabase en
                    <code>.streamlit/secrets.toml</code>.
                </p>
            </div>
            """, unsafe_allow_html=True)

        # ── Botón de cierre de sesión ───────────────────────────────────────
        if st.button("Cerrar sesión", type="secondary"):
            st.session_state.clear()
            st.rerun()


# ── Enrutador principal ───────────────────────────────────────────────────────
if "rol" not in st.session_state or st.session_state.rol is None:
    pantalla_login()
else:
    pantalla_principal()
