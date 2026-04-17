"""
EKKLESIA — Poder Judicial (CGPJ)
Valida asociaciones propuestas por las provincias.
Herramienta de verificación de IDs racionales.
"""

import streamlit as st
import pandas as pd
from core.auth import requiere_rol
from core.db import (
    get_ciudadanos, get_propiedades, get_matriz_propiedades,
    get_asociaciones_local, validar_asociacion,
)
from core.theme import aplicar_css_global, header_rol, badge_estado, badge_provincia, ICONOS, NOMBRES_PROVINCIA
from core.prime_ids import calcular_ids_asociacion, validar_unicidad, explicar_id

st.set_page_config(page_title="Poder Judicial — EKKLESIA", page_icon="⚖️", layout="wide")
aplicar_css_global()
requiere_rol("poder_judicial")

# Banner de intervención del rey
if st.session_state.get("rol") == "rey" and st.session_state.get("intervenir"):
    st.warning("⚠️ **Intervenido por el Rey** — estás en la pantalla del Poder Judicial.")

header_rol("poder_judicial", "Validación de asociaciones y verificación de identidades racionales")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_pendientes, tab_aprobadas, tab_verificador = st.tabs([
    "📋 Asociaciones Pendientes",
    "✅ Asociaciones Aprobadas",
    "🔍 Verificador de IDs",
])


# ═══ TAB 1: Asociaciones Pendientes ═════════════════════════════════════════
with tab_pendientes:
    st.subheader("Asociaciones pendientes de validación")
    st.markdown("""
    Las provincias envían propuestas de asociaciones. Tu función es **verificar**
    que los IDs racionales son correctos y **únicos**, y aprobar o rechazar cada una.
    """)

    pendientes = get_asociaciones_local(estado="pendiente")

    if not pendientes:
        st.info("No hay asociaciones pendientes de validación. Las provincias las proponen desde su pantalla.")
    else:
        st.caption(f"{len(pendientes)} asociación(es) pendiente(s)")

        for idx, asoc in enumerate(pendientes):
            miembros = asoc.get("miembros", [])
            props = asoc.get("propiedades_ord", [])
            prov = asoc.get("provincia", "nacional")
            prov_nombre = NOMBRES_PROVINCIA.get(prov, prov.capitalize() if prov else "Nacional")

            st.markdown("---")
            st.markdown(f"### {ICONOS['asociacion']} {asoc['nombre']}")

            # Info general
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Provincia:** {badge_provincia(prov) if prov else 'Nacional'}",
                        unsafe_allow_html=True)
            c2.markdown(f"**Miembros:** {len(miembros)}")
            c3.markdown(f"**Propiedades:** {len(props)}")

            # Propiedades usadas
            propiedades_all = get_propiedades()
            props_detalle = []
            for pc in props:
                p_obj = next((p for p in propiedades_all if p["codigo"] == pc), None)
                if p_obj:
                    props_detalle.append(f"**{p_obj.get('descripcion_corta', pc)}** (p={p_obj['primo_asignado']})")
                else:
                    props_detalle.append(pc)
            st.markdown("**Propiedades:** " + " · ".join(props_detalle))

            # Tabla de miembros con IDs racionales
            if miembros:
                filas = []
                for m in miembros:
                    patron = m.get("patron", [])
                    patron_str = " ".join("✅" if s else "❌" for s in patron)
                    filas.append({
                        "Ciudadano": m.get("alias", m.get("ciudadano_id", "?")),
                        "Patrón (prop.)": patron_str,
                        "Numerador": " × ".join(str(p) for p in m.get("primos_sat", [])) or "1",
                        "Denominador": " × ".join(str(p) for p in m.get("primos_nosat", [])) or "1",
                        "ID Racional": m.get("id_racional", "?"),
                        "ID Decimal": m.get("id_decimal", "?"),
                    })

                df = pd.DataFrame(filas)
                st.dataframe(df, use_container_width=True, hide_index=True)

            # Verificación automática de unicidad
            ids_dict = {}
            for m in miembros:
                cid = m.get("ciudadano_id", "?")
                ids_dict[cid] = {
                    "id_racional": m.get("id_racional", "?"),
                    "patron": m.get("patron", []),
                }
            validacion = validar_unicidad(ids_dict)

            if validacion["valida"]:
                st.success("✅ **Verificación automática:** Todos los IDs son únicos. Asociación válida.")
            else:
                st.error(f"❌ **Verificación automática:** {validacion['mensaje']}")

            # Explicación detallada
            with st.expander("🔍 Ver explicación detallada de cada ID"):
                for m in miembros:
                    st.markdown(f"#### {m.get('alias', '?')}")
                    explicacion = explicar_id(
                        m.get("id_racional", "?"),
                        props,
                        m.get("patron", []),
                    )
                    st.markdown(explicacion)
                    st.divider()

            # Botones de acción
            st.markdown("**Decisión:**")
            col_apr, col_rej = st.columns(2)
            with col_apr:
                if st.button("✅ Aprobar asociación", key=f"pj_apr_{asoc['id']}",
                             type="primary", use_container_width=True):
                    validar_asociacion(asoc["id"], es_valida=True)
                    st.success(f"Asociación «{asoc['nombre']}» aprobada.")
                    st.rerun()
            with col_rej:
                motivo = st.text_input("Motivo de rechazo (opcional)",
                                       key=f"pj_mot_{asoc['id']}",
                                       placeholder="ej: IDs no son únicos")
                if st.button("❌ Rechazar asociación", key=f"pj_rej_{asoc['id']}",
                             use_container_width=True):
                    validar_asociacion(asoc["id"], es_valida=False,
                                       motivo=motivo or "Rechazada por el Poder Judicial")
                    st.warning(f"Asociación «{asoc['nombre']}» rechazada.")
                    st.rerun()


