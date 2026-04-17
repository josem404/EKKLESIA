"""
Graficado numérico de funciones a trozos.
Usa plotly para integración nativa con Streamlit.
"""

import re
import numpy as np
import plotly.graph_objects as go
from sympy import sympify, latex, lambdify, nan as sym_nan
from core.math_engine import x as x_sym, _NS


# ── Paleta de colores por tramo ───────────────────────────────────────────────
_COLORS = ["#4FC3F7", "#EF5350", "#66BB6A", "#FFA726", "#AB47BC",
           "#26C6DA", "#EC407A", "#D4E157", "#8D6E63", "#78909C"]


def _parse_domain_bounds(cond_str: str) -> tuple[float, float]:
    """
    Extrae los límites numéricos del dominio de una condición.
    Soporta:  'And(x >= 0, x < 1)', 'x > 2', 'x <= -1', 'True'
    """
    if not cond_str or cond_str in ("True", "true"):
        return -5.0, 5.0

    # Busca todos los números (con signo) en la cadena
    nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", cond_str)]

    if len(nums) == 0:
        return -5.0, 5.0
    if len(nums) == 1:
        n = nums[0]
        # Determinar si es límite inferior o superior
        if re.search(r"x\s*[<≤]|<\s*x", cond_str):
            return n, n + 6.0
        if re.search(r"x\s*[>≥]|>\s*x", cond_str):
            return n - 6.0, n
        return n - 3.0, n + 3.0

    a, b = min(nums), max(nums)
    # Clamp razonable
    a = max(a, -12.0)
    b = min(b, 12.0)
    return (a, b) if a < b else (-5.0, 5.0)


def _fmt_num(n: float) -> str:
    """Formatea número: entero si es entero, decimal si no."""
    return str(int(n)) if n == int(n) else str(n)


def _parse_single_constraint(s: str):
    """
    Parsea una restricción simple sobre x.
    Devuelve (valor, op, rol) donde:
      rol = 'lower' si da límite inferior de x, 'upper' si da límite superior.
      op  = '>' | '>=' | '<' | '<=' como está para x (ya normalizado).
    Devuelve None si no lo puede parsear.
    """
    s = s.strip()
    # x OP n
    m = re.match(r"^x\s*(>=|<=|>|<)\s*(-?\d+(?:\.\d+)?)$", s)
    if m:
        op, n = m.group(1), float(m.group(2))
        rol = "lower" if op in (">", ">=") else "upper"
        return n, op, rol
    # n OP x → invert
    m = re.match(r"^(-?\d+(?:\.\d+)?)\s*(>=|<=|>|<)\s*x$", s)
    if m:
        n, op = float(m.group(1)), m.group(2)
        inv = {">=": "<=", "<=": ">=", ">": "<", "<": ">"}
        op_x = inv[op]  # op for x
        rol = "lower" if op_x in (">", ">=") else "upper"
        return n, op_x, rol
    return None


def _cond_to_latex(cond_str: str) -> str:
    """
    Convierte condición SymPy a LaTeX compacto.
    And(x>=0, x<1) → '0 \\le x < 1'
    x > 0          → 'x > 0'
    x != 0         → 'x \\ne 0'
    True           → 'x \\in \\mathbb{R}'
    """
    if cond_str in ("True", "true"):
        return r"x \in \mathbb{R}"
    if "!=" in cond_str:
        m = re.match(r"x\s*!=\s*(-?\d+(?:\.\d+)?)", cond_str)
        if m:
            return rf"x \ne {_fmt_num(float(m.group(1)))}"
        return cond_str

    m = re.match(r"^And\((.+),\s*(.+)\)$", cond_str)
    if m:
        p1 = _parse_single_constraint(m.group(1))
        p2 = _parse_single_constraint(m.group(2))
        if p1 and p2:
            lower = next((p for p in (p1, p2) if p[2] == "lower"), None)
            upper = next((p for p in (p1, p2) if p[2] == "upper"), None)
            if lower and upper:
                lo_n, lo_op, _ = lower
                hi_n, hi_op, _ = upper
                lo_sym = r"\le" if lo_op == ">=" else "<"
                hi_sym = r"\le" if hi_op == "<=" else "<"
                return f"{_fmt_num(lo_n)} {lo_sym} x {hi_sym} {_fmt_num(hi_n)}"

    # Single constraint fallback
    p = _parse_single_constraint(cond_str)
    if p:
        n, op, _ = p
        op_map = {">=": r"\ge", "<=": r"\le", ">": ">", "<": "<"}
        return f"x {op_map.get(op, op)} {_fmt_num(n)}"

    return cond_str


