"""
Sistema de diseño de EKKLESIA — Funcionalia.
Paleta pastel naranja/marrón/beige (modo claro) y marrón oscuro/ámbar (modo oscuro).
Fuente única de verdad para colores, iconos, CSS global, banners y retratos.
"""

import base64
import functools
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ── Tokens paleta CLARO ──────────────────────────────────────────────────────
_TOKENS_LIGHT = {
    "fondo":           "#FAF3E7",
    "fondo_alt":       "#F0E4D0",
    "fondo_hover":     "#E8D9BF",
    "primario":        "#C97B4A",
    "primario_oscuro": "#8B5A3C",
    "secundario":      "#E4B07A",
    "texto":           "#3B2A1E",
    "texto_suave":     "#7A5C46",
    "borde":           "rgba(139,90,60,0.18)",
    "exito":           "#8BA878",
    "aviso":           "#D4A24C",
    "error":           "#B5533C",
    "modo_bg_card":    "#fff",
}

# ── Tokens paleta OSCURO ─────────────────────────────────────────────────────
_TOKENS_DARK = {
    "fondo":           "#1A1008",
    "fondo_alt":       "#2A1C0E",
    "fondo_hover":     "#3A2A18",
    "primario":        "#E4A060",
    "primario_oscuro": "#C97B4A",
    "secundario":      "#A06830",
    "texto":           "#F5E8D4",
    "texto_suave":     "#B89070",
    "borde":           "rgba(228,160,96,0.20)",
    "exito":           "#A8C890",
    "aviso":           "#E4C060",
    "error":           "#D07858",
    "modo_bg_card":    "#2A1C0E",
}


def _tokens() -> dict:
    return _TOKENS_DARK if st.session_state.get("dark_mode") else _TOKENS_LIGHT


# ── Colores por rol ───────────────────────────────────────────────────────────
COLORES = {
    "rey":             "#C9A24A",
    "gobierno":        "#8B5A3C",
    "magnitudia":      "#A68556",
    "intervalia":      "#C97B4A",
    "brevitas":        "#B5533C",
    "poder_judicial":  "#6B4A5C",
    "congreso":        "#D4A24C",
}

# ── Iconos ────────────────────────────────────────────────────────────────────
ICONOS = {
    "rey":             "👑",
    "gobierno":        "🏛️",
    "magnitudia":      "🏔️",
    "intervalia":      "🌊",
    "brevitas":        "⚡",
    "poder_judicial":  "⚖️",
    "congreso":        "🗳️",
    "colectivo":       "👥",
    "asociacion":      "🔗",
    "ley":             "📜",
    "propiedad":       "🔢",
    "grafica":         "📈",
    "bloques":         "🧱",
}

# ── Nombres ───────────────────────────────────────────────────────────────────
NOMBRES_PROVINCIA = {
    "magnitudia": "Magnitudia",
    "intervalia": "Intervalia",
    "brevitas": "Brevitas",
}


# ── Cache de imágenes base64 ──────────────────────────────────────────────────

@functools.lru_cache(maxsize=64)
def _img_b64(path_str: str) -> tuple[str, str]:
    """(ext, base64_data) cacheados por ruta."""
    p = Path(path_str)
    data = base64.b64encode(p.read_bytes()).decode()
    ext = p.suffix.lstrip(".").lower()
    return ext, data


_EKKLESIA_ROOT = Path(__file__).parent.parent  # ekklesia/


def _assets(filename: str) -> Path:
    """Ruta absoluta a ekklesia/assets/<filename>."""
    return _EKKLESIA_ROOT / "assets" / filename


def _portraits_dir() -> Path:
    # Carpeta de retratos movida fuera del proyecto
    return _EKKLESIA_ROOT.parent / "Iconos e imagenes" / "Portraits"


# ── CSS global ────────────────────────────────────────────────────────────────