# ═══ TAB 2: Asociaciones Aprobadas ══════════════════════════════════════════
with tab_aprobadas:
    st.subheader("Registro de asociaciones aprobadas")

    aprobadas = get_asociaciones_local(estado="aprobada")

    if not aprobadas:
        st.info("Aún no hay asociaciones aprobadas.")
    else:
        # Métricas globales
        total_ciudadanos = len(get_ciudadanos())
        ciudadanos_en_asoc = set()
        for asoc in aprobadas:
            for m in asoc.get("miembros", []):
                ciudadanos_en_asoc.add(m.get("ciudadano_id"))

        m1, m2, m3 = st.columns(3)
        m1.metric("Asociaciones aprobadas", len(aprobadas))
        m2.metric("Ciudadanos identificados", len(ciudadanos_en_asoc))
        m3.metric("Progreso", f"{len(ciudadanos_en_asoc)}/{total_ciudadanos}")

        pct = len(ciudadanos_en_asoc) / max(total_ciudadanos, 1)
        st.progress(min(pct, 1.0))

        if pct >= 1.0:
            st.success("🎉 **¡Asociación nacional completa!** Todos los ciudadanos están identificados.")
        else:
            st.caption(f"Faltan {total_ciudadanos - len(ciudadanos_en_asoc)} ciudadanos por identificar.")

        st.divider()

        # Lista de asociaciones
        for asoc in aprobadas:
            miembros = asoc.get("miembros", [])
            props = asoc.get("propiedades_ord", [])
            prov = asoc.get("provincia", "nacional")
            prov_nombre = NOMBRES_PROVINCIA.get(prov, prov.capitalize() if prov else "Nacional")

            with st.expander(
                f"✅ **{asoc['nombre']}** | {prov_nombre} | "
                f"{len(miembros)} miembros | Props: {', '.join(props)}"
            ):
                if miembros:
                    df_m = pd.DataFrame([{
                        "Ciudadano": m.get("alias", "?"),
                        "ID Racional": m.get("id_racional", "?"),
                        "ID Decimal": m.get("id_decimal", "?"),
                    } for m in miembros])
                    st.dataframe(df_m, use_container_width=True, hide_index=True)

    # Rechazadas (informativo)
    rechazadas = get_asociaciones_local(estado="rechazada")
    if rechazadas:
        st.divider()
        with st.expander(f"Asociaciones rechazadas ({len(rechazadas)})"):
            for asoc in rechazadas:
                st.markdown(f"❌ **{asoc['nombre']}** — {asoc.get('motivo_rechazo', 'Sin motivo')}")


