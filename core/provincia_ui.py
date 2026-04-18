"""
Lógica de UI compartida para las tres provincias de Funcionalia.
Uso: render_provincia(provincia, rol) desde cada página de provincia.
"""

import streamlit as st
import pandas as pd
from core.db import (
    get_ciudadanos, get_propiedades_provincia, get_ciudadano,
    _guardar_colectivo_local, get_colectivos_local, añadir_miembro_colectivo_local,
    _guardar_asociacion_local, get_asociaciones_local, actualizar_estado_asociacion_local,
    get_registros, registrar_ciudadano_propiedad,
    registrar_ciudadano_colectivo, get_matriz_descubierta,
)
from core.prime_ids import validar_fraccion_miembro
from core.theme import header_rol, nombre_con_retrato_html, portrait_data_uri, ICONOS, NOMBRES_PROVINCIA
from core.components import selector_propiedades

_PROV_BADGE = {
    "magnitudia": "[MAG]",
    "intervalia": "[INT]",
    "brevitas":   "[BRE]",
    "nacional":   "[NAC]",
}

LIMITE_PROPS = {"magnitudia": 4, "intervalia": 3, "brevitas": 2}
LIMITE_CIUDADANOS = {"magnitudia": 16, "intervalia": 8, "brevitas": 4}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _oracle_satisfacen(todos_provincia: list, prop_codigos: list) -> set:
    """Ciudadanos de la provincia que satisfacen TODAS las props según el oráculo."""
    return {
        c["id"] for c in todos_provincia
        if all(bool(c.get("propiedades", {}).get(pc, False)) for pc in prop_codigos)
    }


def _confirmados_en_props(matriz_desc: dict, prop_codigos: list, todos_ids: list) -> set:
    """Ciudadanos de la provincia con TODAS las props registradas como 'satisface'."""
    return {
        cid for cid in todos_ids
        if all(matriz_desc.get(cid, {}).get(pc) == "satisface" for pc in prop_codigos)
    }


def _boton_completo(key: str, prop_codigos: list, todos_provincia: list,
                    matriz_desc: dict, provincia: str, etiqueta: str = "📋 COLECTIVO COMPLETO"):
    """Renderiza el botón COLECTIVO COMPLETO y ejecuta la lógica."""
    if st.button(etiqueta, key=key, use_container_width=True):
        todos_ids = [c["id"] for c in todos_provincia]
        oracle_set = _oracle_satisfacen(todos_provincia, prop_codigos)
        confirmados = _confirmados_en_props(matriz_desc, prop_codigos, todos_ids)

        if oracle_set <= confirmados:
            # La provincia ha identificado correctamente a todos
            added = 0
            for cid in oracle_set:
                for pc in prop_codigos:
                    r = registrar_ciudadano_propiedad(cid, pc, provincia)
                    if not r.get("ya_registrado"):
                        added += 1
            if added > 0:
                st.toast(f"✅ Completo. Se añadieron {added} registros.", icon="✅")
                st.rerun()
            else:
                st.success("✅ Ya estaba completo. Todos los miembros están registrados.")
        else:
            faltan = oracle_set - confirmados
            st.warning(
                f"❌ No está completo. Faltan **{len(faltan)}** ciudadano(s) por identificar. "
                "(En el futuro habrá penalización por declararlo antes de tiempo.)"
            )


# ── Función principal ─────────────────────────────────────────────────────────

