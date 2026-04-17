"""
Cliente Supabase centralizado.
Todas las queries a la BD pasan por este módulo.
"""

import streamlit as st
import json
import uuid
from datetime import datetime
from pathlib import Path

# ── Singleton del cliente Supabase ────────────────────────────────────────────
_PLACEHOLDERS = {"TU-PROYECTO", "TU-ANON-KEY-AQUI", "UUID-DE-LA-SESION", ""}


@st.cache_resource
def get_client():
    """
    Devuelve el cliente Supabase.
    Falla INMEDIATAMENTE (sin esperar timeout de red) si las credenciales
    son las de ejemplo o no están configuradas.
    """
    try:
        from supabase import create_client
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")

        # Detectar credenciales de ejemplo → fallo rápido, sin timeout de red
        if not url or any(p in url for p in _PLACEHOLDERS):
            raise RuntimeError("Supabase: credenciales de ejemplo. Usando modo local.")
        if not key or any(p in key for p in _PLACEHOLDERS):
            raise RuntimeError("Supabase: credenciales de ejemplo. Usando modo local.")

        return create_client(url, key)
    except KeyError:
        raise RuntimeError("Supabase no configurado (faltan claves en secrets.toml).")
    except ImportError:
        raise RuntimeError("supabase-py no instalado: pip install supabase")


def get_sesion_id() -> str:
    return st.secrets.get("SESION_ID", "")


# ── Fallback: datos locales JSON (para desarrollo sin Supabase) ───────────────
_DATA_DIR = Path(__file__).parent.parent / "data"


def _load_local(nombre: str) -> list | dict:
    path = _DATA_DIR / f"{nombre}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def _save_local(nombre: str, data: list | dict):
    """Persiste datos en el JSON local."""
    path = _DATA_DIR / f"{nombre}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _insertar_propiedad_local(
    codigo: str, descripcion: str, sympy_expr: str,
    descripcion_corta: str = "", nivel: str = "basico",
) -> dict:
    """
    Inserta una nueva propiedad en propiedades.json y la inicializa en
    ciudadanos.json con valor False para todos. Devuelve el dict de la propiedad.
    """
    from core.prime_ids import PRIMOS

    props = _load_local("propiedades")
    # Verificar que el código no existe ya
    if any(p["codigo"] == codigo for p in props):
        raise ValueError(f"Ya existe una propiedad con código '{codigo}'")

    usados = {p.get("primo_asignado") for p in props if p.get("primo_asignado")}
    nuevo_primo = next(p for p in PRIMOS if p not in usados)

    nueva = {
        "id": f"prop-{str(uuid.uuid4())[:8]}",
        "codigo": codigo,
        "descripcion": descripcion,
        "descripcion_corta": descripcion_corta or codigo,
        "sympy_expr": sympy_expr,
        "primo_asignado": nuevo_primo,
        "nivel": nivel,
        "es_adhoc": True,
    }
    props.append(nueva)
    _save_local("propiedades", props)

    # Inicializar la propiedad en todos los ciudadanos con False
    ciudadanos = _load_local("ciudadanos")
    for c in ciudadanos:
        c.setdefault("propiedades", {})[codigo] = False
    _save_local("ciudadanos", ciudadanos)

    return nueva


def _actualizar_propiedad_ciudadanos_local(codigo: str, resultados: dict[str, bool]):
    """Actualiza el valor de una propiedad en ciudadanos.json con los resultados calculados."""
    ciudadanos = _load_local("ciudadanos")
    for c in ciudadanos:
        if c["id"] in resultados:
            c.setdefault("propiedades", {})[codigo] = resultados[c["id"]]
    _save_local("ciudadanos", ciudadanos)