# ═══ TAB 3: Verificador de IDs ══════════════════════════════════════════════
with tab_verificador:
    st.subheader("🔍 Verificador de IDs racionales")
    st.markdown("""
    Herramienta para **probar combinaciones** de propiedades y ciudadanos
    antes de que las provincias envíen sus propuestas formales.

    Selecciona propiedades y ciudadanos para ver si los IDs resultantes son únicos.
    """)

    ciudadanos_all = get_ciudadanos()
    propiedades_all = get_propiedades()

    if not ciudadanos_all or not propiedades_all:
        st.warning("No hay datos cargados.")
    else:
        cids_all = [c["id"] for c in ciudadanos_all]
        matriz_all = get_matriz_propiedades(cids_all)

        col_p, col_c = st.columns([1, 1])

        with col_p:
            st.markdown("**Propiedades**")
            prop_opciones = {
                f"{p.get('descripcion_corta') or p['codigo']} (p={p['primo_asignado']})": p["codigo"]
                for p in propiedades_all
            }
            props_display = st.multiselect("Selecciona propiedades",
                                           options=list(prop_opciones.keys()),
                                           key="verif_props")
            props_sel = [prop_opciones[d] for d in props_display]

        with col_c:
            st.markdown("**Ciudadanos**")

            # Filtro por provincia
            prov_filtro = st.selectbox("Filtrar provincia",
                                       ["Todas", "magnitudia", "intervalia", "brevitas"],
                                       key="verif_prov")
            ciud_filtrados = (
                ciudadanos_all if prov_filtro == "Todas"
                else [c for c in ciudadanos_all if c["provincia"] == prov_filtro]
            )

            ciud_opciones = {c["alias"]: c["id"] for c in ciud_filtrados}
            ciud_display = st.multiselect("Selecciona ciudadanos",
                                          options=list(ciud_opciones.keys()),
                                          key="verif_ciud")
            ciud_sel_ids = [ciud_opciones[d] for d in ciud_display]

        if props_sel and ciud_sel_ids:
            st.markdown("---")
            st.subheader("Resultado de la verificación")

            ciud_sel = [c for c in ciudadanos_all if c["id"] in ciud_sel_ids]
            ids_calculados = calcular_ids_asociacion(ciud_sel, props_sel, matriz_all)
            validacion = validar_unicidad(ids_calculados)

            # Tabla
            filas = []
            for c in ciud_sel:
                datos = ids_calculados.get(c["id"], {})
                patron = datos.get("patron", [])
                filas.append({
                    "Alias": c["alias"],
                    "Provincia": c["provincia"].capitalize(),
                    "Patrón": " ".join("✅" if s else "❌" for s in patron),
                    "ID Racional": datos.get("id_racional", "?"),
                    "ID Decimal": datos.get("id_decimal", "?"),
                })

            st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

            if validacion["valida"]:
                st.success(f"✅ Todos los IDs son únicos — {len(ciud_sel_ids)} ciudadanos identificados.")
            else:
                st.error(f"❌ {validacion['mensaje']}")

            # Explicación
            with st.expander("Ver explicación detallada"):
                for c in ciud_sel:
                    datos = ids_calculados.get(c["id"], {})
                    st.markdown(f"#### {c['alias']}")
                    st.markdown(explicar_id(
                        datos.get("id_racional", "?"),
                        props_sel,
                        datos.get("patron", []),
                    ))
                    st.divider()
