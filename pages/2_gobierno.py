"""
EKKLESIA — Gobierno de Funcionalia
Propiedades nacionales, asociaciones nacionales, registro global de funciones.
"""

import streamlit as st
import pandas as pd
from core.auth import requiere_rol
from core.db import (
    get_ciudadanos, get_propiedades, get_ciudadano,
    get_registros, get_matriz_descubierta,
    promover_a_nacional, get_primo_de_propiedad,
    _guardar_asociacion_local, get_asociaciones_local,
    _guardar_colectivo_local, get_colectivos_local,
    nationalizar_colectivo,
    registrar_ciudadano_propiedad,
)
from core.theme import aplicar_css_global, header_rol, banner_imagen, nombre_con_retrato_html, portrait_data_uri, ICONOS, NOMBRES_PROVINCIA
from core.prime_ids import validar_fraccion_miembro

st.set_page_config(page_title="Gobierno — EKKLESIA", page_icon="🏛", layout="wide")
aplicar_css_global()
requiere_rol("gobierno")

# Banner de intervención del rey
if st.session_state.get("rol") == "rey" and st.session_state.get("intervenir"):
    st.warning("⚠️ **Intervenido por el Rey** — estás en la pantalla del Gobierno.")

header_rol("gobierno", "Gestión de propiedades nacionales y asociaciones de Funcionalia")

# Abreviaturas para badges de provincia
_PROV_BADGE = {"magnitudia": "[MAG]", "intervalia": "[INT]", "brevitas": "[BRE]", "nacional": "[NAC]"}

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_funciones, tab_props, tab_registros, tab_colectivos, tab_asoc = st.tabs([
    "👥 Ciudadanía de Funcionalia",
    f"{ICONOS['propiedad']} Propiedades de Funcionalia",
    "🔍 Registros",
    f"{ICONOS['colectivo']} Colectivos",
    f"{ICONOS['asociacion']} Asociaciones nacionales",
])


# ═══ TAB 1: Propiedades de Funcionalia ═══════════════════════════════════════
with tab_props:
    st.subheader("Propiedades de Funcionalia")
    st.markdown("""
    El Gobierno puede ver todas las propiedades registradas por las provincias
    y **promover una propiedad a nacional [NAC]**, añadiéndola al cajón de todas las provincias.
    """)

    propiedades_all = get_propiedades()

    if not propiedades_all:
        st.info("No hay propiedades registradas.")
    else:
        for p in propiedades_all:
            prov = p.get("provincia", "?")
            badge = _PROV_BADGE.get(prov, f"[{prov[:3].upper()}]")
            es_nacional = prov == "nacional"

            col_info, col_btn = st.columns([4, 1])
            with col_info:
                st.markdown(
                    f"**{badge}** &nbsp; `{p['codigo']}` — {p['descripcion']} &nbsp;"
                    f"*(primo: {p['primo_asignado']})*",
                    unsafe_allow_html=True,
                )
            with col_btn:
                if es_nacional:
                    st.markdown("*Ya es nacional*")
                else:
                    if st.button(f"Hacer [NAC]", key=f"nac_{p['codigo']}", use_container_width=True):
                        ok = promover_a_nacional(p["codigo"])
                        if ok:
                            st.success(
                                f"✅ «{p['descripcion']}» es ahora una propiedad nacional. "
                                "Las 3 provincias pueden usarla."
                            )
                            st.rerun()


