"""
Componentes UI reutilizables para EKKLESIA.
Evita duplicar lógica de renderizado entre páginas.
"""

import streamlit as st
import pandas as pd
from core.grapher import plot_function, formatear_definicion_latex
from core.theme import badge_provincia, nombre_con_retrato_html, portrait_data_uri, ICONOS


def grid_funciones(ciudadanos: list[dict], cols: int = 3, height: int = 200,
                   key_prefix: str = "fig", mostrar_propiedades: bool = False):
    """
    Renderiza una rejilla de gráficas de funciones a trozos.
    Cada celda muestra: retrato + alias + definición LaTeX + gráfica.
    """
    for row_start in range(0, len(ciudadanos), cols):
        chunk = ciudadanos[row_start:row_start + cols]
        cols_ui = st.columns(cols)
        for col_ui, c in zip(cols_ui, chunk):
            with col_ui:
                # Retrato + alias en el encabezado de la celda
                st.markdown(
                    f"{nombre_con_retrato_html(c, size=30)} "
                    f"{badge_provincia(c['provincia'])}",
                    unsafe_allow_html=True,
                )
                try:
                    latex_def = formatear_definicion_latex(c["funcion_json"])
                    st.latex(latex_def)
                except Exception:
                    st.caption(str(c["funcion_json"]))

                try:
                    fig = plot_function(c["funcion_json"], alias="", height=height)
                    st.plotly_chart(fig, use_container_width=True,
                                   key=f"{key_prefix}_{c['id']}")
                except Exception as e:
                    st.warning(f"Error al graficar: {e}")

                if mostrar_propiedades:
                    props_c = c.get("propiedades", {})
                    if props_c:
                        sat = [k for k, v in props_c.items() if v]
                        nosat = [k for k, v in props_c.items() if not v]
                        with st.expander("Ver propiedades"):
                            if sat:
                                st.success("Satisface: " + ", ".join(sat))
                            if nosat:
                                st.error("No satisface: " + ", ".join(nosat))

        if row_start + cols < len(ciudadanos):
            st.divider()


def _enrich_con_retrato(filas: list[dict], ciudadanos: list[dict]) -> tuple[list[dict], dict]:
    """
    Añade la columna 'Retrato' (data URI) a filas alineadas con ciudadanos.
    Devuelve (filas_con_retrato, column_config).
    """
    for fila, c in zip(filas, ciudadanos):
        uri = portrait_data_uri(c)
        fila["Retrato"] = uri if uri else None
    # Mover 'Retrato' a la primera posición
    filas = [{k: v for k, v in ({"Retrato": f.pop("Retrato", None)} | f).items()} for f in filas]
    col_cfg = {
        "Retrato": st.column_config.ImageColumn(
            label="",
            width="small",
        )
    }
    return filas, col_cfg


def tabla_matriz_propiedades(ciudadanos: list[dict], propiedades: list[dict],
                             matriz: dict[str, dict[str, bool]],
                             mostrar_provincia: bool = True):
    """
    Renderiza la tabla ciudadanos x propiedades con emojis y retrato.
    """
    filas = []
    for c in ciudadanos:
        fila = {"Apodo": c["alias"]}
        if mostrar_provincia:
            fila["Prov."] = c["provincia"][:3].upper()
        for p in propiedades:
            val = matriz.get(c["id"], {}).get(p["codigo"])
            fila[p.get("descripcion_corta") or p["codigo"]] = (
                "✅" if val is True else "❌" if val is False else "?"
            )
        filas.append(fila)

    if filas:
        filas, col_cfg = _enrich_con_retrato(filas, ciudadanos)
        st.dataframe(pd.DataFrame(filas), use_container_width=True,
                     hide_index=True, column_config=col_cfg)
    else:
        st.info("Sin datos para mostrar.")


def tabla_estadisticas_propiedades(ciudadanos: list[dict], propiedades: list[dict],
                                   matriz: dict[str, dict[str, bool]]):
    """Tabla resumen: cuántos satisfacen cada propiedad."""
    stats = []
    for p in propiedades:
        vals = [matriz.get(c["id"], {}).get(p["codigo"]) for c in ciudadanos]
        n_sat = sum(1 for v in vals if v is True)
        n_no = sum(1 for v in vals if v is False)
        total = max(n_sat + n_no, 1)
        stats.append({
            "Propiedad": p.get("descripcion_corta") or p["codigo"],
            f"{ICONOS['propiedad']} Primo": p.get("primo_asignado", "?"),
            "Satisfacen": n_sat,
            "No satisfacen": n_no,
            "% Sí": f"{100*n_sat/total:.0f}%",
        })
    if stats:
        st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)


def selector_propiedades(propiedades: list[dict], max_selections: int | None = None,
                         key: str = "prop_sel") -> list[str]:
    """
    Multiselect de propiedades que devuelve los códigos seleccionados.
    """
    prop_opciones = {
        p.get("descripcion_corta") or p["codigo"]: p["codigo"]
        for p in propiedades
    }
    kwargs = {"key": key}
    if max_selections:
        kwargs["max_selections"] = max_selections

    display = st.multiselect(
        "Propiedades",
        options=list(prop_opciones.keys()),
        **kwargs,
    )
    return [prop_opciones[d] for d in display]


def tabla_preview_colectivo(ciudadanos: list[dict], propiedades_all: list[dict],
                            props_sel: list[str], matriz: dict[str, dict[str, bool]]):
    """
    Tabla de previsualización para colectivos: quién satisface TODAS las propiedades.
    Devuelve la lista de IDs de miembros.
    """
    filas_prev = []
    miembros = []
    for c in ciudadanos:
        props_c = matriz.get(c["id"], {})
        en_col = all(props_c.get(p, False) for p in props_sel)
        fila = {"Apodo": c["alias"]}
        for pc in props_sel:
            p_obj = next((p for p in propiedades_all if p["codigo"] == pc), None)
            nombre_col = (p_obj.get("descripcion_corta") or pc) if p_obj else pc
            fila[nombre_col] = "✅" if props_c.get(pc) else "❌"
        fila["En colectivo"] = "✅" if en_col else "—"
        filas_prev.append(fila)
        if en_col:
            miembros.append(c["id"])

    if filas_prev:
        filas_prev, col_cfg = _enrich_con_retrato(filas_prev, ciudadanos)
        st.dataframe(pd.DataFrame(filas_prev), use_container_width=True,
                     hide_index=True, column_config=col_cfg)
    st.info(f"**{len(miembros)}** ciudadanos satisfacen todas las propiedades seleccionadas.")
    return miembros
