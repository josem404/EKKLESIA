"""
Motor matemático con SymPy.
Reconstruye funciones a trozos y evalúa propiedades sobre ellas.

Uso:
    funcion = rebuild_function(ciudadano['funcion_json'])
    resultado = eval_property('continua_en_0', funcion)
"""

from sympy import (
    symbols, sympify, Piecewise, oo, nan, limit, S,
    solve, Interval, Rational, diff,
    And, Or, Le, Ge,
)
from sympy.calculus.util import function_range

import traceback

x = symbols('x', real=True)

# Namespace compartido para sympify: garantiza que 'x' en las cadenas
# sea SIEMPRE nuestro símbolo x = symbols('x', real=True)
_NS = {'x': x, 'And': And, 'Or': Or, 'Le': Le, 'Ge': Ge, 'True': True, 'False': False}


# ── Reconstrucción de función a trozos ────────────────────────────────────────
def rebuild_function(funcion_json: list[dict]) -> Piecewise:
    """
    Convierte la representación JSON de una función a trozos en un objeto Piecewise de SymPy.

    funcion_json: [
        {"expr": "x**2", "condicion": "And(x >= 0, x < 1)"},
        {"expr": "2 - x", "condicion": "And(x >= 1, x <= 3)"},
    ]
    IMPORTANTE: sympify usa _NS para que 'x' sea siempre el mismo símbolo.
    """
    tramos = []
    for tramo in funcion_json:
        expr = sympify(tramo["expr"], locals=_NS)
        cond_str = tramo["condicion"]
        # "True" como condición = siempre activo (catch-all)
        if cond_str in ("True", "true"):
            cond = True
        else:
            cond = sympify(cond_str, locals=_NS)
        tramos.append((expr, cond))

    # Si el último tramo no es catch-all, añadir nan como indefinido fuera del dominio
    if tramos and tramos[-1][1] is not True:
        tramos.append((nan, True))

    return Piecewise(*tramos)


def _evaluar_en(f: Piecewise, punto) -> object:
    """Evalúa f en x=punto devolviendo el valor SymPy (puede ser nan, oo, número)."""
    from sympy import S as _S
    p = sympify(punto)
    return f.subs(x, p)


# ── Evaluadores de propiedades estándar ───────────────────────────────────────
def _es_continua_en(f: Piecewise, punto) -> bool:
    """f es continua en x = punto"""
    try:
        p = sympify(punto)
        val = _evaluar_en(f, p)
        lim_izq = limit(f, x, p, '-')
        lim_der = limit(f, x, p, '+')
        return bool(val == lim_izq == lim_der and val != nan and val != oo)
    except Exception:
        return False


def _esta_definida_en(f: Piecewise, punto) -> bool:
    """f(punto) existe y es finito"""
    try:
        val = _evaluar_en(f, sympify(punto))
        return bool(val != nan and val.is_finite)
    except Exception:
        return False


def _tiene_asintota_vertical(f: Piecewise) -> bool:
    """
    f tiene al menos una asíntota vertical.
    Estrategia: busca puntos candidatos donde algún denominador sea 0,
    y comprueba si el límite lateral es ±∞.
    """
    try:
        # Buscar denominadores en cada tramo de la Piecewise
        candidatos = set()
        from sympy import denom as _denom
        for expr, _ in f.args:
            d = _denom(expr)
            if d != 1 and d != S.One:
                raices = solve(d, x)
                candidatos.update(raices)

        for punto in candidatos:
            try:
                lim_der = limit(f, x, punto, '+')
                lim_izq = limit(f, x, punto, '-')
                if lim_der == oo or lim_der == -oo or lim_izq == oo or lim_izq == -oo:
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return False


def _tiene_asintota_horizontal(f: Piecewise) -> bool:
    """f tiene asíntota horizontal (lim x→±∞ es finito)"""
    try:
        lim_pos = limit(f, x, oo)
        lim_neg = limit(f, x, -oo)
        return bool(lim_pos.is_finite or lim_neg.is_finite)
    except Exception:
        return False


def _tiene_punto_fijo(f: Piecewise) -> bool:
    """Existe x tal que f(x) = x"""
    try:
        sols = solve(f - x, x)
        return bool(len(sols) > 0)
    except Exception:
        return False


def _es_acotada_superiormente(f: Piecewise, dominio=(-10, 10)) -> bool:
    """f está acotada superiormente en el dominio [-10, 10]"""
    try:
        rango = function_range(f, x, Interval(*dominio))
        return bool(rango.sup != oo)
    except Exception:
        # Fallback: muestreo numérico en el dominio
        try:
            import sympy as sp
            puntos = [sp.Rational(i, 10) for i in range(dominio[0]*10, dominio[1]*10 + 1, 5)]
            vals = [float(f.subs(x, p).evalf()) for p in puntos if f.subs(x, p).is_finite]
            return bool(vals and max(vals) < 1e6)
        except Exception:
            return False