def render_provincia(provincia: str, rol: str):
    """Renderiza la pantalla completa de una provincia."""

    if rol == "rey":
        st.warning(
            f"⚠️ **Intervenido por el Rey** — estás en la pantalla de {NOMBRES_PROVINCIA[provincia]}."
        )

    header_rol(provincia, f"Límite de propiedades en asociaciones: {LIMITE_PROPS[provincia]} | "
                          f"Máximo ciudadanos identificables: {LIMITE_CIUDADANOS[provincia]}")

    # ── Datos de la provincia ─────────────────────────────────────────────────
    todos_provincia = get_ciudadanos(provincia=provincia)
    ids_provincia = {c["id"]: c for c in todos_provincia}

    # Session-state con prefijo de provincia para evitar conflictos al navegar
    pref = f"{provincia}_"
    reg_key = f"{pref}ciudadanos_registrados"
    if reg_key not in st.session_state:
        st.session_state[reg_key] = set()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_registro, tab_propiedades, tab_colectivos, tab_asociaciones = st.tabs([
        "📋 Padrón",
        f"{ICONOS['propiedad']} Propiedades y Registro",
        f"{ICONOS['colectivo']} Colectivos",
        f"{ICONOS['asociacion']} Asociaciones",
    ])

    # ═══ TAB 1: Registro ══════════════════════════════════════════════════════
    with tab_registro:
        st.subheader("Empadronamiento en la provincia")
        st.markdown("""
        Cuando un ciudadano llega a la provincia, introduce su ID para marcarlo como presente.
        """)

        with st.form(f"{pref}registro_form"):
            id_input = st.text_input("ID del ciudadano",
                                     placeholder="ej: c-mag-01  o pega el código QR aquí",
                                     key=f"{pref}reg_id_input")
            registrar = st.form_submit_button("Empadronar ciudadano/a", type="primary")

        if registrar:
            id_limpio = id_input.strip()
            if not id_limpio:
                st.error("Introduce un ID.")
            elif id_limpio not in ids_provincia:
                st.error(f"ID «{id_limpio}» no encontrado en {NOMBRES_PROVINCIA[provincia]}.")
            elif id_limpio in st.session_state[reg_key]:
                st.warning("Este ciudadano ya estaba registrado.")
            else:
                st.session_state[reg_key].add(id_limpio)
                c_reg = ids_provincia[id_limpio]
                st.markdown(
                    f'<div style="color:#8BA878; font-weight:600;">✅ Registrado: '
                    f'{nombre_con_retrato_html(c_reg, size=32)}</div>',
                    unsafe_allow_html=True,
                )

        st.divider()
        registrados_ids = st.session_state[reg_key] & set(ids_provincia.keys())
        pendientes_ids  = set(ids_provincia.keys()) - registrados_ids

        # ── Galería con retratos ──────────────────────────────────────────────
        def _galeria_ciudadanos(lista_ids: list, highlight: bool = True):
            """Muestra ciudadanos en cuadrícula con retrato pixelart + alias."""
            cols_per_row = 3
            filas = [lista_ids[i:i + cols_per_row]
                     for i in range(0, len(lista_ids), cols_per_row)]
            border_color = "#8BA878" if highlight else "#B5533C"
            for fila in filas:
                cols_g = st.columns(cols_per_row)
                for j, cid in enumerate(fila):
                    c = ids_provincia[cid]
                    uri = portrait_data_uri(c)
                    img_html = (
                        f'<img src="{uri}" width="36" height="36" '
                        f'style="image-rendering:pixelated; display:block; '
                        f'margin:0 auto 4px;" />'
                        if uri else ""
                    )
                    alias_short = c["alias"].split(" — ")[0]  # solo "Nombre X."
                    fn = c["alias"].split(" — ")[-1] if " — " in c["alias"] else ""
                    cols_g[j].markdown(
                        f'<div style="text-align:center; padding:6px 4px; '
                        f'border:1px solid {border_color}44; border-radius:10px; '
                        f'overflow:hidden;">'
                        f'{img_html}'
                        f'<div style="font-size:0.7rem; font-weight:600; '
                        f'word-break:break-word; line-height:1.3;">{alias_short}</div>'
                        f'<div style="font-size:0.65rem; color:#7A5C46;">{fn}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        col_reg, col_pend = st.columns(2)
        with col_reg:
            st.markdown(f"**Presentes ({len(registrados_ids)}/{len(todos_provincia)})**")
            if registrados_ids:
                _galeria_ciudadanos(sorted(registrados_ids), highlight=True)
                if st.button("Limpiar registros", type="secondary", key=f"{pref}limpiar"):
                    st.session_state[reg_key].clear()
                    st.rerun()
            else:
                st.info("Ningún ciudadano presente aún.")

        with col_pend:
            st.markdown(f"**Pendientes ({len(pendientes_ids)})**")
            if pendientes_ids:
                _galeria_ciudadanos(sorted(pendientes_ids), highlight=False)
            else:
                st.success("¡Todos presentes!")

        st.divider()
        if st.button("⚡ Empadronar todos/as (modo demo)", type="secondary", key=f"{pref}demo"):
            for cid in ids_provincia:
                st.session_state[reg_key].add(cid)
            st.success(f"Registrados {len(ids_provincia)} ciudadanos.")
            st.rerun()

    # ═══ TAB 2: Propiedades ═══════════════════════════════════════════════════
    with tab_propiedades:
        props_prov = get_propiedades_provincia(provincia)
        regs_prov  = get_registros(provincia=provincia)

        st.subheader(f"Propiedades de {NOMBRES_PROVINCIA[provincia]}")

        if not props_prov:
            st.info("Esta provincia no tiene propiedades registradas todavía.")
        else:
            regs_por_prop: dict = {}
            for r in regs_prov:
                pc = r["propiedad_codigo"]
                regs_por_prop.setdefault(pc, {"satisface": 0, "no_satisface": 0})
                regs_por_prop[pc][r["estado"]] = regs_por_prop[pc].get(r["estado"], 0) + 1

            _AMBITO_BADGE = {
                "magnitudia": "[MAG]", "intervalia": "[INT]",
                "brevitas": "[BRE]", "nacional": "[NAC]",
            }
            df_props = pd.DataFrame([{
                "Propiedad":    p.get("descripcion_corta", p["codigo"]),
                "Ámbito":       _AMBITO_BADGE.get(p.get("provincia", "?"), "?"),
                "Primo":        p["primo_asignado"],
                "Nivel":        p["nivel"],
                "Satisfacen":   regs_por_prop.get(p["codigo"], {}).get("satisface", 0),
                "No satisfacen": regs_por_prop.get(p["codigo"], {}).get("no_satisface", 0),
            } for p in props_prov])
            st.dataframe(df_props, use_container_width=True, hide_index=True)

            # ── Botón COMPLETO por propiedad ─────────────────────────────────
            st.markdown("**Declarar propiedad completa:**")
            matriz_desc_props = get_matriz_descubierta(provincia=provincia)
            prop_completo_sel = st.selectbox(
                "Selecciona propiedad",
                options=[p["codigo"] for p in props_prov],
                format_func=lambda c: next(
                    (p.get("descripcion_corta", c) for p in props_prov if p["codigo"] == c), c
                ),
                key=f"{pref}prop_completo_sel",
            )
            _boton_completo(
                key=f"{pref}btn_completo_prop_{prop_completo_sel}",
                prop_codigos=[prop_completo_sel],
                todos_provincia=todos_provincia,
                matriz_desc=matriz_desc_props,
                provincia=provincia,
                etiqueta="📋 PROPIEDAD COMPLETA",
            )

        st.divider()

        # ── Flujo de registro individual ──────────────────────────────────────
        st.subheader("Registrar ciudadano en una propiedad")
        if not props_prov:
            st.warning("No hay propiedades disponibles en esta provincia.")
        else:
            prop_opciones = {
                f"{p.get('descripcion_corta', p['codigo'])} (primo={p['primo_asignado']})": p["codigo"]
                for p in props_prov
            }
            col_sel, col_id = st.columns([1, 1])
            with col_sel:
                prop_display = st.selectbox("Propiedad", options=list(prop_opciones.keys()),
                                            key=f"{pref}reg_prop_sel")
            with col_id:
                ciudadano_input = st.text_input("Código del ciudadano",
                                                placeholder="ej: c-mag-01",
                                                key=f"{pref}reg_ciud_id")

            if st.button("🔍 Verificar y registrar", type="primary", key=f"{pref}btn_reg_prop"):
                cid = ciudadano_input.strip()
                if not cid:
                    st.error("Introduce el código del ciudadano.")
                else:
                    prop_codigo = prop_opciones[prop_display]
                    resultado = registrar_ciudadano_propiedad(cid, prop_codigo, provincia)

                    if not resultado["ok"]:
                        st.error(f"Error: {resultado.get('error', 'desconocido')}")
                    elif resultado.get("ya_registrado"):
                        estado_prev = resultado["estado"]
                        icon = "✅" if estado_prev == "satisface" else "❌"
                        st.info(f"{icon} Ya estaba registrado: «{cid}» **{estado_prev}** «{prop_display}».")
                    elif resultado["satisface"]:
                        c_dat = get_ciudadano(cid)
                        alias = c_dat["alias"] if c_dat else cid
                        st.toast(f"✅ {alias} satisface «{prop_display}». Registrado.", icon="✅")
                        st.rerun()
                    else:
                        c_dat = get_ciudadano(cid)
                        alias = c_dat["alias"] if c_dat else cid
                        st.toast(f"❌ {alias} NO satisface «{prop_display}».", icon="❌")
                        st.rerun()

            # ── Tabla de lo descubierto ───────────────────────────────────────
            st.divider()
            _render_tabla_registros(provincia, props_prov, regs_prov)

    # ═══ TAB 3: Colectivos ════════════════════════════════════════════════════
    with tab_colectivos:
        st.subheader(f"Colectivos de {NOMBRES_PROVINCIA[provincia]}")

        props_prov_col = get_propiedades_provincia(provincia)
        regs_col       = get_registros(provincia=provincia)
        matriz_desc_col = get_matriz_descubierta(provincia=provincia)

        # Colectivos de la provincia + colectivos nacionales
        colectivos_prov = get_colectivos_local(provincia=provincia)
        colectivos_nac  = get_colectivos_local(ambito="nacional")
        todos_colectivos = colectivos_prov + colectivos_nac

        if todos_colectivos:
            for col_item in todos_colectivos:
                props_col   = col_item.get("propiedades", [])
                ambito_col  = col_item.get("ambito", "provincial")
                prov_col    = col_item.get("provincia")
                badge_col   = _PROV_BADGE.get(prov_col, "[NAC]") if ambito_col == "provincial" else "[NAC]"

                # Miembros dinámicos: ciudadanos con TODAS las props como "satisface"
                miembros_dinamicos = [
                    cid for cid in ids_provincia
                    if all(
                        matriz_desc_col.get(cid, {}).get(pc) == "satisface"
                        for pc in props_col
                    )
                ]

                with st.expander(
                    f"**{badge_col} {col_item['nombre']}** | "
                    f"Props: {', '.join(props_col)} | "
                    f"{len(miembros_dinamicos)} miembro(s) confirmado(s)"
                ):
                    if miembros_dinamicos:
                        filas_m = []
                        for cid in miembros_dinamicos:
                            c = ids_provincia.get(cid) or get_ciudadano(cid)
                            if c:
                                filas_m.append({"Apodo": c["alias"], "Bloques": c["bloques"]})
                        if filas_m:
                            st.dataframe(pd.DataFrame(filas_m),
                                         use_container_width=True, hide_index=True)

                    # Solo permitir registrar en colectivos propios (no nacionales desde aquí)
                    if ambito_col == "provincial":
                        st.markdown("**Registrar ciudadano en este colectivo:**")
                        cid_col_input = st.text_input(
                            "Código del ciudadano", placeholder="ej: c-mag-01",
                            key=f"{pref}reg_col_{col_item['id']}"
                        )
                        if st.button("🔍 Verificar y registrar en colectivo",
                                     key=f"{pref}btn_col_{col_item['id']}", type="primary"):
                            cid = cid_col_input.strip()
                            if not cid:
                                st.error("Introduce el código del ciudadano.")
                            else:
                                resultado = registrar_ciudadano_colectivo(cid, col_item["id"], provincia)
                                if not resultado["ok"]:
                                    st.error(f"Error: {resultado.get('error')}")
                                elif resultado["todas_satisfechas"]:
                                    c_dat = get_ciudadano(cid)
                                    alias = c_dat["alias"] if c_dat else cid
                                    st.toast(f"✅ {alias} satisface todas las propiedades.", icon="✅")
                                    st.rerun()
                                else:
                                    c_dat = get_ciudadano(cid)
                                    alias = c_dat["alias"] if c_dat else cid
                                    st.warning(f"❌ **{alias}** NO satisface todas las propiedades.")
                                    for pc, r in resultado.get("resultados", {}).items():
                                        icon = "✅" if r.get("satisface") else "❌"
                                        st.caption(f"  {icon} {pc}")

                    # COLECTIVO COMPLETO
                    if props_col:
                        _boton_completo(
                            key=f"{pref}completo_col_{col_item['id']}",
                            prop_codigos=props_col,
                            todos_provincia=todos_provincia,
                            matriz_desc=matriz_desc_col,
                            provincia=provincia,
                        )
        else:
            st.info("Aún no hay colectivos en esta provincia.")

        st.divider()

        # ── Crear nuevo colectivo provincial ─────────────────────────────────
        st.subheader("Crear nuevo colectivo")

        if not props_prov_col:
            st.warning("No hay propiedades en esta provincia para crear colectivos.")
        else:
            st.markdown("""
            El colectivo agrupa ciudadanos que satisfacen **todas** las propiedades seleccionadas.
            Solo se muestran ciudadanos cuyas registros ya estén confirmadas.
            """)

            col_izq, col_der = st.columns([1, 1])
            with col_izq:
                st.markdown("**Selecciona propiedades**")
                props_sel_col = selector_propiedades(
                    props_prov_col,
                    max_selections=LIMITE_PROPS[provincia],
                    key=f"{pref}col_nueva_props",
                )

            with col_der:
                if props_sel_col:
                    st.markdown("**Ciudadanos que satisfacen TODAS (según registros)**")
                    todos_cids_set = {r["ciudadano_id"] for r in regs_col}

                    miembros_confirmados = [
                        cid for cid in todos_cids_set
                        if all(
                            matriz_desc_col.get(cid, {}).get(pc) == "satisface"
                            for pc in props_sel_col
                        )
                    ]

                    if miembros_confirmados:
                        filas_prev = []
                        for cid in miembros_confirmados:
                            c = get_ciudadano(cid)
                            if c:
                                filas_prev.append({
                                    "Apodo": c["alias"],
                                    "Provincia": c["provincia"].capitalize(),
                                })
                        st.dataframe(pd.DataFrame(filas_prev), use_container_width=True, hide_index=True)
                        st.caption(f"{len(miembros_confirmados)} miembro(s) confirmado(s)")
                    else:
                        st.info("Ningún ciudadano registrado satisface todas las propiedades seleccionadas.")
                        miembros_confirmados = []
                else:
                    st.info("← Selecciona propiedades.")
                    miembros_confirmados = []

            if props_sel_col:
                st.divider()
                col_nm, col_btn = st.columns([2, 1])
                with col_nm:
                    nombre_col = st.text_input(
                        "Nombre del colectivo",
                        placeholder=f'ej: "Continuas en {NOMBRES_PROVINCIA[provincia]}"',
                        key=f"{pref}col_nueva_nombre",
                    )
                with col_btn:
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                    if st.button("💾 Guardar colectivo", type="primary",
                                 key=f"{pref}btn_guardar_col", use_container_width=True):
                        if not nombre_col.strip():
                            st.error("Ponle un nombre al colectivo.")
                        else:
                            try:
                                _guardar_colectivo_local(
                                    nombre=nombre_col.strip(),
                                    ambito="provincial",
                                    provincia=provincia,
                                    prop_codigos=props_sel_col,
                                    miembros_ids=miembros_confirmados,
                                    created_by=rol,
                                )
                                st.success(
                                    f"Colectivo «{nombre_col}» guardado "
                                    f"con {len(miembros_confirmados)} miembro(s)."
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

    # ═══ TAB 4: Asociaciones ══════════════════════════════════════════════════
    with tab_asociaciones:
        props_prov_asoc = get_propiedades_provincia(provincia)
        regs_asoc       = get_registros(provincia=provincia)

        # ── Tabla de registros (también visible aquí para referencia) ────
        with st.expander("📊 Tabla de registros de esta provincia", expanded=False):
            _render_tabla_registros(provincia, props_prov_asoc, regs_asoc)

        st.divider()

        # ── Asociaciones existentes ───────────────────────────────────────────
        asocs_prov = [a for a in get_asociaciones_local() if a.get("provincia") == provincia]

        if asocs_prov:
            st.subheader("Asociaciones de esta provincia")
            for asoc in asocs_prov:
                miembros = asoc.get("miembros", [])
                props    = asoc.get("propiedades_ord", [])
                with st.expander(
                    f"**{asoc['nombre']}** | {len(miembros)} miembro(s) | Props: {', '.join(props)}"
                ):
                    if miembros:
                        df_m = pd.DataFrame([{
                            "Ciudadano": m.get("alias", "?"),
                            "ID": m.get("id_racional", "?"),
                        } for m in miembros])
                        st.dataframe(df_m, use_container_width=True, hide_index=True)
                    if st.button("✏️ Editar asociación", key=f"{pref}edit_asoc_{asoc['id']}"):
                        st.session_state[f"{pref}edit_asoc_id"]      = asoc["id"]
                        st.session_state[f"{pref}edit_asoc_nombre"]   = asoc["nombre"]
                        st.session_state[f"{pref}edit_asoc_props"]    = asoc["propiedades_ord"]
                        st.session_state[f"{pref}edit_asoc_miembros"] = {
                            m["ciudadano_id"]: m.get("id_racional", "")
                            for m in miembros
                        }
                        st.rerun()
            st.divider()

        # ── Formulario de creación / edición ──────────────────────────────────
        modo_edicion = f"{pref}edit_asoc_id" in st.session_state
        st.subheader("Editar asociación" if modo_edicion else "Crear nueva asociación")

        if not props_prov_asoc:
            st.warning("No hay propiedades disponibles en esta provincia.")
        else:
            nombre_def  = st.session_state.get(f"{pref}edit_asoc_nombre", "")
            nombre_asoc = st.text_input(
                "Nombre de la asociación",
                value=nombre_def,
                placeholder=f'ej: "Asociación {NOMBRES_PROVINCIA[provincia]} Alpha"',
                key=f"{pref}prov_asoc_nombre",
            )

            st.markdown("**Selecciona propiedades (el orden importa):**")
            prop_opciones_asoc = {
                f"{_PROV_BADGE.get(p.get('provincia','?'), '?')} "
                f"{p.get('descripcion_corta', p['codigo'])} (p={p['primo_asignado']})": p
                for p in props_prov_asoc
            }
            default_props = []
            if modo_edicion:
                codigos_previos = st.session_state.get(f"{pref}edit_asoc_props", [])
                default_props = [k for k, v in prop_opciones_asoc.items()
                                 if v["codigo"] in codigos_previos]

            props_display_asoc = st.multiselect(
                "Propiedades de la asociación",
                options=list(prop_opciones_asoc.keys()),
                default=default_props,
                max_selections=LIMITE_PROPS[provincia],
                key=f"{pref}prov_asoc_props",
            )
            props_sel_objs   = [prop_opciones_asoc[d] for d in props_display_asoc]
            props_sel_codigos = [p["codigo"]        for p in props_sel_objs]
            primos_sel        = [p["primo_asignado"] for p in props_sel_objs]

            if props_sel_codigos:
                st.markdown("**Propiedades seleccionadas:**")
                for i, p_obj in enumerate(props_sel_objs):
                    badge = _PROV_BADGE.get(p_obj.get("provincia", "?"), "?")
                    st.markdown(
                        f"{i+1}. {badge} **{p_obj.get('descripcion_corta', p_obj['codigo'])}** "
                        f"— primo: `{p_obj['primo_asignado']}`"
                    )

                st.divider()
                st.subheader("Introducir números de asociado")
                st.markdown("""
                Cada ciudadano calcula su número de asociado según las propiedades que satisface o no.
                Introdúcelo en formato **numerador/denominador** (ej: `6/5`).
                """)

                fracs_previas = (
                    st.session_state.get(f"{pref}edit_asoc_miembros", {})
                    if modo_edicion else {}
                )

                filas_header = st.columns([3, 2])
                filas_header[0].markdown("**Ciudadano**")
                filas_header[1].markdown("**Número de asociado**")

                for c in todos_provincia:
                    cols = st.columns([3, 2])
                    cols[0].markdown(nombre_con_retrato_html(c, size=24), unsafe_allow_html=True)
                    frac_val = fracs_previas.get(c["id"], "")
                    cols[1].text_input(
                        "fracción", value=frac_val, placeholder="ej: 6/5",
                        key=f"{pref}prov_frac_{c['id']}",
                        label_visibility="collapsed",
                    )

                st.divider()

                if st.button("🔍 Verificar números de asociado", type="primary",
                             key=f"{pref}prov_verificar"):
                    fracciones_intro = {
                        c["id"]: st.session_state.get(f"{pref}prov_frac_{c['id']}", "").strip()
                        for c in todos_provincia
                    }
                    fracciones_intro = {cid: f for cid, f in fracciones_intro.items() if f}

                    if not fracciones_intro:
                        st.warning("Introduce al menos un número de asociado.")
                    else:
                        resultados_verif = {}
                        for cid, frac_str in fracciones_intro.items():
                            c = get_ciudadano(cid)
                            if c:
                                r = validar_fraccion_miembro(c, props_sel_codigos, primos_sel, frac_str)
                                resultados_verif[cid] = {"ciudadano": c, "frac_str": frac_str, **r}
                        st.session_state[f"{pref}prov_verif_resultados"] = resultados_verif

                # Resultados
                res_key = f"{pref}prov_verif_resultados"
                if res_key in st.session_state and st.session_state[res_key]:
                    resultados_verif = st.session_state[res_key]
                    filas_r = []
                    todos_correctos = True
                    for cid, r in resultados_verif.items():
                        c = r["ciudadano"]
                        if not r["ok"]:
                            filas_r.append({
                                "Ciudadano": c["alias"],
                                "Introducido": r["frac_str"],
                                "Estado": f"❌ {r.get('error', '?')}",
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
                        btn_label = "💾 Guardar cambios" if modo_edicion else "💾 Guardar asociación"
                        if st.button(btn_label, type="primary", key=f"{pref}prov_guardar_asoc"):
                            miembros_data = []
                            for cid, r in resultados_verif.items():
                                c = r["ciudadano"]
                                miembros_data.append({
                                    "ciudadano_id": cid,
                                    "alias": c["alias"],
                                    "id_racional": r["introducido"],
                                    "patron": r["patron"],
                                })
                                for prop_codigo in props_sel_codigos:
                                    registrar_ciudadano_propiedad(cid, prop_codigo, provincia)

                            if modo_edicion:
                                actualizar_estado_asociacion_local(
                                    st.session_state[f"{pref}edit_asoc_id"], "reemplazada"
                                )
                                for key in [
                                    f"{pref}edit_asoc_id", f"{pref}edit_asoc_nombre",
                                    f"{pref}edit_asoc_props", f"{pref}edit_asoc_miembros",
                                ]:
                                    st.session_state.pop(key, None)

                            _guardar_asociacion_local(
                                nombre=nombre_asoc.strip(),
                                ambito="provincial",
                                provincia=provincia,
                                propiedades_ord=props_sel_codigos,
                                miembros=miembros_data,
                                created_by=rol,
                            )
                            st.success(f"✅ Asociación «{nombre_asoc}» guardada con {len(miembros_data)} miembro(s).")
                            del st.session_state[res_key]
                            st.rerun()
                    elif not nombre_asoc.strip():
                        st.caption("Ponle un nombre a la asociación para guardarla.")
                    elif not todos_correctos:
                        st.error("Corrige los errores antes de guardar.")

        if modo_edicion:
            if st.button("✖ Cancelar edición", key=f"{pref}prov_cancelar_edit"):
                for key in [
                    f"{pref}edit_asoc_id", f"{pref}edit_asoc_nombre",
                    f"{pref}edit_asoc_props", f"{pref}edit_asoc_miembros",
                    f"{pref}prov_verif_resultados",
                ]:
                    st.session_state.pop(key, None)
                st.rerun()


# ── Subfunción: tabla de registros ──────────────────────────────────────

def _render_tabla_registros(provincia: str, props_prov: list, regs_prov: list):
    """Renderiza la tabla de registros descubiertas por la provincia."""
    st.subheader("Tabla de registros de esta provincia")

    if not regs_prov:
        st.info("Aún no hay registros. Registra ciudadanos en propiedades para empezar.")
        return

    codigos_prov   = [p["codigo"] for p in props_prov]
    nombres_prop   = {p["codigo"]: p.get("descripcion_corta", p["codigo"]) for p in props_prov}
    matriz_desc    = get_matriz_descubierta(provincia=provincia)

    ciudadanos_vistos: dict[str, dict] = {}
    for r in regs_prov:
        cid = r["ciudadano_id"]
        if cid not in ciudadanos_vistos:
            c = get_ciudadano(cid)
            ciudadanos_vistos[cid] = c if c else {"alias": r.get("alias", cid), "portrait": ""}

    filas = []
    orden_ciudadanos = []
    for cid in sorted(ciudadanos_vistos):
        c = ciudadanos_vistos[cid]
        uri = portrait_data_uri(c)
        fila = {
            "Retrato": uri if uri else None,
            "Ciudadano": c.get("alias", cid),
        }
        for pc in codigos_prov:
            estado = matriz_desc.get(cid, {}).get(pc, "?")
            fila[nombres_prop[pc]] = "✅" if estado == "satisface" else ("❌" if estado == "no_satisface" else "?")
        filas.append(fila)
        orden_ciudadanos.append(c)

    col_cfg = {
        "Retrato": st.column_config.ImageColumn(label="", width="small")
    }
    st.dataframe(pd.DataFrame(filas), use_container_width=True,
                 hide_index=True, column_config=col_cfg)
    st.caption("✅ satisface · ❌ no satisface · ? sin registrar")
