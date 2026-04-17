"""
EKKLESIA — Pantalla del Rey (Profesor / Admin)
Vista maestra omnisciente: ciudadanos, gráficas, propiedades, colectivos, asociaciones, ad-hoc.
"""

import streamlit as st
import pandas as pd
from core.auth import requiere_rol
from core.db import (
    get_ciudadanos, get_propiedades, get_matriz_propiedades, get_matriz_descubierta,
    get_estado_global,
    insertar_propiedad, upsert_ciudadano_propiedad,
    _insertar_propiedad_local, _actualizar_propiedad_ciudadanos_local,
    _guardar_colectivo_local, get_colectivos_local,
    get_asociaciones_local, validar_asociacion,
)
from core.math_engine import evaluar_todos_ciudadanos
from core.grapher import plot_function, formatear_definicion_latex
from core.theme import aplicar_css_global, header_rol, badge_provincia, badge_estado, ICONOS, portrait_data_uri
from core.components import (
    grid_funciones, tabla_matriz_propiedades, tabla_estadisticas_propiedades,
    selector_propiedades, tabla_preview_colectivo,
)
from core.prime_ids import calcular_ids_asociacion, validar_unicidad, explicar_id

st.set_page_config(page_title="Rey — Vista Maestra", page_icon="👑", layout="wide")
aplicar_css_global()
requiere_rol("rey")

header_rol("rey", "Jefe del Estado de Funcionalia")

# ── Modo Intervención ─────────────────────────────────────────────────────────
_col_int, _ = st.columns([1, 4])
with _col_int:
    _intervenir = st.toggle(
        "🚨 Modo Intervención",
        value=st.session_state.get("intervenir", False),
        key="toggle_intervenir",
        help=(
            "Activa el acceso total a todas las pantallas sin contraseña.\n\n"
            "*Nota: en España, la figura del rey está muy limitada por la Constitución, "
            "y no existe ningún mecanismo, ni siquiera estados excepcionales de alarma, "
            "excepción, o sitio, que permitan al rey intervenir activamente en los poderes del Estado.*"
        ),
    )
    st.session_state.intervenir = _intervenir

if st.session_state.get("intervenir"):
    st.warning("🚨 **Modo Intervención activo** — tienes acceso a todas las pantallas de Funcionalia.")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_estado, tab_graficas, tab_matriz, tab_colectivos, tab_asociaciones, tab_adhoc = st.tabs([
    f"{ICONOS['bloques']} Estado Global",
    f"{ICONOS['grafica']} Gráficas",
    f"{ICONOS['propiedad']} Matriz de Propiedades",
    f"{ICONOS['colectivo']} Colectivos",
    f"{ICONOS['asociacion']} Asociaciones",
    "➕ Nueva Propiedad",
])


# ═══ TAB 1: Estado Global ════════════════════════════════════════════════════
with tab_estado:
    st.subheader("Estado de Funcionalia")

    try:
        estado = get_estado_global()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Turno", estado["turno"])
        c2.metric("Total bloques", estado["total_bloques"])
        c3.metric("Leyes promulgadas", estado["leyes_promulgadas"])
        c4.metric("Asociaciones", estado["asociaciones"])
    except Exception as e:
        st.caption(f"Sin BD: {e}")

    ciudadanos = get_ciudadanos()
    if ciudadanos:
        df = pd.DataFrame(ciudadanos)
        st.divider()
        st.subheader("Distribución de bloques por provincia")

        resumen = df.groupby("provincia").agg(
            ciudadanos=("id", "count"),
            total=("bloques", "sum"),
            media=("bloques", "mean"),
            mín=("bloques", "min"),
            máx=("bloques", "max"),
        ).reset_index()
        resumen["Δ equidad"] = (resumen["media"] - 10).abs().round(2)
        st.dataframe(resumen, use_container_width=True, hide_index=True)

        st.bar_chart(df.set_index("alias")["bloques"], height=250)


