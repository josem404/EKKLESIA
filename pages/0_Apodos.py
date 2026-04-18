"""
EKKLESIA — Página de Apodos
Accesible sin login. Muestra las 30 biografías y permite identificar la propia función.
"""

import json
import random
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

# Señuelos: mujeres importantes NO asignadas a ningún ciudadano
_SEÑUELOS = [
    "Maryam Mirzakhani",
    "Karen Uhlenbeck",
    "Ingrid Daubechies",
    "Julia Robinson",
    "Olga Ladyzhenskaya",
    "Grace Hopper",
    "Marie Curie",
    "Lise Meitner",
    "Rosalind Franklin",
    "Alicia Boole Stott",
    "Vera Rubin",
    "Chien-Shiung Wu",
    "Cecilia Payne-Gaposchkin",
    "Marjorie Rice",
    "Mildred Dresselhaus",
]


@st.cache_data
def _cargar_apodos() -> list[dict]:
    return json.loads((_ROOT / "data" / "apodos.json").read_text(encoding="utf-8"))


@st.cache_data
def _cargar_ciudadanos() -> dict:
    """Devuelve dict {ciudadano_id: ciudadano}."""
    data = json.loads((_ROOT / "data" / "ciudadanos.json").read_text(encoding="utf-8"))
    return {c["id"]: c for c in data}


@st.cache_data
def _lista_candidatas(nombres_reales_tuple: tuple) -> list[str]:
    todas = list(nombres_reales_tuple) + _SEÑUELOS
    rng = random.Random(17)
    rng.shuffle(todas)
    return todas


def _normalizar(s: str) -> str:
    """Minúsculas sin tildes ni puntuación especial."""
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _coincide_palabra(texto: str, candidata: str) -> bool:
    """True si alguna palabra completa (normalizada) del texto coincide con alguna del nombre."""
    palabras_buscadas = set(_normalizar(texto).split())
    palabras_nombre = set(_normalizar(candidata).split())
    return bool(palabras_buscadas & palabras_nombre)


apodos = _cargar_apodos()
ciudadanos = _cargar_ciudadanos()
nombres_reales_reales = tuple(a["nombre_real"] for a in apodos)
candidatas = _lista_candidatas(nombres_reales_reales)

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

numeros = [""] + list(range(1, 31))

with col_num:
    num_sel = st.selectbox(
        "Nº de biografía",
        options=numeros,
        format_func=lambda v: "— Selecciona —" if v == "" else str(v),
        key="apodo_num",
    )

nombre_sel = ""
with col_nombre:
    busqueda = st.text_input(
        "Escribe el nombre real",
        key="apodo_busqueda",
        placeholder="Escribe al menos una palabra completa del nombre…",
    )
    if busqueda and busqueda.strip():
        filtradas = [n for n in candidatas if _coincide_palabra(busqueda.strip(), n)]
        if filtradas:
            nombre_sel = st.selectbox(
                "Selecciona de las coincidencias:",
                options=[""] + filtradas,
                format_func=lambda v: "— Elige —" if v == "" else v,
                key="apodo_nombre",
            )
        else:
            st.caption("Ninguna coincidencia exacta en alguna palabra. Prueba con el nombre completo.")

# ── Resultado: mostrar función solo si AMBOS (número y nombre) son correctos ──
if nombre_sel:
    if not num_sel:
        st.info("Selecciona también un número de biografía para verificar.")
    else:
        entrada = next((a for a in apodos if a["nombre_real"] == nombre_sel), None)
        if not entrada:
            st.info(f"**{nombre_sel}** es una mujer importante en la ciencia, pero no tiene función asignada en Funcionalia. Sigue buscando.")
        elif num_sel != entrada["numero"]:
            st.warning("⚠️ Ese nombre no se corresponde con el número de biografía seleccionado.")
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