def _cond_to_readable(cond_str: str) -> str:
    """Texto plano compacto (para hover de gráficas, etc.)."""
    if cond_str in ("True", "true"):
        return "para todo x"
    if "!=" in cond_str:
        m = re.match(r"x\s*!=\s*(-?\d+(?:\.\d+)?)", cond_str)
        if m:
            return f"x ≠ {_fmt_num(float(m.group(1)))}"

    m = re.match(r"^And\((.+),\s*(.+)\)$", cond_str)
    if m:
        p1 = _parse_single_constraint(m.group(1))
        p2 = _parse_single_constraint(m.group(2))
        if p1 and p2:
            lower = next((p for p in (p1, p2) if p[2] == "lower"), None)
            upper = next((p for p in (p1, p2) if p[2] == "upper"), None)
            if lower and upper:
                lo_n, lo_op, _ = lower
                hi_n, hi_op, _ = upper
                lo_sym = "≤" if lo_op == ">=" else "<"
                hi_sym = "≤" if hi_op == "<=" else "<"
                return f"{_fmt_num(lo_n)} {lo_sym} x {hi_sym} {_fmt_num(hi_n)}"

    p = _parse_single_constraint(cond_str)
    if p:
        n, op, _ = p
        op_map = {">=": "≥", "<=": "≤", ">": ">", "<": "<"}
        return f"x {op_map.get(op, op)} {_fmt_num(n)}"

    return cond_str


def formatear_definicion_latex(funcion_json: list[dict]) -> str:
    """Devuelve la definición de la función a trozos como LaTeX."""
    partes = []
    for tramo in funcion_json:
        try:
            expr = sympify(tramo["expr"], locals=_NS)
            expr_latex = latex(expr)
        except Exception:
            expr_latex = tramo["expr"]
        cond_latex = _cond_to_latex(tramo["condicion"])
        partes.append(rf"{expr_latex} & \text{{si }} {cond_latex}")

    inner = r" \\ ".join(partes)
    return rf"f(x) = \begin{{cases}} {inner} \end{{cases}}"


def plot_function(
    funcion_json: list[dict],
    alias: str = "f(x)",
    height: int = 220,
    show_title: bool = True,
) -> go.Figure:
    """
    Grafica una función a trozos usando plotly.
    Evalúa cada tramo numéricamente sobre su dominio.
    """
    fig = go.Figure()

    for i, tramo in enumerate(funcion_json):
        cond_str = tramo["condicion"]
        if cond_str in ("True", "true") and i > 0:
            # tramo catch-all: usar dominio del tramo anterior extendido
            prev_a, prev_b = _parse_domain_bounds(funcion_json[i - 1]["condicion"])
            # Solo ampliar si tiene sentido (evita graficar el nan final)
            if tramo["expr"] in ("nan", "NaN"):
                continue
            a, b = prev_b, prev_b + 4.0
        else:
            a, b = _parse_domain_bounds(cond_str)

        try:
            expr = sympify(tramo["expr"], locals=_NS)
            if expr == sym_nan:
                continue
            f_np = lambdify(x_sym, expr, modules="numpy")
            t = np.linspace(a, b, 400)
            with np.errstate(divide="ignore", invalid="ignore"):
                y = np.array(f_np(t), dtype=float)
            y = np.where(np.isfinite(y), y, np.nan)

            color = _COLORS[i % len(_COLORS)]
            fig.add_trace(go.Scatter(
                x=t, y=y,
                mode="lines",
                name=f"Tramo {i + 1}",
                line=dict(width=2.5, color=color),
                hovertemplate=f"x=%{{x:.2f}}<br>f(x)=%{{y:.2f}}<extra>Tramo {i+1}</extra>",
            ))

            # Marcar extremos del tramo (puntos abiertos/cerrados)
            for bound, sym in [(a, "circle"), (b, "circle")]:
                y_bound = float(expr.subs(x_sym, bound))
                if np.isfinite(y_bound):
                    fig.add_trace(go.Scatter(
                        x=[bound], y=[y_bound],
                        mode="markers",
                        marker=dict(size=7, color=color, line=dict(width=1.5, color="white")),
                        showlegend=False,
                        hoverinfo="skip",
                    ))
        except Exception:
            continue

    fig.update_layout(
        title=dict(text=alias if show_title else "", font=dict(size=11)),
        height=height,
        margin=dict(l=30, r=10, t=30 if show_title else 5, b=30),
        showlegend=len(funcion_json) > 1,
        xaxis=dict(
            title="x", zeroline=True, zerolinecolor="rgba(255,255,255,0.3)",
            gridcolor="rgba(255,255,255,0.1)",
        ),
        yaxis=dict(
            title="f(x)", zeroline=True, zerolinecolor="rgba(255,255,255,0.3)",
            gridcolor="rgba(255,255,255,0.1)",
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA", size=10),
        legend=dict(font=dict(size=9)),
    )
    return fig


def plot_all_functions(ciudadanos: list[dict], cols: int = 3) -> list[go.Figure]:
    """Genera una figura por ciudadano."""
    return [
        plot_function(c["funcion_json"], alias=c["alias"], height=180, show_title=True)
        for c in ciudadanos
        if c.get("funcion_json")
    ]