# ═══ TAB 2: Colectivos ═══════════════════════════════════════════════════════
with tab_colectivos:
    st.subheader("Colectivos de Funcionalia")
    st.markdown("""
    El Gobierno puede ver los colectivos de todas las provincias y crear **colectivos nacionales [NAC]**.
    Al crear un colectivo nacional, todas sus propiedades se promueven automáticamente a nacionales.
    """)

    # ── Vista de todos los colectivos ─────────────────────────────────────────
    todos_colectivos = get_colectivos_local()
    _PROV_BADGE_COL = {"magnitudia": "[MAG]", "intervalia": "[INT]", "brevitas": "[BRE]", "nacional": "[NAC]"}

    if todos_colectivos:
        st.markdown(f"**{len(todos_colectivos)} colectivo(s) registrado(s):**")
        for col_item in todos_colectivos:
            ambito_c = col_item.get("ambito", "provincial")
            prov_c   = col_item.get("provincia")
            badge_c  = "[NAC]" if ambito_c == "nacional" else _PROV_BADGE_COL.get(prov_c, f"[{str(prov_c or '?')[:3].upper()}]")
            props_c  = col_item.get("propiedades", [])

            # Computar miembros dinámicamente desde registros
            matriz_c = get_matriz_descubierta()
            ciudadanos_c = (
                get_ciudadanos() if ambito_c == "nacional"
                else get_ciudadanos(provincia=prov_c)
            )
            miembros_din = [
                c["id"] for c in ciudadanos_c
                if all(matriz_c.get(c["id"], {}).get(pc) == "satisface" for pc in props_c)
            ]

            with st.expander(
                f"**{badge_c} {col_item['nombre']}** | Props: {', '.join(props_c)} | "
                f"{len(miembros_din)} miembro(s) confirmado(s)"
            ):
                if miembros_din:
                    filas_cm = [{"Ciudadano": c["alias"], "Bloques": c["bloques"]}
                                for c in ciudadanos_c if c["id"] in miembros_din]
                    st.dataframe(pd.DataFrame(filas_cm), use_container_width=True, hide_index=True)

                if ambito_c == "provincial":
                    if st.button("🌐 Hacer [NAC]", key=f"nac_col_{col_item['id']}", type="secondary"):
                        ok = nationalizar_colectivo(col_item["id"])
                        if ok:
                            props_nac = col_item.get("propiedades", [])
                            st.success(
                                f"✅ «{col_item['nombre']}» es ahora un colectivo nacional. "
                                f"Propiedades {props_nac} promovidas a [NAC]."
                            )
                            st.rerun()
    else:
        st.info("Todavía no hay colectivos creados por las provincias.")

    st.divider()

    # ── Crear nuevo colectivo nacional ────────────────────────────────────────
    st.subheader("Crear colectivo nacional [NAC]")
    st.caption("Al guardar, todas las propiedades seleccionadas se promueven a [NAC].")

    propiedades_nac = get_propiedades()
    if not propiedades_nac:
        st.warning("No hay propiedades disponibles.")
    else:
        nombre_col_nac = st.text_input(
            "Nombre del colectivo nacional",
            placeholder='ej: "Gran Colectivo de Funcionalia"',
            key="gob_col_nac_nombre",
        )
        prop_col_opciones = {
            f"{_PROV_BADGE.get(p.get('provincia','?'),'?')} {p.get('descripcion_corta', p['codigo'])} (p={p['primo_asignado']})": p["codigo"]
            for p in propiedades_nac
        }
        props_col_sel_display = st.multiselect(
            "Propiedades del colectivo",
            options=list(prop_col_opciones.keys()),
            key="gob_col_nac_props",
        )
        props_col_sel = [prop_col_opciones[d] for d in props_col_sel_display]

        if props_col_sel:
            st.info(f"⚠️ Al guardar, las propiedades {props_col_sel} se promoverán a [NAC].")

        if st.button("💾 Guardar colectivo nacional", type="primary", key="gob_guardar_col_nac"):
            if not nombre_col_nac.strip():
                st.error("Ponle un nombre al colectivo.")
            elif not props_col_sel:
                st.error("Selecciona al menos una propiedad.")
            else:
                # Promover propiedades a nacionales
                for pc in props_col_sel:
                    promover_a_nacional(pc)
                # Guardar colectivo
                _guardar_colectivo_local(
                    nombre=nombre_col_nac.strip(),
                    ambito="nacional",
                    provincia=None,
                    prop_codigos=props_col_sel,
                    miembros_ids=[],
                    created_by="gobierno",
                )
                st.success(
                    f"✅ Colectivo nacional «{nombre_col_nac}» creado. "
                    f"Propiedades {props_col_sel} promovidas a [NAC]."
                )
                st.rerun()