# ═══ TAB 2: Gráficas y Definiciones ══════════════════════════════════════════
with tab_graficas:
    ciudadanos = get_ciudadanos()
    if not ciudadanos:
        st.info("No hay ciudadanos cargados.")
    else:
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            prov_opts = ["Todas"] + sorted({c["provincia"] for c in ciudadanos})
            prov_sel = st.selectbox("Provincia", prov_opts, key="graf_prov")
        with col_f2:
            aliases = [c["alias"] for c in ciudadanos
                       if prov_sel == "Todas" or c["provincia"] == prov_sel]
            sel_alias = st.multiselect("Funciones específicas (vacío = todas)",
                                       aliases, key="graf_sel")

        ciudadanos_vis = [
            c for c in ciudadanos
            if (prov_sel == "Todas" or c["provincia"] == prov_sel)
            and (not sel_alias or c["alias"] in sel_alias)
        ]

        st.caption(f"Mostrando {len(ciudadanos_vis)} funciones")
        st.divider()

        grid_funciones(ciudadanos_vis, cols=3, key_prefix="rey_fig",
                       mostrar_propiedades=True)


# ═══ TAB 3: Matriz de Propiedades ═══════════════════════════════════════════
with tab_matriz:
    ciudadanos = get_ciudadanos()
    propiedades = get_propiedades()

    if not ciudadanos or not propiedades:
        st.info("Carga ciudadanos y propiedades para ver la matriz.")
    else:
        # Abreviaturas de provincia para las cabeceras
        _PROV_ABREV = {"magnitudia": "MAG", "intervalia": "INT", "brevitas": "BRE"}

        prov_f = st.selectbox("Filtrar ciudadanos por provincia",
                              ["Todas", "magnitudia", "intervalia", "brevitas"],
                              key="mat_prov")
        ciud_filtrados = (ciudadanos if prov_f == "Todas"
                          else [c for c in ciudadanos if c["provincia"] == prov_f])

        cids = [c["id"] for c in ciud_filtrados]

        vista = st.radio("Vista", ["Oráculo (verdad completa)", "Registros (descubierto)"],
                         horizontal=True, key="mat_vista")

        if vista == "Oráculo (verdad completa)":
            st.subheader("Tabla de verdad — oráculo")
            st.caption("El rey ve el estado real de todas las propiedades. ✅ satisface · ❌ no satisface")
            matriz = get_matriz_propiedades(cids)

            # Construir DataFrame con provincia en la cabecera de columna
            filas = []
            for c in ciud_filtrados:
                uri = portrait_data_uri(c)
                fila = {
                    "Retrato": uri if uri else None,
                    "Ciudadano": c["alias"],
                    "Prov.": _PROV_ABREV.get(c["provincia"], c["provincia"][:3].upper()),
                }
                for p in propiedades:
                    col_name = f"{p.get('descripcion_corta', p['codigo'])} [{_PROV_ABREV.get(p.get('provincia',''), '?')}]"
                    val = matriz.get(c["id"], {}).get(p["codigo"])
                    fila[col_name] = "✅" if val else "❌"
                filas.append(fila)

            _col_cfg_rey = {"Retrato": st.column_config.ImageColumn(label="", width="small")}
            st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True,
                         column_config=_col_cfg_rey)

            st.divider()
            st.subheader("Estadísticas por propiedad")
            tabla_estadisticas_propiedades(ciud_filtrados, propiedades, matriz)

        else:
            st.subheader("Tabla de registros — lo descubierto por las provincias")
            st.caption("✅ satisface · ❌ no satisface · ? aún no registrado")
            matriz_desc = get_matriz_descubierta(ciudadano_ids=cids)

            filas = []
            for c in ciud_filtrados:
                uri = portrait_data_uri(c)
                fila = {
                    "Retrato": uri if uri else None,
                    "Ciudadano": c["alias"],
                    "Prov.": _PROV_ABREV.get(c["provincia"], c["provincia"][:3].upper()),
                }
                for p in propiedades:
                    col_name = f"{p.get('descripcion_corta', p['codigo'])} [{_PROV_ABREV.get(p.get('provincia',''), '?')}]"
                    estado = matriz_desc.get(c["id"], {}).get(p["codigo"], "desconocido")
                    if estado == "satisface":
                        fila[col_name] = "✅"
                    elif estado == "no_satisface":
                        fila[col_name] = "❌"
                    else:
                        fila[col_name] = "?"
                filas.append(fila)

            _col_cfg_desc = {"Retrato": st.column_config.ImageColumn(label="", width="small")}
            st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True,
                         column_config=_col_cfg_desc)

            # Resumen de descubrimiento
            st.divider()
            total_celdas = len(ciud_filtrados) * len(propiedades)
            _meta_cols_r = {"Retrato", "Ciudadano", "Prov."}
            celdas_descubiertas = sum(
                1 for r in filas for k, v in r.items()
                if k not in _meta_cols_r and v != "?"
            )
            # Excluir columnas no-propiedad del recuento
            _meta_cols = {"Retrato", "Ciudadano", "Prov."}
            celdas_descubiertas = sum(
                1 for r in filas for k, v in r.items()
                if k not in _meta_cols and v != "?"
            )
            if total_celdas > 0:
                pct_desc = celdas_descubiertas / total_celdas
                st.metric("Celdas descubiertas",
                          f"{celdas_descubiertas} / {total_celdas}",
                          f"{pct_desc:.0%}")
                st.progress(pct_desc)