def _guardar_colectivo_local(
    nombre: str, ambito: str, provincia: str | None,
    prop_codigos: list[str], miembros_ids: list[str], created_by: str,
) -> dict:
    """Guarda un colectivo en colectivos.json (modo local)."""
    colectivos = _load_local("colectivos")
    nuevo = {
        "id": f"col-{str(uuid.uuid4())[:8]}",
        "nombre": nombre,
        "ambito": ambito,
        "provincia": provincia,
        "propiedades": prop_codigos,  # códigos, no UUIDs en modo local
        "miembros": miembros_ids,
        "estado": "completo",
        "created_by": created_by,
    }
    colectivos.append(nuevo)
    _save_local("colectivos", colectivos)
    return nuevo


def añadir_miembro_colectivo_local(colectivo_id: str, ciudadano_id: str) -> bool:
    """Añade un ciudadano a los miembros de un colectivo local. Devuelve True si se añadió."""
    colectivos = _load_local("colectivos")
    for col in colectivos:
        if col["id"] == colectivo_id:
            miembros = col.setdefault("miembros", [])
            if ciudadano_id not in miembros:
                miembros.append(ciudadano_id)
                _save_local("colectivos", colectivos)
                return True
            return False  # ya estaba
    return False  # colectivo no encontrado


def get_colectivos_local(ambito: str | None = None, provincia: str | None = None) -> list[dict]:
    cols = _load_local("colectivos")
    if ambito:
        cols = [c for c in cols if c.get("ambito") == ambito]
    if provincia:
        cols = [c for c in cols if c.get("provincia") == provincia]
    return cols


# ── Ciudadanos ────────────────────────────────────────────────────────────────
def get_ciudadanos(provincia: str | None = None) -> list[dict]:
    """Devuelve ciudadanos de la sesión activa, opcionalmente filtrados por provincia."""
    try:
        client = get_client()
        sesion_id = get_sesion_id()
        q = client.table("ciudadanos").select("*").eq("sesion_id", sesion_id)
        if provincia:
            q = q.eq("provincia", provincia)
        return q.execute().data
    except Exception:
        ciudadanos = _load_local("ciudadanos")
        if provincia:
            return [c for c in ciudadanos if c.get("provincia") == provincia]
        return ciudadanos


def get_ciudadano(ciudadano_id: str) -> dict | None:
    try:
        client = get_client()
        res = client.table("ciudadanos").select("*").eq("id", ciudadano_id).single().execute()
        return res.data
    except Exception:
        for c in _load_local("ciudadanos"):
            if c["id"] == ciudadano_id:
                return c
        return None


def actualizar_bloques(ciudadano_id: str, delta: int) -> dict:
    client = get_client()
    sesion_id = get_sesion_id()
    ciudadano = get_ciudadano(ciudadano_id)
    nuevos = max(0, ciudadano["bloques"] + delta)
    client.table("ciudadanos").update({"bloques": nuevos}).eq("id", ciudadano_id).execute()
    client.table("movimientos_bloques").insert({
        "sesion_id": sesion_id,
        "ciudadano_id": ciudadano_id,
        "delta": delta,
        "bloques_antes": ciudadano["bloques"],
        "bloques_despues": nuevos,
    }).execute()
    return {"bloques_antes": ciudadano["bloques"], "bloques_despues": nuevos}


# ── Propiedades ───────────────────────────────────────────────────────────────
def get_propiedades() -> list[dict]:
    try:
        client = get_client()
        sesion_id = get_sesion_id()
        return (
            client.table("propiedades")
            .select("*")
            .eq("sesion_id", sesion_id)
            .order("primo_asignado")
            .execute()
            .data
        )
    except Exception:
        return _load_local("propiedades")