# ═══ TAB 3: Asociaciones nacionales ══════════════════════════════════════════
with tab_asoc:
    st.subheader("Asociaciones nacionales")
    st.markdown("""
    El Gobierno puede crear asociaciones que incluyen ciudadanos de cualquier provincia
    usando propiedades de todo el cajón global.
    """)

    # ── Asociaciones existentes ───────────────────────────────────────────────
    asocs_nac = get_asociaciones_local(estado=None)
    asocs_nac = [a for a in asocs_nac if a.get("ambito") == "nacional"]

    if asocs_nac:
        st.markdown(f"**{len(asocs_nac)} asociación(es) nacional(es):**")
        for asoc in asocs_nac:
            miembros = asoc.get("miembros", [])
            props = asoc.get("propiedades_ord", [])
            estado = asoc.get("estado", "?")
            with st.expander(
                f"**{asoc['nombre']}** | {len(miembros)} miembros | Props: {', '.join(props)} | {estado}"
            ):
                if miembros:
                    df_m = pd.DataFrame([{
                        "Ciudadano": m.get("alias", "?"),
                        "ID": m.get("id_racional", "?"),
                    } for m in miembros])
                    st.dataframe(df_m, use_container_width=True, hide_index=True)
        st.divider()

    # ── Crear nueva asociación nacional ──────────────────────────────────────
    st.subheader("Crear nueva asociación nacional")

    propiedades_all = get_propiedades()
    ciudadanos_all = get_ciudadanos()

    if not propiedades_all or not ciudadanos_all:
        st.warning("No hay datos disponibles.")
    else:
        # ── Paso 1: Nombre + propiedades ──────────────────────────────────────
        nombre_asoc = st.text_input("Nombre de la asociación",
                                    placeholder='ej: "Gran Asociación Nacional Alpha"',
                                    key="gob_asoc_nombre")

        st.markdown("**Selecciona propiedades (en orden):**")
        prop_opciones = {
            f"{_PROV_BADGE.get(p.get('provincia','?'), '?')} {p.get('descripcion_corta', p['codigo'])} (p={p['primo_asignado']})": p
            for p in propiedades_all
        }
        props_display = st.multiselect(
            "Propiedades de la asociación",
            options=list(prop_opciones.keys()),
            key="gob_asoc_props",
        )
        props_sel_objs = [prop_opciones[d] for d in props_display]
        props_sel_codigos = [p["codigo"] for p in props_sel_objs]
        primos_sel = [p["primo_asignado"] for p in props_sel_objs]

        if props_sel_codigos:
            st.markdown("**Propiedades seleccionadas (el orden determina el patrón):**")
            for i, p_obj in enumerate(props_sel_objs):
                badge = _PROV_BADGE.get(p_obj.get("provincia", "?"), "?")
                st.markdown(f"{i+1}. {badge} **{p_obj.get('descripcion_corta', p_obj['codigo'])}** — primo: `{p_obj['primo_asignado']}`")

        st.divider()

        # ── Paso 2: Miembros y sus fracciones ────────────────────────────────
        if props_sel_codigos:
            st.subheader("Introducir números de asociado")
            st.markdown("""
            Cada ciudadano debe calcular su número de asociado según las propiedades que satisface o no.
            Introdúcelo en formato **numerador/denominador** (ej: `6/5`).
            """)

            # Inicializar fracciones en session_state
            if "gob_fracciones" not in st.session_state:
                st.session_state.gob_fracciones = {}

            # Tabla de ciudadanos con inputs
            filas_header = st.columns([3, 2, 2])
            filas_header[0].markdown("**Ciudadano**")
            filas_header[1].markdown("**Provincia**")
            filas_header[2].markdown("**Número de asociado (fracción)**")

            for c in ciudadanos_all:
                cols = st.columns([3, 2, 2])
                cols[0].markdown(nombre_con_retrato_html(c, size=22), unsafe_allow_html=True)
                cols[1].markdown(NOMBRES_PROVINCIA.get(c["provincia"], c["provincia"].capitalize()))
                frac_val = st.session_state.gob_fracciones.get(c["id"], "")
                nueva_frac = cols[2].text_input(
                    "fracción",
                    value=frac_val,
                    placeholder="ej: 6/5",
                    key=f"gob_frac_{c['id']}",
                    label_visibility="collapsed",
                )
                if nueva_frac != frac_val:
                    st.session_state.gob_fracciones[c["id"]] = nueva_frac

            st.divider()

            # ── Paso 3: Verificar ────────────────────────────────────────────
            if st.button("🔍 Verificar números de asociado", type="primary", key="gob_verificar"):
                # Solo verificar los que tienen fracción introducida
                fracciones_intro = {
                    cid: frac for cid, frac in
                    {c["id"]: st.session_state.get(f"gob_frac_{c['id']}", "").strip()
                     for c in ciudadanos_all}.items()
                    if frac
                }

                if not fracciones_intro:
                    st.warning("Introduce al menos un número de asociado para verificar.")
                else:
                    resultados_verif = {}
                    for cid, frac_str in fracciones_intro.items():
                        c = get_ciudadano(cid)
                        if c:
                            r = validar_fraccion_miembro(c, props_sel_codigos, primos_sel, frac_str)
                            resultados_verif[cid] = {"ciudadano": c, "frac_str": frac_str, **r}

                    st.session_state.gob_verif_resultados = resultados_verif

            # Mostrar resultados de verificación
            if "gob_verif_resultados" in st.session_state and st.session_state.gob_verif_resultados:
                resultados_verif = st.session_state.gob_verif_resultados
                filas_r = []
                todos_correctos = True
                for cid, r in resultados_verif.items():
                    c = r["ciudadano"]
                    if not r["ok"]:
                        filas_r.append({
                            "Ciudadano": c["alias"],
                            "Introducido": r["frac_str"],
                            "Estado": f"❌ Error: {r.get('error', '?')}",
                        })
                        todos_correctos = False
                    elif r["correcto"]:
                        patron_str = " ".join("✅" if s else "❌" for s in r["patron"])
                        filas_r.append({
                            "Ciudadano": c["alias"],
                            "Introducido": r["introducido"],
                            "Estado": "✅ Correcto",
                            "Patrón": patron_str,
                        })
                    else:
                        filas_r.append({
                            "Ciudadano": c["alias"],
                            "Introducido": r["introducido"],
                            "Estado": f"❌ Incorrecto (esperado: {r['esperado']})",
                        })
                        todos_correctos = False

                st.dataframe(pd.DataFrame(filas_r), use_container_width=True, hide_index=True)

                if todos_correctos and nombre_asoc.strip():
                    if st.button("💾 Guardar asociación nacional", type="primary", key="gob_guardar"):
                        # Construir miembros
                        miembros_data = []
                        for cid, r in resultados_verif.items():
                            c = r["ciudadano"]
                            miembros_data.append({
                                "ciudadano_id": cid,
                                "alias": c["alias"],
                                "id_racional": r["introducido"],
                                "patron": r["patron"],
                            })
                            # Actualizar registros con lo descubierto
                            for prop_codigo in props_sel_codigos:
                                registrar_ciudadano_propiedad(cid, prop_codigo, "gobierno")

                        _guardar_asociacion_local(
                            nombre=nombre_asoc.strip(),
                            ambito="nacional",
                            provincia=None,
                            propiedades_ord=props_sel_codigos,
                            miembros=miembros_data,
                            created_by="gobierno",
                        )
                        st.success(f"✅ Asociación «{nombre_asoc}» guardada con {len(miembros_data)} miembro(s).")
                        del st.session_state["gob_verif_resultados"]
                        st.rerun()
                elif not nombre_asoc.strip():
                    st.caption("Ponle un nombre a la asociación para guardarla.")
                elif not todos_correctos:
                    st.error("Corrige los errores antes de guardar.")


