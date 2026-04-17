"""
Sistema de identificación por números primos.
Implementa la mecánica central de las asociaciones:
  - Asignar primos a propiedades (en orden)
  - Calcular el ID racional de cada ciudadano
  - Validar unicidad de una asociación
"""

from math import gcd
from functools import reduce
from fractions import Fraction


# ── Lista de primos pre-generada (suficiente para 30+ propiedades) ────────────
def _criba_eratostenes(limite: int) -> list[int]:
    es_primo = [True] * (limite + 1)
    es_primo[0] = es_primo[1] = False
    for i in range(2, int(limite**0.5) + 1):
        if es_primo[i]:
            for j in range(i * i, limite + 1, i):
                es_primo[j] = False
    return [i for i in range(2, limite + 1) if es_primo[i]]


PRIMOS = _criba_eratostenes(500)  # los primeros ~95 primos, suficiente para el juego


def primo_para_posicion(n: int) -> int:
    """
    Devuelve el primo correspondiente a la posición n (base 0).
    Posición 0 → 2, posición 1 → 3, posición 2 → 5, ...
    """
    if n < 0 or n >= len(PRIMOS):
        raise ValueError(f"Posición {n} fuera de rango (máx {len(PRIMOS) - 1})")
    return PRIMOS[n]


def calcular_id_racional(patron_satisface: list[bool], primos: list[int]) -> Fraction:
    """
    Dado un patrón de True/False y la lista de primos asignados,
    calcula el ID racional del ciudadano.

    numerador   = ∏ primos[i] donde patron[i] = True
    denominador = ∏ primos[i] donde patron[i] = False

    Returns: Fraction (e.g., Fraction(6, 5))
    """
    if len(patron_satisface) != len(primos):
        raise ValueError("El patrón y la lista de primos deben tener la misma longitud")

    numerador = 1
    denominador = 1
    for satisface, primo in zip(patron_satisface, primos):
        if satisface:
            numerador *= primo
        else:
            denominador *= primo

    return Fraction(numerador, denominador)


def calcular_ids_asociacion(
    ciudadanos: list[dict],
    propiedades_ord: list[str],
    matriz: dict[str, dict[str, bool]],
) -> dict[str, dict]:
    """
    Calcula los IDs racionales para todos los ciudadanos de una asociación.

    Args:
        ciudadanos: Lista de dicts con al menos {'id': str}
        propiedades_ord: Lista de códigos de propiedad EN ORDEN
        matriz: {ciudadano_id: {propiedad_codigo: bool}}

    Returns:
        {ciudadano_id: {
            'patron': [True, False, ...],
            'primos_sat': [2, 5, ...],
            'primos_nosat': [3, ...],
            'fraccion': Fraction(6, 5),
            'id_racional': '6/5',
            'id_decimal': 1.2,
        }}
    """
    primos = [primo_para_posicion(i) for i in range(len(propiedades_ord))]
    resultado = {}

    for ciudadano in ciudadanos:
        cid = ciudadano["id"]
        props_ciudadano = matriz.get(cid, {})

        patron = [bool(props_ciudadano.get(cod, False)) for cod in propiedades_ord]
        fraccion = calcular_id_racional(patron, primos)

        primos_sat = [p for p, s in zip(primos, patron) if s]
        primos_nosat = [p for p, s in zip(primos, patron) if not s]

        resultado[cid] = {
            "patron": patron,
            "primos_sat": primos_sat,
            "primos_nosat": primos_nosat,
            "fraccion": fraccion,
            "id_racional": f"{fraccion.numerator}/{fraccion.denominator}",
            "id_decimal": round(float(fraccion), 6),
        }

    return resultado