# ═══ TAB 4: Colectivos ═══════════════════════════════════════════════════════
with tab_colectivos:

    st.subheader("Colectivos registrados")
    colectivos = get_colectivos_local()
    if colectivos:
        for col_item in colectivos:
            props_col = col_item.get("propiedades", [])
            miembros_col = col_item.get("miembros", [])
            etiqueta = (f"**{col_item['nombre']}** | {col_item['ambito']} | "
                        f"Props: {', '.join(props_col)} | {len(miembros_col)} miembros")
            with st.expander(etiqueta):
                if miembros_col:
                    todos_c = get_ciudadanos()
                    miembros_info = [c for c in todos_c if c["id"] in miembros_col]
                    if miembros_info:
                        filas_col = [{
                            "Retrato": portrait_data_uri(c) or None,
                            "Alias": c["alias"],
                            "Provincia": c["provincia"].capitalize(),
                            "Bloques": c["bloques"],
                        } for c in miembros_info]
                        _col_cfg_col = {"Retrato": st.column_config.ImageColumn(label="", width="small")}
                        st.dataframe(pd.DataFrame(filas_col), use_container_width=True,
                                     hide_index=True, column_config=_col_cfg_col)
                else:
                    st.info("Sin miembros.")
    else:
        st.info("Aún no hay colectivos creados.")

    st.divider()

    # ── Crear nuevo colectivo ─────────────────────────────────────────────────
    st.subheader("Crear nuevo colectivo")
    st.markdown("""
    Selecciona propiedades → mira quién satisface **todas** → ponle nombre y guárdalo.
    """)

    ciudadanos_all = get_ciudadanos()
    propiedades_all = get_propiedades()

    if not ciudadanos_all or not propiedades_all:
        st.warning("Necesitas ciudadanos y propiedades cargados.")
    else:
        cids_all = [c["id"] for c in ciudadanos_all]
        matriz_all = get_matriz_propiedades(cids_all)

        prov_col = st.selectbox("Ámbito",
                                ["nacional", "magnitudia", "intervalia", "brevitas"],
                                key="col_prov")
        ciudadanos_scope = (
            ciudadanos_all if prov_col == "nacional"
            else [c for c in ciudadanos_all if c["provincia"] == prov_col]
        )

        col_izq, col_der = st.columns([1, 1])
        with col_izq:
            st.markdown("**Propiedades del colectivo**")
            props_seleccionadas = selector_propiedades(propiedades_all, key="col_props_sel")

        with col_der:
            miembros_auto = []
            if props_seleccionadas:
                st.markdown("**Vista previa: ¿quién satisface TODAS?**")
                miembros_auto = tabla_preview_colectivo(
                    ciudadanos_scope, propiedades_all, props_seleccionadas, matriz_all
                )
            else:
                st.info("← Selecciona propiedades para ver la previsualización.")

        if props_seleccionadas:
            st.divider()
            col_n1, col_n2 = st.columns([2, 1])
            with col_n1:
                nombre_col = st.text_input("Nombre del colectivo",
                                           placeholder='ej: "Continuas en 0 y crecientes"',
                                           key="col_nombre")
            with col_n2:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("💾 Guardar colectivo", type="primary", use_container_width=True):
                    if not nombre_col.strip():
                        st.error("Ponle un nombre al colectivo.")
                    else:
                        try:
                            _guardar_colectivo_local(
                                nombre=nombre_col.strip(),
                                ambito="provincial" if prov_col != "nacional" else "nacional",
                                provincia=prov_col if prov_col != "nacional" else None,
                                prop_codigos=props_seleccionadas,
                                miembros_ids=miembros_auto,
                                created_by="rey",
                            )
                            st.success(f"Colectivo «{nombre_col}» guardado con {len(miembros_auto)} miembros.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")