def insertar_propiedad(codigo: str, descripcion: str, sympy_expr: str, es_adhoc: bool = True) -> dict:
    client = get_client()
    sesion_id = get_sesion_id()
    # Calcular siguiente primo disponible
    props = get_propiedades()
    primos_usados = [p["primo_asignado"] for p in props if p.get("primo_asignado")]
    from core.prime_ids import PRIMOS
    usados_set = set(primos_usados)
    nuevo_primo = next(p for p in PRIMOS if p not in usados_set)

    data = {
        "sesion_id": sesion_id,
        "codigo": codigo,
        "descripcion": descripcion,
        "sympy_expr": sympy_expr,
        "primo_asignado": nuevo_primo,
        "es_adhoc": es_adhoc,
    }
    res = client.table("propiedades").insert(data).execute()
    return res.data[0]


# ── Matriz ciudadano × propiedad ──────────────────────────────────────────────
def get_matriz_propiedades(ciudadano_ids: list[str] | None = None) -> dict[str, dict[str, bool]]:
    """
    Devuelve {ciudadano_id: {propiedad_codigo: bool}}
    """
    try:
        client = get_client()
        q = (
            client.table("ciudadano_propiedades")
            .select("ciudadano_id, propiedad_id, satisface, propiedades(codigo)")
        )
        if ciudadano_ids:
            q = q.in_("ciudadano_id", ciudadano_ids)
        filas = q.execute().data

        matriz: dict[str, dict[str, bool]] = {}
        for fila in filas:
            cid = fila["ciudadano_id"]
            codigo = fila["propiedades"]["codigo"]
            matriz.setdefault(cid, {})[codigo] = fila["satisface"]
        return matriz
    except Exception:
        # Fallback: leer desde el JSON local de ciudadanos
        ciudadanos = _load_local("ciudadanos")
        matriz = {}
        for c in ciudadanos:
            if ciudadano_ids and c["id"] not in ciudadano_ids:
                continue
            matriz[c["id"]] = c.get("propiedades", {})
        return matriz


def upsert_ciudadano_propiedad(ciudadano_id: str, propiedad_id: str, satisface: bool):
    client = get_client()
    client.table("ciudadano_propiedades").upsert({
        "ciudadano_id": ciudadano_id,
        "propiedad_id": propiedad_id,
        "satisface": satisface,
    }).execute()


# ── Colectivos ────────────────────────────────────────────────────────────────
def get_colectivos(ambito: str | None = None, provincia: str | None = None) -> list[dict]:
    try:
        client = get_client()
        sesion_id = get_sesion_id()
        q = client.table("colectivos").select("*").eq("sesion_id", sesion_id)
        if ambito:
            q = q.eq("ambito", ambito)
        if provincia:
            q = q.eq("provincia", provincia)
        return q.order("created_at", desc=True).execute().data
    except Exception:
        return []


def crear_colectivo(nombre: str, ambito: str, provincia: str | None,
                    propiedad_ids: list[str], created_by: str) -> dict:
    client = get_client()
    sesion_id = get_sesion_id()
    data = {
        "sesion_id": sesion_id,
        "nombre": nombre,
        "ambito": ambito,
        "provincia": provincia,
        "propiedades": propiedad_ids,
        "created_by": created_by,
    }
    return client.table("colectivos").insert(data).execute().data[0]


def añadir_miembro_colectivo(colectivo_id: str, ciudadano_id: str):
    client = get_client()
    client.table("colectivo_miembros").upsert({
        "colectivo_id": colectivo_id,
        "ciudadano_id": ciudadano_id,
        "verificado": True,
    }).execute()


# ── Asociaciones ──────────────────────────────────────────────────────────────

def _guardar_asociacion_local(
    nombre: str, ambito: str, provincia: str | None,
    propiedades_ord: list[str], miembros: list[dict], created_by: str,
) -> dict:
    """
    Guarda una asociación en asociaciones.json (modo local).
    miembros: lista de dicts con {ciudadano_id, alias, id_racional, id_decimal, patron, ...}
    """
    asociaciones = _load_local("asociaciones")
    nueva = {
        "id": f"asoc-{str(uuid.uuid4())[:8]}",
        "nombre": nombre,
        "ambito": ambito,
        "provincia": provincia,
        "propiedades_ord": propiedades_ord,
        "miembros": miembros,
        "estado": "pendiente",
        "created_by": created_by,
        "motivo_rechazo": None,
    }
    asociaciones.append(nueva)
    _save_local("asociaciones", asociaciones)
    return nueva


