# EKKLESIA — La Riqueza de las Funciones

Aplicación web interactiva para un juego de rol matemático-político dirigido a 25-30 alumnos de matemáticas. Cada alumno es un **ciudadano de Funcionalia** representado por una función a trozos única, y participa en un sistema democrático donde se aprueban leyes que redistribuyen "bloques" según las propiedades matemáticas de su función.

**Objetivo pedagógico:** funciones a trozos, propiedades (continuidad, asíntotas, monotonía, acotación, etc.), números primos como identificadores únicos, sistemas electorales.

**Producción:** [ekklesia.streamlit.app](https://ekklesia.streamlit.app/) | **Repo:** [josem404/EKKLESIA](https://github.com/josem404/EKKLESIA) (GNU GPL v3)

---

## Roles del juego

| Rol | Descripción | Página |
|-----|-------------|--------|
| *(sin login)* | Página de Apodos: descubrir la propia función por biografía | `pages/0_Apodos.py` |
| **Rey** (Profesor) | Vista maestra del oráculo. Puede activar "Intervención" para acceder a cualquier otra página. | `pages/1_rey.py` |
| **Gobierno** | Nacionaliza propiedades, crea colectivos y asociaciones nacionales, revisa funciones. | `pages/2_gobierno.py` |
| **Magnitudia / Intervalia / Brevitas** | Provincias. Empadronan ciudadanos y registran propiedades, colectivos y asociaciones. | `pages/3-5_*.py` |
| **Poder Judicial** | Valida asociaciones propuestas y ofrece un verificador de IDs racionales. | `pages/6_poder_judicial.py` |
| **Congreso** | Vota leyes *(pendiente, Sprint 3)*. | — |

El Rey **solo** accede a otras páginas cuando tiene la casilla "Intervención" activada en su propia pantalla.

---

## Conceptos clave

- **Ciudadano**: cada alumno. Tiene un **alias** = nombre de mujer científica + fₙ (ej. `"Hipatía de Alejandría — f₁"`). El **apodo** narrativo (`"La Maestra de Alejandría"`) solo aparece en la página de Apodos para el juego de descubrimiento.
- **Propiedad**: característica matemática (ej. "continua en 0"). Pertenece a una provincia `[MAG]`, `[INT]`, `[BRE]` o es nacional `[NAC]`. Primo asignado único.
- **Oráculo**: `ciudadanos.json["propiedades"]` = verdad absoluta. Solo lo ve el Rey.
- **Registros**: lo que cada provincia ha *descubierto*. Viven en `data/registros.json`.
- **Colectivo**: grupo con lógica AND sobre propiedades. Miembros calculados dinámicamente desde registros descubiertos.
- **Asociación**: grupo donde cada ciudadano queda **unívocamente identificado** por ID racional. Los alumnos lo calculan a mano; el sistema valida. Al aprobar → escribe registros automáticamente.
- **Empadronamiento**: cada sesión, la provincia registra qué ciudadanos están presentes. Solo los empadronados aparecen en las tabs de trabajo (Propiedades, Colectivos, Asociaciones).

---

## Stack

- **Frontend/Backend:** Python + Streamlit (multipage)
- **BD producción:** Supabase (PostgreSQL + Realtime)
- **BD desarrollo:** JSON planos en `data/` (fallback automático)
- **Motor matemático:** SymPy
- **Gráficas:** Plotly

---

## Estructura de archivos

```
ekklesia/
├── main.py                     # Login glassmorphism + router de roles
├── EKKLESIA.md                 # Este documento
├── requirements.txt
├── .streamlit/config.toml      # Tema pastel naranja/marrón/beige
├── assets/
│   ├── congreso_imagen.png     # Fondo de main.py (también en Streamlit Cloud)
│   └── portraits/              # Icons_01.png … Icons_40.png (copia para Cloud)
│
├── core/
│   ├── auth.py                 # ROLES, contraseñas, guards (requiere_rol)
│   ├── db.py                   # CRUD Supabase + fallback JSON
│   │                           # validar_asociacion() escribe registros al aprobar
│   ├── theme.py                # Paleta, CSS global, retratos,
│   │                           # aplicar_fondo_main(), header_rol(), ICONOS, COLORES
│   ├── provincia_ui.py         # render_provincia() — UI compartida de las 3 provincias
│   │                           # Empadronamiento → filtra tabs de trabajo a solo empadronados
│   ├── components.py           # Tablas con retratos, grid de gráficas
│   ├── grapher.py              # Plotly + formatear_definicion_latex()
│   ├── math_engine.py          # Evaluador SymPy
│   └── prime_ids.py            # IDs racionales + validar_fraccion_miembro()
│
├── pages/
│   ├── 0_Apodos.py             # Sin login: 30 biografías + revelar función al acertar
│   ├── 1_rey.py                # 6 tabs: Estado, Gráficas, Matriz, Colectivos, Asociaciones, Nueva prop.
│   ├── 2_gobierno.py           # 5 tabs: Ciudadanía, Propiedades, Registros, Colectivos, Asociaciones
│   ├── 3_Magnitudia.py         # render_provincia("magnitudia")
│   ├── 4_Intervalia.py         # render_provincia("intervalia")
│   ├── 5_Brevitas.py           # render_provincia("brevitas")
│   └── 6_poder_judicial.py     # Validar asociaciones + verificador de IDs
│
├── data/
│   ├── ciudadanos.json         # 30 ciudadanos: alias = "Nombre Mujer — fₙ", nombre_real, portrait
│   ├── apodos.json             # 30 entradas biográficas para la página Apodos
│   ├── propiedades.json        # 10 propiedades con primo asignado
│   ├── colectivos.json         # Colectivos activos (mid-game)
│   ├── asociaciones.json       # Asociaciones (1 aprobada + 1 pendiente, mid-game)
│   ├── registros.json          # Registros descubiertos por las provincias
│   └── nombres.json
│
└── sql/schema.sql

# Fuera de ekklesia/ (en MASTER FORMACIÓN/):
Iconos e imagenes/
├── congreso_imagen.png         # Original local
└── Portraits/                  # Icons_01.png … Icons_40.png (original local)
```

---

## Cómo ejecutar

```bash
cd "c:/Users/newsy/LGgram GDrive sync/Maths Obsidian/MASTER FORMACIÓN/ekklesia"
pip install streamlit sympy pandas plotly
streamlit run main.py
```

---

## Contraseñas por defecto (desarrollo)

| Rol | Contraseña |
|-----|-----------|
| rey | `rey2024` |
| gobierno | `gobierno2024` |
| magnitudia | `magna2024` |
| intervalia | `inter2024` |
| brevitas | `brevi2024` |
| poder_judicial | `judicial2024` |
| congreso | `congreso2024` |

En producción, sobrescribe con `.streamlit/secrets.toml` (configurar en Streamlit Cloud → Settings → Secrets).

---

## Página de Apodos (`0_Apodos.py`)

Accesible **sin login**. Dinámica de juego inicial:

1. El alumno lee su biografía numerada (30 en total, 6 grupos temáticos).
2. Escribe en el buscador parte del nombre de la mujer que cree que es su apodo.
3. El buscador filtra por **coincidencia de palabra completa** (normaliza tildes y mayúsculas).
4. Cuando selecciona el nombre Y el número de biografía correctos → se revela la gráfica y definición de su función.
5. La lista incluye **15 señuelos** (mujeres científicas sin función asignada) para que no sea trivial.

**Grupos temáticos de las 30 mujeres:**

- Arquitectas de la Lógica y el Cálculo (Hipatía → Gladys West, c-mag-01…15)
- Pioneras del Derecho y la Democracia (Frances Northcutt → Pilar Bayer, c-int-01…10)
- Inventoras e Inconformistas (Ángela Ruiz Robles → Mary Somerville, c-bre-01…05)

---

## Mecánica de empadronamiento

Al inicio de cada sesión, la provincia empadrona a los alumnos presentes desde la pestaña **Padrón**:

- El selectbox muestra todos los ciudadanos de la provincia; filtrable al escribir.
- Solo los empadronados aparecen en las tabs de Propiedades, Colectivos y Asociaciones.
- **"Empadronar todos/as (modo demo)"** registra a todos para pruebas.
- El empadronamiento es **por sesión** (session_state); se pierde al recargar.

---

## Convenciones de código

- **Alias de ciudadanos:** `"Nombre Real — fₙ"` — nombre de la mujer científica + subíndice numérico.
- **Apodo narrativo:** solo en `apodos.json` y en la página `0_Apodos.py`.
- **Campo `portrait`** en `ciudadanos.json`: nombre de archivo (ej. `"Icons_01.png"`).
- **Resolución de assets:** `_resolve_asset(nombre)` en `theme.py` busca: `ekklesia/assets/<nombre>` → ruta absoluta → relativa a `ekklesia/` → `Iconos e imagenes/<nombre>`.
- **Retratos:** `_portraits_dir()` prueba `ekklesia/assets/portraits/` primero (Streamlit Cloud), luego `MASTER FORMACIÓN/Iconos e imagenes/Portraits/`.
- **Session state** en `provincia_ui.py` prefijado `{provincia}_` para evitar colisiones en modo intervención del Rey.
- **Glassmorphism:** solo en `main.py` vía `aplicar_fondo_main()`. CSS aplica glass a `.ekk-glass` y a `[data-testid="stForm"]`.
- **Modo oscuro:** código presente pero toggle desactivado (funciona mal con Streamlit native widgets). Fácilmente reactivable en `theme.py`.
- **Selectboxes de ciudadano:** usan `index=None` + `placeholder=...` para que el texto de ayuda sea genuino (no opción seleccionable).

---

## Estado del juego (datos mid-game simulados)

- **Registros:** ~21 entradas — Magnitudia registrada manualmente + 7 de la asociación aprobada.
- **Colectivos:** 6 activos (2 nacionales del Rey, 4 provinciales; 1 de Intervalia vacío — caso didáctico).
- **Asociaciones:** "Asociación de la Continuidad" de Magnitudia (aprobada, 4 miembros) + "Asociación del Intervalo" de Intervalia (pendiente, 5 miembros).

---

## Hoja de ruta

- **Sprint 3 (siguiente):** `pages/7_congreso.py`, propuesta y votación de leyes, aplicación de deltas a bloques, penalización COLECTIVO COMPLETO.
- **Sprint 4:** sistema electoral D'Hondt, partidos, senadores.
- **Sprint 5:** Supabase Realtime, QR por ciudadano, pantalla pública proyectable.