# ── Evaluador genérico (para propiedades ad-hoc) ──────────────────────────────
def eval_property_standard(codigo: str, funcion_json: list[dict]) -> bool | None:
    """
    Evalúa una propiedad estándar (por código) sobre una función definida en JSON.
    Devuelve True/False o None si no reconoce el código.
    """
    PROPIEDADES_STANDARD = {
        "definida_en_0":        lambda f: _esta_definida_en(f, 0),
        "continua_en_0":        lambda f: _es_continua_en(f, 0),
        "continua_en_1":        lambda f: _es_continua_en(f, 1),
        "asintota_vertical":    lambda f: _tiene_asintota_vertical(f),
        "asintota_horizontal":  lambda f: _tiene_asintota_horizontal(f),
        "punto_fijo":           lambda f: _tiene_punto_fijo(f),
        "acotada_sup":          lambda f: _es_acotada_superiormente(f),
    }

    if codigo not in PROPIEDADES_STANDARD:
        return None

    try:
        f = rebuild_function(funcion_json)
        return bool(PROPIEDADES_STANDARD[codigo](f))
    except Exception:
        return None


def eval_property_adhoc(sympy_expr_str: str, funcion_json: list[dict]) -> bool:
    """
    Evalúa una propiedad ad-hoc expresada como string SymPy sobre una función.

    El string puede usar:
        f   — la función Piecewise
        x   — la variable simbólica
        Funciones SymPy estándar (limit, solve, etc.)

    Ejemplo:
        sympy_expr_str = "limit(f, x, 0) == 1"
        sympy_expr_str = "f.subs(x, 0) > 0"
        sympy_expr_str = "len(solve(f - x, x)) > 0"
    """
    try:
        f = rebuild_function(funcion_json)
        from sympy import denom as _denom
        namespace = {
            "f": f, "x": x,
            "limit": limit, "solve": solve, "oo": oo, "nan": nan,
            "Rational": Rational, "And": And, "Or": Or,
            "Interval": Interval, "S": S, "diff": diff, "denom": _denom,
        }
        resultado = eval(sympy_expr_str, {"__builtins__": {}}, namespace)
        return bool(resultado)
    except Exception as e:
        raise ValueError(f"Error evaluando '{sympy_expr_str}': {e}")


def _eval_con_timeout(sympy_expr_str: str, funcion_json: list[dict], timeout_s: float = 4.0) -> bool:
    """
    Evalúa una propiedad ad-hoc con timeout por función.
    Si SymPy tarda más de timeout_s segundos, devuelve False sin bloquear.
    Usa threading porque Windows no soporta signal.alarm.
    """
    import threading
    resultado = [False]
    error = [None]

    def _worker():
        try:
            resultado[0] = eval_property_adhoc(sympy_expr_str, funcion_json)
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=timeout_s)
    if t.is_alive():
        # SymPy se colgó — devolver False sin esperar más
        return False
    if error[0]:
        return False
    return resultado[0]


def evaluar_todos_ciudadanos(
    sympy_expr_str: str,
    ciudadanos: list[dict],
    timeout_por_funcion: float = 4.0,
) -> dict[str, bool]:
    """
    Evalúa una propiedad ad-hoc contra todos los ciudadanos.
    Aplica timeout por función para evitar que SymPy bloquee la UI.
    Returns: {ciudadano_id: True/False}
    """
    resultados = {}
    for c in ciudadanos:
        resultados[c["id"]] = _eval_con_timeout(
            sympy_expr_str, c["funcion_json"], timeout_s=timeout_por_funcion
        )
    return resultados


def recalcular_matriz_propiedad(
    propiedad_codigo: str,
    sympy_expr_str: str,
    ciudadanos: list[dict],
) -> dict[str, bool]:
    """
    Recalcula todos los valores de una propiedad para todos los ciudadanos.
    Primero intenta el evaluador estándar (por código), luego el ad-hoc.
    """
    resultados = {}
    for c in ciudadanos:
        # Intentar evaluador estándar primero
        res = eval_property_standard(propiedad_codigo, c["funcion_json"])
        if res is None and sympy_expr_str:
            try:
                res = eval_property_adhoc(sympy_expr_str, c["funcion_json"])
            except Exception:
                res = False
        resultados[c["id"]] = bool(res) if res is not None else False
    return resultados