def get_asociaciones_local(estado: str | None = None, provincia: str | None = None) -> list[dict]:
    asocs = _load_local("asociaciones")
    if estado:
        asocs = [a for a in asocs if a.get("estado") == estado]
    if provincia:
        asocs = [a for a in asocs if a.get("provincia") == provincia]
    return asocs


def actualizar_estado_asociacion_local(asociacion_id: str, nuevo_estado: str, motivo: str | None = None):
    """Cambia el estado de una asociación local (pendiente → aprobada/rechazada)."""
    asociaciones = _load_local("asociaciones")
    for a in asociaciones:
        if a["id"] == asociacion_id:
            a["estado"] = nuevo_estado
            if motivo:
                a["motivo_rechazo"] = motivo
            break
    _save_local("asociaciones", asociaciones)


def get_asociaciones(ambito: str | None = None, provincia: str | None = None) -> list[dict]:
    try:
        client = get_client()
        sesion_id = get_sesion_id()
        q = client.table("asociaciones").select("*").eq("sesion_id", sesion_id)
        if ambito:
            q = q.eq("ambito", ambito)
        if provincia:
            q = q.eq("provincia", provincia)
        return q.order("created_at", desc=True).execute().data
    except Exception:
        return get_asociaciones_local(provincia=provincia)


def crear_asociacion(nombre: str, ambito: str, provincia: str | None,
                     propiedades_ord: list[str], miembros: list[dict],
                     created_by: str) -> dict:
    try:
        client = get_client()
        sesion_id = get_sesion_id()
        data = {
            "sesion_id": sesion_id,
            "nombre": nombre,
            "ambito": ambito,
            "provincia": provincia,
            "propiedades_ord": propiedades_ord,
            "created_by": created_by,
            "estado": "pendiente_validacion",
        }
        asoc = client.table("asociaciones").insert(data).execute().data[0]
        # Registrar miembros
        rows = [{"asociacion_id": asoc["id"], **m} for m in miembros]
        client.table("asociacion_miembros").insert(rows).execute()
        return asoc
    except Exception:
        return _guardar_asociacion_local(nombre, ambito, provincia, propiedades_ord, miembros, created_by)


def _escribir_registros_asociacion_local(asociacion_id: str):
    """
    Escribe en registros.json los patrones de propiedades de una asociación aprobada.
    Llama a registrar_ciudadano_propiedad (que consulta el oráculo), por lo que
    los valores siempre son correctos aunque el alumno haya enviado un patrón erróneo.
    """
    asociaciones = _load_local("asociaciones")
    asoc = next((a for a in asociaciones if a["id"] == asociacion_id), None)
    if not asoc:
        return
    props = asoc.get("propiedades_ord", [])
    origen = asoc.get("provincia") or "gobierno"
    for miembro in asoc.get("miembros", []):
        cid = miembro.get("ciudadano_id")
        if not cid:
            continue
        for prop_codigo in props:
            registrar_ciudadano_propiedad(cid, prop_codigo, registrado_por=f"asoc:{origen}")


def validar_asociacion(asociacion_id: str, es_valida: bool, motivo: str | None = None):
    try:
        client = get_client()
        update = {
            "es_valida": es_valida,
            "estado": "registrada" if es_valida else "rechazada",
        }
        if motivo:
            update["motivo_rechazo"] = motivo
        client.table("asociaciones").update(update).eq("id", asociacion_id).execute()
    except Exception:
        nuevo_estado = "aprobada" if es_valida else "rechazada"
        actualizar_estado_asociacion_local(asociacion_id, nuevo_estado, motivo)
    # Escribir registros en modo local siempre que se apruebe
    if es_valida:
        _escribir_registros_asociacion_local(asociacion_id)


