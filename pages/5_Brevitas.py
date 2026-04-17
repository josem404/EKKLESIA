"""EKKLESIA — Provincia de Brevitas"""
import streamlit as st
from core.auth import requiere_rol
from core.theme import aplicar_css_global

st.set_page_config(page_title="Brevitas — EKKLESIA", page_icon="⚡", layout="wide")
aplicar_css_global()
requiere_rol("brevitas")

from core.provincia_ui import render_provincia

render_provincia("brevitas", st.session_state.rol)