# ═══ TAB 4: Funciones de Funcionalia ═════════════════════════════════════════
with tab_funciones:
    st.subheader("Registro de funciones de Funcionalia")
    st.caption("El Gobierno ve el censo de ciudadanos. Las definiciones de las funciones son confidenciales (solo el Rey tiene acceso).")

    ciudadanos_all = get_ciudadanos()
    if not ciudadanos_all:
        st.info("No hay ciudadanos registrados.")
    else:
        for prov in ["magnitudia", "intervalia", "brevitas"]:
            ciudadanos_prov = [c for c in ciudadanos_all if c["provincia"] == prov]
            if ciudadanos_prov:
                st.markdown(f"### {NOMBRES_PROVINCIA[prov]} ({len(ciudadanos_prov)} ciudadanos)")
                filas = [{
                    "Retrato": portrait_data_uri(c) or None,
                    "Apodo": c["alias"],
                    "Bloques": c["bloques"],
                } for c in ciudadanos_prov]
                _col_cfg_fun = {"Retrato": st.column_config.ImageColumn(label="", width="small")}
                st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True,
                             column_config=_col_cfg_fun)
                st.divider()


# ═══ TAB 4: Tabla de registros ════════════════════════════════════════
with tab_registros:
    st.subheader("Tabla de registros — lo descubierto por las provincias")
    st.caption("✅ satisface · ❌ no satisface · ? sin registrar")

    propiedades_all = get_propiedades()
    ciudadanos_all = get_ciudadanos()

    if not propiedades_all or not ciudadanos_all:
        st.info("No hay datos disponibles.")
    else:
        _PROV_ABREV = {"magnitudia": "MAG", "intervalia": "INT", "brevitas": "BRE"}

        prov_f = st.selectbox(
            "Filtrar ciudadanos",
            ["Todas", "magnitudia", "intervalia", "brevitas"],
            key="gob_reg_prov",
        )
        ciud_filtrados = (
            ciudadanos_all if prov_f == "Todas"
            else [c for c in ciudadanos_all if c["provincia"] == prov_f]
        )
        cids = [c["id"] for c in ciud_filtrados]
        matriz_desc = get_matriz_descubierta(ciudadano_ids=cids)

        filas = []
        for c in ciud_filtrados:
            uri = portrait_data_uri(c)
            fila = {
                "Retrato": uri if uri else None,
                "Ciudadano": c["alias"],
                "Prov.": _PROV_ABREV.get(c["provincia"], c["provincia"][:3].upper()),
            }
            for p in propiedades_all:
                col_name = (
                    f"{p.get('descripcion_corta', p['codigo'])} "
                    f"[{_PROV_ABREV.get(p.get('provincia',''), _PROV_BADGE.get(p.get('provincia',''), '?'))}]"
                )
                estado = matriz_desc.get(c["id"], {}).get(p["codigo"], "desconocido")
                fila[col_name] = "✅" if estado == "satisface" else ("❌" if estado == "no_satisface" else "?")
            filas.append(fila)

        _col_cfg_gob = {"Retrato": st.column_config.ImageColumn(label="", width="small")}
        st.dataframe(pd.DataFrame(filas), use_container_width=True,
                     hide_index=True, column_config=_col_cfg_gob)

        # Métricas
        total_celdas = len(ciud_filtrados) * len(propiedades_all)
        celdas_desc = sum(
            1 for f in filas for k, v in f.items()
            if k not in ("Retrato", "Ciudadano", "Prov.") and v != "?"
        )
        if total_celdas > 0:
            pct = celdas_desc / total_celdas
            st.metric("Celdas descubiertas", f"{celdas_desc} / {total_celdas}", f"{pct:.0%}")
            st.progress(pct)