# ── Registros (lo que los jugadores han descubierto) ────────────────────

def get_propiedades_provincia(provincia: str) -> list[dict]:
    """Propiedades que pertenecen a una provincia concreta O son nacionales [NAC]."""
    return [p for p in get_propiedades()
            if p.get("provincia") == provincia or p.get("provincia") == "nacional"]


def get_primo_de_propiedad(propiedad_codigo: str) -> int | None:
    """Devuelve el primo asignado a una propiedad dado su código."""
    for p in get_propiedades():
        if p["codigo"] == propiedad_codigo:
            return p.get("primo_asignado")
    return None


def nationalizar_colectivo(colectivo_id: str) -> bool:
    """
    Convierte un colectivo provincial en nacional:
    - Cambia ambito a 'nacional' y provincia a None
    - Promueve todas sus propiedades a [NAC]
    Devuelve True si se realizó el cambio.
    """
    colectivos = _load_local("colectivos")
    for col in colectivos:
        if col["id"] == colectivo_id:
            if col.get("ambito") == "nacional":
                return False  # ya era nacional
            col["ambito"] = "nacional"
            col["provincia"] = None
            # Promover propiedades
            for pc in col.get("propiedades", []):
                promover_a_nacional(pc)
            _save_local("colectivos", colectivos)
            return True
    return False


def promover_a_nacional(propiedad_codigo: str) -> bool:
    """
    Cambia la provincia de una propiedad a 'nacional'.
    Devuelve True si se hizo el cambio, False si ya era nacional o no se encontró.
    """
    props = _load_local("propiedades")
    for p in props:
        if p["codigo"] == propiedad_codigo:
            if p.get("provincia") == "nacional":
                return False  # ya era nacional
            p["provincia"] = "nacional"
            _save_local("propiedades", props)
            return True
    return False


def get_registros(provincia: str | None = None) -> list[dict]:
    """
    Devuelve las registros guardadas.
    provincia: si se especifica, filtra las registradas POR esa provincia.
    """
    regs = _load_local("registros")
    if provincia:
        regs = [r for r in regs if r.get("registrado_por") == provincia]
    return regs


def get_matriz_descubierta(
    ciudadano_ids: list[str] | None = None,
    provincia: str | None = None,
) -> dict[str, dict[str, str]]:
    """
    Devuelve {ciudadano_id: {propiedad_codigo: "satisface"|"no_satisface"|"desconocido"}}
    Solo incluye filas con al menos una registro (desconocido implica ausencia).
    provincia: si se especifica, solo las registradas por esa provincia.
    """
    regs = get_registros(provincia=provincia)
    matriz: dict[str, dict[str, str]] = {}
    for r in regs:
        cid = r["ciudadano_id"]
        if ciudadano_ids and cid not in ciudadano_ids:
            continue
        matriz.setdefault(cid, {})[r["propiedad_codigo"]] = r["estado"]
    return matriz


