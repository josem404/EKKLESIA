"""
EKKLESIA — Página de Apodos
Accesible sin login. Muestra las 30 biografías y permite identificar la propia función.
"""

import json
from pathlib import Path

import streamlit as st

from core.theme import aplicar_css_global, ICONOS, COLORES
from core.grapher import plot_function, formatear_definicion_latex

st.set_page_config(
    page_title="Apodos — EKKLESIA",
    page_icon="📖",
    layout="wide",
)
aplicar_css_global()

# ── Cargar datos ──────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent


@st.cache_data
def _cargar_apodos() -> list[dict]:
    return json.loads((_ROOT / "data" / "apodos.json").read_text(encoding="utf-8"))


@st.cache_data
def _cargar_ciudadanos() -> dict:
    """Devuelve dict {ciudadano_id: ciudadano}."""
    data = json.loads((_ROOT / "data" / "ciudadanos.json").read_text(encoding="utf-8"))
    return {c["id"]: c for c in data}


apodos = _cargar_apodos()
ciudadanos = _cargar_ciudadanos()

# ── Header ────────────────────────────────────────────────────────────────────
color = COLORES.get("poder_judicial", "#6B4A5C")
st.markdown(f"""
<div class="ekk-header" style="background: linear-gradient(135deg, {color}22, {color}08);">
    <span class="ekk-header-icon">📖</span>
    <span class="ekk-header-text" style="color:{color};">Apodos de Funcionalia</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
Cada ciudadana de Funcionalia tiene un **apodo** que esconde la identidad de una mujer
relevante en la historia de las matemáticas y la ciencia. Lee tu biografía, descubre
de quién se trata e introduce el nombre para ver tu función.
""")

st.divider()

# ── Controles de búsqueda ─────────────────────────────────────────────────────
col_num, col_nombre = st.columns([1, 3])

nombres_reales = [""] + [a["nombre_real"] for a in apodos]
numeros = [""] + list(range(1, 31))

with col_num:
    num_sel = st.selectbox(
        "Nº de biografía",
        options=numeros,
        format_func=lambda v: "— Selecciona —" if v == "" else str(v),
        key="apodo_num",
    )

with col_nombre:
    nombre_sel = st.selectbox(
        "Escribe o selecciona el nombre real",
        options=nombres_reales,
        format_func=lambda v: "— Escribe para buscar —" if v == "" else v,
        key="apodo_nombre",
    )

# ── Resultado: mostrar función si el nombre es correcto ───────────────────────
if nombre_sel:
    entrada = next((a for a in apodos if a["nombre_real"] == nombre_sel), None)
    if entrada:
        # Verificar coherencia con el número seleccionado
        if num_sel and num_sel != entrada["numero"]:
            st.warning(
                f"⚠️ El nombre **{nombre_sel}** corresponde a la biografía **{entrada['numero']}**, "
                f"no a la {num_sel}."
            )
        else:
            ciudadano = ciudadanos.get(entrada["ciudadano_id"])
            if ciudadano:
                st.success(f"✅ Has descubierto el apodo: **{entrada['apodo']}**")
                st.markdown(f"*Nombre real: {nombre_sel} · Provincia: {ciudadano['provincia'].capitalize()}*")

                col_g, col_d = st.columns([1, 1])
                with col_g:
                    st.subheader("Tu función")
                    fig = plot_function(
                        ciudadano["funcion_json"],
                        alias=entrada["apodo"],
                        height=280,
                        show_title=True,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with col_d:
                    st.subheader("Definición a trozos")
                    latex_str = formatear_definicion_latex(ciudadano["funcion_json"])
                    st.latex(latex_str)

        st.divider()

# ── Lista de todas las biografías ─────────────────────────────────────────────
st.subheader("Las 30 biografías")

grupos_vistos = []
for entrada in apodos:
    # Cabecera de grupo (solo primera vez)
    if entrada["grupo"] not in grupos_vistos:
        grupos_vistos.append(entrada["grupo"])
        st.markdown(f"### {entrada['grupo']}")

    # Destacar si coincide con el número seleccionado
    destacada = (num_sel != "" and num_sel == entrada["numero"])
    borde = "#C97B4A" if destacada else "rgba(139,90,60,0.18)"
    fondo = "rgba(201,123,74,0.10)" if destacada else "transparent"

    st.markdown(f"""
<div style="
    border-left: 4px solid {borde};
    background: {fondo};
    border-radius: 0 10px 10px 0;
    padding: 0.7rem 1.1rem;
    margin-bottom: 0.6rem;
">
    <strong style="font-size:1rem;">Nº {entrada['numero']}</strong><br>
    <span style="font-size:0.95rem;">{entrada['biografia']}</span>
</div>
""", unsafe_allow_html=True)