# ═══ TAB 5: Asociaciones ════════════════════════════════════════════════════
with tab_asociaciones:
    st.subheader(f"{ICONOS['asociacion']} Gestión de Asociaciones")
    st.markdown("""
    Las asociaciones son grupos de ciudadanos **únicamente identificables** entre sí
    mediante un conjunto de propiedades matemáticas. Cada miembro recibe un
    **ID racional único** basado en números primos.
    """)

    todas_asoc = get_asociaciones_local()

    if not todas_asoc:
        st.info("Aún no hay asociaciones propuestas. Las provincias pueden crearlas desde su pantalla.")
    else:
        # Separar por estado
        pendientes = [a for a in todas_asoc if a["estado"] == "pendiente"]
        aprobadas = [a for a in todas_asoc if a["estado"] == "aprobada"]
        rechazadas = [a for a in todas_asoc if a["estado"] == "rechazada"]

        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Pendientes", len(pendientes))
        m2.metric("Aprobadas", len(aprobadas))
        m3.metric("Rechazadas", len(rechazadas))

        st.divider()

        # ── Pendientes: el Rey puede aprobar/rechazar ─────────────────────────
        if pendientes:
            st.subheader("Asociaciones pendientes de validación")
            for asoc in pendientes:
                miembros = asoc.get("miembros", [])
                props = asoc.get("propiedades_ord", [])
                with st.expander(
                    f"📋 **{asoc['nombre']}** | {asoc.get('provincia', 'nacional').capitalize()} | "
                    f"{len(miembros)} miembros | Props: {', '.join(props)}"
                ):
                    # Tabla de miembros con IDs
                    if miembros:
                        df_m = pd.DataFrame([{
                            "Alias": m.get("alias", m.get("ciudadano_id", "?")),
                            "ID Racional": m.get("id_racional", "?"),
                            "ID Decimal": m.get("id_decimal", "?"),
                        } for m in miembros])
                        st.dataframe(df_m, use_container_width=True, hide_index=True)

                    # Validación de unicidad
                    ids_dict = {}
                    for m in miembros:
                        cid = m.get("ciudadano_id", "?")
                        ids_dict[cid] = {
                            "id_racional": m.get("id_racional", "?"),
                            "patron": m.get("patron", []),
                        }
                    validacion = validar_unicidad(ids_dict)
                    if validacion["valida"]:
                        st.success("✅ Todos los IDs son únicos — asociación válida.")
                    else:
                        st.error(f"❌ {validacion['mensaje']}")

                    # Botones de acción
                    col_apr, col_rej = st.columns(2)
                    with col_apr:
                        if st.button("✅ Aprobar", key=f"apr_{asoc['id']}", type="primary",
                                     use_container_width=True):
                            validar_asociacion(asoc["id"], es_valida=True)
                            st.success("Asociación aprobada.")
                            st.rerun()
                    with col_rej:
                        motivo = st.text_input("Motivo de rechazo", key=f"mot_{asoc['id']}",
                                               placeholder="Opcional")
                        if st.button("❌ Rechazar", key=f"rej_{asoc['id']}",
                                     use_container_width=True):
                            validar_asociacion(asoc["id"], es_valida=False,
                                               motivo=motivo or "Rechazada por el Rey")
                            st.warning("Asociación rechazada.")
                            st.rerun()

        # ── Aprobadas ────────────────────────────────────────────────────────
        if aprobadas:
            st.divider()
            st.subheader("Asociaciones aprobadas")
            for asoc in aprobadas:
                miembros = asoc.get("miembros", [])
                props = asoc.get("propiedades_ord", [])
                with st.expander(
                    f"✅ **{asoc['nombre']}** | {asoc.get('provincia', 'nacional').capitalize()} | "
                    f"{len(miembros)} miembros"
                ):
                    if miembros:
                        df_m = pd.DataFrame([{
                            "Alias": m.get("alias", "?"),
                            "ID Racional": m.get("id_racional", "?"),
                            "ID Decimal": m.get("id_decimal", "?"),
                        } for m in miembros])
                        st.dataframe(df_m, use_container_width=True, hide_index=True)
                    st.caption(f"Propiedades: {', '.join(props)}")

        # ── Rechazadas ───────────────────────────────────────────────────────
        if rechazadas:
            st.divider()
            with st.expander(f"Asociaciones rechazadas ({len(rechazadas)})"):
                for asoc in rechazadas:
                    st.markdown(
                        f"❌ **{asoc['nombre']}** — {asoc.get('motivo_rechazo', 'Sin motivo')}"
                    )

    # ── Progreso hacia la asociación nacional ────────────────────────────────
    st.divider()
    total_ciudadanos = len(get_ciudadanos())
    ciudadanos_en_asoc = set()
    for asoc in [a for a in todas_asoc if a["estado"] == "aprobada"]:
        for m in asoc.get("miembros", []):
            ciudadanos_en_asoc.add(m.get("ciudadano_id"))
    pct = len(ciudadanos_en_asoc) / max(total_ciudadanos, 1) * 100

    st.subheader("Progreso hacia la asociación nacional")
    st.progress(min(pct / 100, 1.0))
    st.caption(f"{len(ciudadanos_en_asoc)}/{total_ciudadanos} ciudadanos identificados ({pct:.0f}%)")