def registrar_ciudadano_propiedad(
    ciudadano_id: str,
    propiedad_codigo: str,
    registrado_por: str,
) -> dict:
    """
    Verifica con el oráculo (ciudadanos.json) si el ciudadano satisface la propiedad
    y guarda la registro. Devuelve {ok, satisface, estado, ya_registrado}.
    """
    ciudadano = get_ciudadano(ciudadano_id)
    if not ciudadano:
        return {"ok": False, "error": "Ciudadano no encontrado"}

    # Oráculo: campo 'propiedades' precalculado en ciudadanos.json
    oraculo = ciudadano.get("propiedades", {})
    if propiedad_codigo not in oraculo:
        return {"ok": False, "error": f"La propiedad '{propiedad_codigo}' no está evaluada para este ciudadano"}

    satisface: bool = bool(oraculo[propiedad_codigo])
    estado = "satisface" if satisface else "no_satisface"

    # Evitar duplicados: si ya está registrado, devolver sin reescribir
    regs = _load_local("registros")
    for r in regs:
        if r["ciudadano_id"] == ciudadano_id and r["propiedad_codigo"] == propiedad_codigo:
            return {"ok": True, "satisface": satisface, "estado": r["estado"], "ya_registrado": True}

    nueva = {
        "id": f"reg-{str(uuid.uuid4())[:8]}",
        "ciudadano_id": ciudadano_id,
        "alias": ciudadano.get("alias", ciudadano_id),
        "propiedad_codigo": propiedad_codigo,
        "estado": estado,
        "registrado_por": registrado_por,
        "timestamp": datetime.utcnow().isoformat(),
    }
    regs.append(nueva)
    _save_local("registros", regs)

    return {"ok": True, "satisface": satisface, "estado": estado, "ya_registrado": False}


def registrar_ciudadano_colectivo(
    ciudadano_id: str,
    colectivo_id: str,
    registrado_por: str,
) -> dict:
    """
    Intenta registrar un ciudadano en un colectivo (conjunto de propiedades).
    Devuelve {ok, todas_satisfechas, resultados: {prop_codigo: {satisface, ya_registrado}}}.
    """
    colectivos = _load_local("colectivos")
    col = next((c for c in colectivos if c["id"] == colectivo_id), None)
    if not col:
        return {"ok": False, "error": "Colectivo no encontrado"}

    props = col.get("propiedades", [])
    resultados = {}
    for prop_codigo in props:
        r = registrar_ciudadano_propiedad(ciudadano_id, prop_codigo, registrado_por)
        resultados[prop_codigo] = r

    todas_satisfechas = all(r.get("satisface") for r in resultados.values() if r.get("ok"))
    return {"ok": True, "todas_satisfechas": todas_satisfechas, "resultados": resultados}


# ── Leyes ─────────────────────────────────────────────────────────────────────
def get_leyes(estado: str | None = None) -> list[dict]:
    try:
        client = get_client()
        sesion_id = get_sesion_id()
        q = client.table("leyes").select("*").eq("sesion_id", sesion_id)
        if estado:
            q = q.eq("estado", estado)
        return q.order("created_at", desc=True).execute().data
    except Exception:
        return []


def proponer_ley(titulo: str, tipo: str, paquete: list[dict], propuesta_por: str) -> dict:
    client = get_client()
    sesion_id = get_sesion_id()
    suma_neta = sum(item.get("delta_bloques", 0) for item in paquete)
    data = {
        "sesion_id": sesion_id,
        "titulo": titulo,
        "tipo": tipo,
        "paquete_json": paquete,
        "propuesta_por": propuesta_por,
        "suma_neta": suma_neta,
    }
    return client.table("leyes").insert(data).execute().data[0]


# ── Estado global ─────────────────────────────────────────────────────────────
def get_estado_global() -> dict:
    try:
        client = get_client()
        sesion_id = get_sesion_id()

        sesion = client.table("sesiones").select("*").eq("id", sesion_id).single().execute().data
        leyes_count = len(client.table("leyes").select("id").eq("sesion_id", sesion_id).eq("estado", "promulgada").execute().data)
        asoc_count = len(client.table("asociaciones").select("id").eq("sesion_id", sesion_id).eq("estado", "registrada").execute().data)
        total_bloques = sum(c["bloques"] for c in get_ciudadanos())

        return {
            "turno": sesion.get("turno", 1),
            "total_bloques": total_bloques,
            "leyes_promulgadas": leyes_count,
            "asociaciones": asoc_count,
        }
    except Exception:
        ciudadanos = _load_local("ciudadanos")
        total = sum(c.get("bloques", 10) for c in ciudadanos)
        return {"turno": 1, "total_bloques": total, "leyes_promulgadas": 0, "asociaciones": 0}