def aplicar_css_global():
    """Inyecta CSS global (sensible al modo claro/oscuro) y el toggle de modo."""
    # Toggle dark mode en sidebar
    # Toggle de modo oscuro — desactivado temporalmente (pendiente mejora CSS)
    # dark = st.sidebar.toggle("🌙 Modo oscuro", value=st.session_state.get("dark_mode", False),
    #                          key="dark_mode")
    dark = st.session_state.get("dark_mode", False)

    t = _tokens()
    dm = st.session_state.get("dark_mode", False)
    bg_img_tint = "rgba(26,16,8,0.72)" if dm else "rgba(250,243,231,0.82)"

    # Desactivar autocompletado
    components.html("""
    <script>
    (function() {
        function disableAutocomplete() {
            try {
                var doc = window.parent.document;
                doc.querySelectorAll('input[type="text"], input:not([type])').forEach(function(el) {
                    el.setAttribute('autocomplete', 'new-password');
                    el.setAttribute('name', 'ekk-' + Math.random().toString(36).slice(2));
                });
            } catch(e) {}
        }
        disableAutocomplete();
        try {
            var observer = new MutationObserver(disableAutocomplete);
            observer.observe(window.parent.document.body, { childList: true, subtree: true });
        } catch(e) {}
    })();
    </script>
    """, height=0)

    st.markdown(f"""
    <style>
    :root {{
        --ekk-fondo: {t['fondo']};
        --ekk-fondo-alt: {t['fondo_alt']};
        --ekk-fondo-hover: {t['fondo_hover']};
        --ekk-primario: {t['primario']};
        --ekk-primario-oscuro: {t['primario_oscuro']};
        --ekk-secundario: {t['secundario']};
        --ekk-texto: {t['texto']};
        --ekk-texto-suave: {t['texto_suave']};
        --ekk-borde: {t['borde']};
        --ekk-exito: {t['exito']};
        --ekk-aviso: {t['aviso']};
        --ekk-error: {t['error']};
        --ekk-card-bg: {t['modo_bg_card']};
        --ekk-banner-tint: {bg_img_tint};
    }}

    /* ── Base ── */
    .stApp {{ background: var(--ekk-fondo) !important; color: var(--ekk-texto) !important; }}
    .block-container {{ padding-top: 1.5rem; }}
    section[data-testid="stSidebar"] {{
        background: var(--ekk-fondo-alt) !important;
    }}
    h1, h2, h3, h4 {{
        color: var(--ekk-primario-oscuro) !important;
        font-family: Georgia, serif;
    }}

    /* ── Botones ── */
    .stButton > button, .stFormSubmitButton > button {{
        background: var(--ekk-primario) !important;
        color: #fff !important;
        border: 1px solid var(--ekk-primario-oscuro) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.15s ease;
    }}
    .stButton > button:hover, .stFormSubmitButton > button:hover {{
        background: var(--ekk-primario-oscuro) !important;
    }}

    /* ── Inputs ── */
    .stTextInput input, .stNumberInput input, .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div {{
        background: var(--ekk-card-bg) !important;
        color: var(--ekk-texto) !important;
        border-radius: 8px !important;
        border: 1px solid var(--ekk-borde) !important;
    }}

    /* ── Tarjetas ── */
    .ekk-card {{
        background: var(--ekk-fondo-alt);
        border: 1px solid var(--ekk-borde);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }}
    .ekk-card h4 {{ margin-top: 0; }}

    /* ── Header temático ── */
    .ekk-header {{
        display: flex;
        align-items: center;
        gap: 0.7rem;
        padding: 0.9rem 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid var(--ekk-borde);
    }}
    .ekk-header-icon {{ font-size: 1.8rem; }}
    .ekk-header-text {{ font-size: 1.5rem; font-weight: 700; font-family: Georgia, serif; }}

    /* ── Badges de provincia ── */
    .ekk-badge {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #fff;
    }}
    .ekk-badge-magnitudia {{ background: {COLORES['magnitudia']}; }}
    .ekk-badge-intervalia  {{ background: {COLORES['intervalia']}; }}
    .ekk-badge-brevitas    {{ background: {COLORES['brevitas']}; }}
    .ekk-badge-nacional    {{ background: {COLORES['gobierno']}; }}

    /* ── Estados ── */
    .ekk-status {{
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 12px; border-radius: 20px;
        font-size: 0.85rem; font-weight: 500;
    }}
    .ekk-status-pendiente {{ background: rgba(212,162,76,0.18); color: {_TOKENS_LIGHT['aviso']}; border: 1px solid rgba(212,162,76,0.35); }}
    .ekk-status-aprobada  {{ background: rgba(139,168,120,0.18); color: {_TOKENS_LIGHT['exito']}; border: 1px solid rgba(139,168,120,0.35); }}
    .ekk-status-rechazada {{ background: rgba(181,83,60,0.18);   color: {_TOKENS_LIGHT['error']}; border: 1px solid rgba(181,83,60,0.35); }}

    /* ── IDs racionales ── */
    .ekk-id-unico    {{ color: var(--ekk-exito); font-weight: bold; }}
    .ekk-id-colision {{ color: var(--ekk-error); font-weight: bold; }}

    /* ── Retratos inline ── */
    .ekk-retrato {{
        display: inline-block;
        vertical-align: middle;
        image-rendering: pixelated;
        border-radius: 4px;
        margin: 0 4px;
    }}
    .ekk-ciudadano {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        white-space: nowrap;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px 10px 0 0;
        padding: 8px 16px;
        background: var(--ekk-fondo-alt);
        color: var(--ekk-texto-suave);
    }}
    .stTabs [aria-selected="true"] {{
        background: var(--ekk-primario) !important;
        color: #fff !important;
    }}

    /* ── Banner imagen ── */
    .ekk-banner-wrap {{
        position: relative;
        width: 100%;
        height: 200px;
        overflow: hidden;
        border-radius: 14px;
        margin-bottom: 1.4rem;
    }}
    .ekk-banner-wrap img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
        display: block;
    }}
    /* fade-bottom: imagen sólida arriba → transparente abajo */
    .ekk-banner-fade-bottom::after {{
        content: '';
        position: absolute;
        left: 0; right: 0; bottom: 0;
        height: 70%;
        background: linear-gradient(to bottom, transparent, var(--ekk-fondo));
        pointer-events: none;
    }}
    /* fade-center: vignette circular */
    .ekk-banner-vignette::after {{
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(ellipse at center, transparent 30%, var(--ekk-fondo) 90%);
        pointer-events: none;
    }}
    /* fade-sides: desvanece por los lados (tira estrecha) */
    .ekk-banner-sides {{
        height: 130px;
    }}
    .ekk-banner-sides::after {{
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(to right,
            var(--ekk-fondo) 0%,
            transparent 18%,
            transparent 82%,
            var(--ekk-fondo) 100%),
            linear-gradient(to bottom, transparent 60%, var(--ekk-fondo) 100%);
        pointer-events: none;
    }}
    /* tint: superposición de color de provincia */
    .ekk-banner-tint::after {{
        content: '';
        position: absolute;
        inset: 0;
        background: var(--ekk-banner-tint);
        pointer-events: none;
    }}

    /* ── Mejoras globales ── */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    .stDataFrame, .stTable {{ border-radius: 10px; overflow: hidden; }}
    div[data-baseweb="notification"] {{ border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)


# ── Helpers de nombre ─────────────────────────────────────────────────────────

def _nombre_de(rol_o_provincia: str) -> str:
    if rol_o_provincia in NOMBRES_PROVINCIA:
        return f"Provincia de {NOMBRES_PROVINCIA[rol_o_provincia]}"
    try:
        from core.auth import ROLES
        return ROLES.get(rol_o_provincia, {}).get("nombre", rol_o_provincia.capitalize())
    except Exception:
        return rol_o_provincia.capitalize()


def header_rol(rol_o_provincia: str, subtitulo: str = ""):
    """Renderiza el header principal de una página."""
    icono = ICONOS.get(rol_o_provincia, "⚖️")
    color = COLORES.get(rol_o_provincia, _tokens()["primario"])
    nombre = _nombre_de(rol_o_provincia)
    st.markdown(f"""
    <div class="ekk-header" style="background: linear-gradient(135deg, {color}22, {color}08);">
        <span class="ekk-header-icon">{icono}</span>
        <span class="ekk-header-text" style="color: {color};">{nombre}</span>
    </div>
    """, unsafe_allow_html=True)
    if subtitulo:
        st.caption(subtitulo)


# ── Banners con degradado ─────────────────────────────────────────────────────

def _resolve_asset(ruta: str) -> Path:
    """Devuelve la ruta absoluta: prueba varias ubicaciones en orden."""
    p = Path(ruta)
    if p.is_absolute() and p.exists():
        return p
    # Relativo al root de ekklesia
    candidate = _EKKLESIA_ROOT / ruta
    if candidate.exists():
        return candidate
    # Carpeta de imágenes compartida fuera de ekklesia/
    name = Path(ruta).name
    candidate2 = _EKKLESIA_ROOT.parent / "Iconos e imagenes" / name
    if candidate2.exists():
        return candidate2
    # assets/ dentro de ekklesia/
    return _EKKLESIA_ROOT / "assets" / name


def _banner_html(ruta: str, css_class: str, height_px: int = 200) -> str:
    """Construye el HTML de un banner con la clase CSS dada."""
    p = _resolve_asset(ruta)
    if not p.exists():
        return ""
    ext, data = _img_b64(str(p))
    return (
        f'<div class="ekk-banner-wrap {css_class}" style="height:{height_px}px;">'
        f'<img src="data:image/{ext};base64,{data}" />'
        f'</div>'
    )


def banner_vignette(ruta: str = "congreso_imagen.png"):
    """Banner con vignette radial. Disponible para uso en provincias si se desea."""
    html = _banner_html(ruta, "ekk-banner-vignette", height_px=180)
    if html:
        st.markdown(html, unsafe_allow_html=True)


def banner_sides(ruta: str = "congreso_imagen.png"):
    """Banner estrecho que funde por los lados."""
    html = _banner_html(ruta, "ekk-banner-sides", height_px=130)
    if html:
        st.markdown(html, unsafe_allow_html=True)


def banner_tint(ruta: str = "congreso_imagen.png"):
    """Banner con tint semitransparente."""
    html = _banner_html(ruta, "ekk-banner-tint", height_px=160)
    if html:
        st.markdown(html, unsafe_allow_html=True)


def banner_imagen(ruta: str = "congreso_imagen.png"):
    """Banner sólido (sin degradado). Uso en Gobierno."""
    p = _resolve_asset(ruta)
    if p.exists():
        st.image(str(p), use_container_width=True)


def aplicar_fondo_main(ruta: str = "congreso_imagen.png"):
    """
    Aplica la imagen como fondo fijo de main.py con glassmorphism por secciones.
    Llamar desde main.py justo después de aplicar_css_global().
    """
    p = _resolve_asset(ruta)
    if not p.exists():
        return
    ext, b64data = _img_b64(str(p))
    dark = st.session_state.get("dark_mode", False)
    glass_bg     = "rgba(245,232,212,0.70)" if not dark else "rgba(22,14,6,0.72)"
    glass_border = "rgba(201,123,74,0.32)"  if not dark else "rgba(228,160,96,0.28)"
    glass_text   = "#3B2A1E"                if not dark else "#F5E8D4"
    glass_shadow = "0 6px 32px rgba(59,42,30,0.22)"

    st.markdown(f"""
    <style>
    /* ── Fondo imagen fijo ── */
    .stApp {{
        background-image: url('data:image/{ext};base64,{b64data}') !important;
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
        background-color: transparent !important;
    }}
    .main .block-container {{
        background: transparent !important;
        max-width: 820px;
    }}

    /* ── Columnas: contenedores transparentes (el glass va en .ekk-glass) ── */
    div[data-testid="column"] {{
        background: transparent !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0.3rem !important;
    }}

    /* ── Clase glass reutilizable para secciones HTML ── */
    .ekk-glass {{
        background: {glass_bg};
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 18px;
        border: 1px solid {glass_border};
        padding: 1.5rem 1.8rem;
        box-shadow: {glass_shadow};
        margin-bottom: 0.9rem;
        color: {glass_text};
    }}
    .ekk-glass h2, .ekk-glass h3 {{
        color: #8B5A3C !important;
        margin-top: 0;
    }}
    .ekk-glass small {{ color: {glass_text}; opacity: 0.75; }}

    /* ── Glass aplicado al formulario de Streamlit ── */
    [data-testid="stForm"] {{
        background: {glass_bg} !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 18px !important;
        border: 1px solid {glass_border} !important;
        padding: 1.6rem 1.8rem 1.2rem !important;
        box-shadow: {glass_shadow} !important;
        margin-bottom: 0.9rem !important;
    }}

    /* ── "Pulsa enter para acceder" junto a la etiqueta Contraseña ── */
    [data-testid="InputInstructions"] {{
        display: none !important;
    }}
    [data-testid="stTextInput"] label::after,
    [data-testid="stTextInputRootElement"] label::after {{
        content: "  ·  Pulsa enter para acceder";
        font-size: 0.72rem;
        color: {glass_text};
        opacity: 0.60;
        font-weight: 400;
        margin-left: 0.4rem;
    }}

    /* ── Ocultar toggle nativo del navegador en password ── */
    input[type="password"]::-ms-reveal  {{ display: none !important; }}
    input[type="password"]::-ms-clear   {{ display: none !important; }}
    input[type="password"]::-webkit-credentials-auto-fill-button {{ display: none !important; }}
    </style>
    """, unsafe_allow_html=True)


# ── Retratos de ciudadanos ────────────────────────────────────────────────────

def _portrait_b64(filename: str) -> str | None:
    """Base64 del retrato, o None si no existe."""
    p = _portraits_dir() / filename
    if not p.exists():
        return None
    try:
        _, data = _img_b64(str(p))
        return data
    except Exception:
        return None


def portrait_data_uri(ciudadano: dict) -> str:
    """Devuelve 'data:image/png;base64,...' para usar en st.column_config.ImageColumn.
    Devuelve cadena vacía si no hay retrato disponible."""
    portrait_file = ciudadano.get("portrait", "")
    if portrait_file:
        b64 = _portrait_b64(portrait_file)
        if b64:
            return f"data:image/png;base64,{b64}"
    return ""


def nombre_con_retrato_html(ciudadano: dict, size: int = 28) -> str:
    """
    Devuelve HTML inline con el retrato pixelart + alias del ciudadano.
    Uso: st.markdown(nombre_con_retrato_html(c), unsafe_allow_html=True)
    """
    alias = ciudadano.get("alias", "?")
    portrait_file = ciudadano.get("portrait", "")
    if portrait_file:
        b64 = _portrait_b64(portrait_file)
        if b64:
            img = (
                f'<img src="data:image/png;base64,{b64}" '
                f'width="{size}" height="{size}" class="ekk-retrato" />'
            )
            return f'<span class="ekk-ciudadano">{img}{alias}</span>'
    return f'<span class="ekk-ciudadano">{alias}</span>'


def render_ciudadano(ciudadano: dict, size: int = 28):
    """Renderiza nombre con retrato usando st.markdown."""
    st.markdown(nombre_con_retrato_html(ciudadano, size), unsafe_allow_html=True)


# ── Badges y tarjetas ─────────────────────────────────────────────────────────

def badge_provincia(provincia: str) -> str:
    nombre = NOMBRES_PROVINCIA.get(provincia, provincia.capitalize())
    return f'<span class="ekk-badge ekk-badge-{provincia}">{nombre}</span>'


def badge_estado(estado: str) -> str:
    mapa = {
        "pendiente": ("pendiente", "Pendiente"),
        "pendiente_validacion": ("pendiente", "Pendiente"),
        "aprobada": ("aprobada", "Aprobada"),
        "registrada": ("aprobada", "Registrada"),
        "rechazada": ("rechazada", "Rechazada"),
    }
    cls, texto = mapa.get(estado, ("pendiente", estado.capitalize()))
    return f'<span class="ekk-status ekk-status-{cls}">{texto}</span>'


def tarjeta(contenido: str, titulo: str = ""):
    titulo_html = f"<h4>{titulo}</h4>" if titulo else ""
    st.markdown(f'<div class="ekk-card">{titulo_html}{contenido}</div>',
                unsafe_allow_html=True)
