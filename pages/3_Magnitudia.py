"""EKKLESIA — Provincia de Magnitudia"""
import streamlit as st
from core.auth import requiere_rol
from core.theme import aplicar_css_global

st.set_page_config(page_title="Magnitudia — EKKLESIA", page_icon="🏔️", layout="wide")
aplicar_css_global()
requiere_rol("magnitudia")

from core.provincia_ui import render_provincia

render_provincia("magnitudia", st.session_state.rol)