def validar_unicidad(ids: dict[str, dict]) -> dict:
    """
    Verifica que todos los IDs racionales sean únicos.

    Returns:
        {
            'valida': bool,
            'colisiones': [{
                'id_racional': '6/5',
                'ciudadanos': [cid1, cid2, ...]
            }],
            'mensaje': str
        }
    """
    por_fraccion: dict[str, list[str]] = {}
    for cid, datos in ids.items():
        key = datos["id_racional"]
        por_fraccion.setdefault(key, []).append(cid)

    colisiones = [
        {"id_racional": key, "ciudadanos": lista}
        for key, lista in por_fraccion.items()
        if len(lista) > 1
    ]

    if not colisiones:
        return {"valida": True, "colisiones": [], "mensaje": "Asociación válida: todos los IDs son únicos."}

    msgs = []
    for col in colisiones:
        msgs.append(
            f"ID {col['id_racional']} compartido por {len(col['ciudadanos'])} ciudadanos: "
            f"tienen exactamente el mismo patrón de propiedades."
        )
    return {
        "valida": False,
        "colisiones": colisiones,
        "mensaje": "Asociación inválida:\n" + "\n".join(msgs),
    }


def validar_fraccion_miembro(
    ciudadano: dict,
    propiedades_ord: list[str],
    primos_asignados: list[int],
    fraccion_str: str,
) -> dict:
    """
    Verifica que la fracción introducida por un alumno es correcta.

    Args:
        ciudadano: dict con campo 'propiedades' (oráculo, bool por código)
        propiedades_ord: códigos en orden (definen el patrón)
        primos_asignados: primo de cada propiedad (en el mismo orden)
        fraccion_str: string introducido por el usuario, ej: "6/5"

    Returns:
        {
            ok: bool,           # False si hay error de parseo
            error: str,         # mensaje de error si ok=False
            correcto: bool,     # True si la fracción es la esperada
            esperado: str,      # ej "6/5"
            introducido: str,   # la fracción parseada y reducida
            patron: [bool],
        }
    """
    oraculo = ciudadano.get("propiedades", {})
    patron = [bool(oraculo.get(p, False)) for p in propiedades_ord]
    fraccion_esperada = calcular_id_racional(patron, primos_asignados)

    fraccion_str = fraccion_str.strip().replace(",", ".")
    if not fraccion_str:
        return {"ok": False, "error": "Campo vacío."}

    try:
        if "/" in fraccion_str:
            num_s, den_s = fraccion_str.split("/", 1)
            introducida = Fraction(int(num_s.strip()), int(den_s.strip()))
        else:
            # Número entero (denominador = 1)
            introducida = Fraction(int(fraccion_str))
    except (ValueError, ZeroDivisionError):
        return {"ok": False, "error": f"Formato inválido: '{fraccion_str}'. Usa 'p/q' o un entero."}

    return {
        "ok": True,
        "correcto": introducida == fraccion_esperada,
        "esperado": f"{fraccion_esperada.numerator}/{fraccion_esperada.denominator}",
        "introducido": f"{introducida.numerator}/{introducida.denominator}",
        "patron": patron,
    }


def explicar_id(id_racional: str, propiedades_ord: list[str], patron: list[bool]) -> str:
    """
    Genera una explicación legible del ID racional de un ciudadano.
    """
    primos = [primo_para_posicion(i) for i in range(len(propiedades_ord))]
    lineas = ["**Cálculo del identificador racional:**", ""]

    sat = [(p, primos[i]) for i, (p, s) in enumerate(zip(propiedades_ord, patron)) if s]
    nosat = [(p, primos[i]) for i, (p, s) in enumerate(zip(propiedades_ord, patron)) if not s]

    if sat:
        num_expr = " × ".join(str(p) for _, p in sat)
        num_props = ", ".join(f"P{i+1}" for i, s in enumerate(patron) if s)
        lineas.append(f"✅ Numerador ({num_props}): {num_expr} = {reduce(lambda a, b: a*b, [p for _, p in sat])}")
    else:
        lineas.append("✅ Numerador: 1 (no satisface ninguna propiedad)")

    if nosat:
        den_expr = " × ".join(str(p) for _, p in nosat)
        den_props = ", ".join(f"P{i+1}" for i, s in enumerate(patron) if not s)
        lineas.append(f"❌ Denominador ({den_props}): {den_expr} = {reduce(lambda a, b: a*b, [p for _, p in nosat])}")
    else:
        lineas.append("❌ Denominador: 1 (satisface todas las propiedades)")

    lineas.append(f"\n**ID racional = {id_racional}**")
    return "\n".join(lineas)