# ═══ TAB 6: Nueva Propiedad Ad-hoc ══════════════════════════════════════════
with tab_adhoc:
    st.subheader("Añadir nueva propiedad matemática")
    st.markdown("""
    Escribe una propiedad y una expresión SymPy opcional para evaluarla automáticamente.
    Se asignará el siguiente número primo disponible y se actualizará la matriz.
    """)

    with st.form("nueva_prop_form", clear_on_submit=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            codigo = st.text_input("Código único", placeholder="ej: creciente_1_2")
            desc_corta = st.text_input("Descripción corta", placeholder="ej: Crec. (1,2)")
        with c2:
            descripcion = st.text_input("Descripción completa",
                                        placeholder="ej: f es estrictamente creciente en (1, 2)")
            nivel = st.selectbox("Nivel", ["basico", "medio", "bachillerato"])

        sympy_expr = st.text_area(
            "Expresión SymPy (opcional)",
            placeholder="ej: limit(f, x, 0) == 1\nej: len(solve(f - x, x)) > 0",
            height=80,
        )
        submitted = st.form_submit_button("Añadir propiedad", type="primary")

    if submitted:
        if not codigo.strip() or not descripcion.strip():
            st.error("El código y la descripción son obligatorios.")
        else:
            ciudadanos_ev = get_ciudadanos()
            resultados: dict[str, bool] = {}
            if sympy_expr.strip():
                with st.spinner("Evaluando contra todos los ciudadanos..."):
                    resultados = evaluar_todos_ciudadanos(sympy_expr.strip(), ciudadanos_ev)
            else:
                resultados = {c["id"]: False for c in ciudadanos_ev}

            try:
                nueva_prop = insertar_propiedad(
                    codigo.strip(), descripcion.strip(), sympy_expr.strip(), es_adhoc=True
                )
                prop_id = nueva_prop["id"]
                for cid, satisface in resultados.items():
                    upsert_ciudadano_propiedad(cid, prop_id, satisface)
                st.success(f"✅ Propiedad guardada. Primo asignado: **{nueva_prop['primo_asignado']}**")
            except Exception:
                try:
                    nueva_prop = _insertar_propiedad_local(
                        codigo=codigo.strip(), descripcion=descripcion.strip(),
                        sympy_expr=sympy_expr.strip(), descripcion_corta=desc_corta.strip(),
                        nivel=nivel,
                    )
                    if resultados:
                        _actualizar_propiedad_ciudadanos_local(codigo.strip(), resultados)
                    st.success(f"✅ Propiedad guardada localmente. Primo: **{nueva_prop['primo_asignado']}**")
                except ValueError as ve:
                    st.error(str(ve))
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

            if resultados:
                n_sat = sum(1 for v in resultados.values() if v)
                cc1, cc2 = st.columns(2)
                cc1.metric("Satisfacen", n_sat)
                cc2.metric("No satisfacen", len(resultados) - n_sat)

                with st.expander("Ver detalle"):
                    for c in ciudadanos_ev:
                        icono = "✅" if resultados.get(c["id"]) else "❌"
                        st.markdown(f"{icono} {c['alias']}")

    st.divider()
    st.subheader("Propiedades registradas")
    propiedades = get_propiedades()
    if propiedades:
        df_props = pd.DataFrame([{
            "Código": p["codigo"],
            "Descripción": p["descripcion"],
            "Primo p": p.get("primo_asignado", "?"),
            "Nivel": p.get("nivel", "?"),
            "Ad-hoc": "✅" if p.get("es_adhoc") else "—",
        } for p in propiedades])
        st.dataframe(df_props, use_container_width=True, hide_index=True)
    else:
        st.info("Sin propiedades cargadas.")
