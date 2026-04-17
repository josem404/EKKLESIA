# EKKLESIA — La Riqueza de las Funciones

Aplicación web interactiva para un juego de rol matemático-político dirigido a 25-30 alumnos de matemáticas. Cada alumno es un **ciudadano de Funcionalia** representado por una función a trozos única, y participa en un sistema democrático donde se aprueban leyes que redistribuyen "bloques" según las propiedades matemáticas de su función.

**Objetivo pedagógico:** funciones a trozos, propiedades (continuidad, asíntotas, monotonía, acotación, etc.), números primos como identificadores únicos, sistemas electorales.

---

## Roles del juego

| Rol | Descripción | Página |
|-----|-------------|--------|
| **Rey** (Profesor) | Vista maestra del oráculo. Puede activar "Intervención" para acceder a cualquier otra página. | `pages/1_rey.py` |
| **Gobierno** | Nacionaliza propiedades, crea colectivos y asociaciones nacionales, revisa funciones. | `pages/2_gobierno.py` |
| **Magnitudia / Intervalia / Brevitas** | Provincias. Registran ciudadanos en sus propiedades, crean colectivos y asociaciones provinciales. | `pages/3-5_*.py` |
| **Poder Judicial** | Valida asociaciones propuestas y ofrece un verificador de IDs racionales. | `pages/6_poder_judicial.py` |
| **Congreso** | Vota leyes *(pendiente, Sprint 3)*. | — |

El Rey **solo** accede a otras páginas cuando tiene la casilla "Intervención" activada en su propia pantalla.

---

## Conceptos clave

- **Propiedad**: característica matemática de una función (ej. "continua en 0", "asíntota horizontal"). Pertenece a una provincia `[MAG]`, `[INT]`, `[BRE]` o es nacional `[NAC]`. El Gobierno puede nacionalizar una propiedad provincial.
- **Primo asignado**: cada propiedad tiene un número primo único, usado para calcular IDs racionales.
- **Oráculo**: el campo `propiedades` en `data/ciudadanos.json` es la verdad absoluta. Solo lo ve el Rey.
- **Registros**: lo que cada provincia ha *descubierto*. Viven en `data/registros.json`. Una provincia sabe de una propiedad de un ciudadano solo si ha hecho un registro explícito o si se ha validado una asociación que la incluya.
- **Colectivo**: grupo de ciudadanos que satisfacen TODAS las propiedades de un conjunto (lógica AND). Los miembros se calculan dinámicamente. El botón *COLECTIVO COMPLETO* verifica contra el oráculo.
- **Asociación**: grupo donde cada ciudadano queda **unívocamente identificado**. ID = numerador (primos de props que satisface) / denominador (primos que no satisface). Los alumnos calculan su ID a mano; el sistema lo valida. Al aprobar → escribe registros automáticamente.

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
├── main.py                     # Login con glassmorphism + router de roles
├── EKKLESIA.md                 # Este documento
├── requirements.txt
├── .streamlit/config.toml      # Tema pastel naranja/marrón/beige
│
├── core/
│   ├── auth.py                 # ROLES, contraseñas, guards (requiere_rol)
│   ├── db.py                   # CRUD Supabase + fallback JSON
│   │                           # validar_asociacion() escribe registros al aprobar
│   ├── theme.py                # Paleta, CSS global, dark mode, retratos,
│   │                           # aplicar_fondo_main(), header_rol(), banner_imagen()
│   ├── provincia_ui.py         # render_provincia() — UI compartida de las 3 provincias
│   ├── components.py           # Tablas con retratos, grid de gráficas
│   ├── grapher.py              # Plotly + notación LaTeX de condiciones
│   ├── math_engine.py          # Evaluador SymPy
│   └── prime_ids.py            # IDs racionales + validar_fraccion_miembro()
│
├── pages/
│   ├── 1_rey.py                # 6 tabs: Estado, Gráficas, Matriz (oráculo+registros),
│   │                           # Colectivos, Asociaciones, Nueva propiedad
│   ├── 2_gobierno.py           # 5 tabs: Propiedades, Colectivos, Asociaciones,
│   │                           # Funciones, Registros
│   ├── 3_Magnitudia.py         # render_provincia("magnitudia")
│   ├── 4_Intervalia.py         # render_provincia("intervalia")
│   ├── 5_Brevitas.py           # render_provincia("brevitas")
│   └── 6_poder_judicial.py     # Validar asociaciones + verificador de IDs
│
├── data/
│   ├── ciudadanos.json         # 30 ciudadanos (oráculo + portrait + alias abreviados)
│   ├── propiedades.json        # 10 propiedades con primo asignado
│   ├── colectivos.json         # 6 colectivos (2 nac. + 4 provinciales, con miembros)
│   ├── asociaciones.json       # 2 asociaciones: Magnitudia aprobada, Intervalia pendiente
│   ├── registros.json          # 21 registros descubiertos por las provincias
│   └── nombres.json
│
└── sql/schema.sql

# Fuera de ekklesia/ (en MASTER FORMACIÓN/):
Iconos e imagenes/
├── congreso_imagen.png         # Fondo de la pantalla de login/main
└── Portraits/                  # Icons_01.png … Icons_40.png (retratos pixelart)
```

---

## Cómo ejecutar

```bash
cd "ruta/a/MASTER FORMACIÓN/ekklesia"
pip install -r requirements.txt
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

En producción, sobrescribe con `.streamlit/secrets.toml`.

---

## Estado actual del juego (mid-game simulado)

Los datos reflejan una partida a mitad del juego:

- **Registros:** 21 entradas — varias provincias han registrado manualmente propiedades de ciudadanos de Magnitudia; 7 provienen de la asociación aprobada.
- **Colectivos activos:** 6 en total. Dos nacionales (del Rey), tres provinciales con miembros. Uno de Intervalia vacío (ningún ciudadano cumple `definida_en_0` AND `asintota_vertical` simultáneamente — caso didáctico).
- **Asociaciones:** Magnitudia envió y el Poder Judicial aprobó "Asociación de la Continuidad" (4 miembros, props `continua_en_0` × `punto_fijo`). Intervalia tiene pendiente "Asociación del Intervalo" (5 miembros, 3 props).

---

## Hoja de ruta

- **Sprint 3 (siguiente):** `pages/7_congreso.py`, propuesta y votación de leyes, aplicación de deltas a bloques, penalización por COLECTIVO COMPLETO fallido.
- **Sprint 4:** sistema electoral D'Hondt, partidos, senadores.
- **Sprint 5:** Supabase Realtime, QR por ciudadano, pantalla pública proyectable, despliegue en Streamlit Community Cloud.

---

## Convenciones de código

- **Alias de ciudadanos:** `"Nombre P. — fₙ"` — inicial de provincia (M./I./B.) y subíndice numérico.
- **Campo `portrait`** en `ciudadanos.json`: nombre de archivo en `Iconos e imagenes/Portraits/`.
- **Propiedades:** etiqueta `[NAC]` si nacionales; `[MAG]/[INT]/[BRE]` si provinciales.
- **Session state** en `provincia_ui.py` prefijado `{provincia}_` para evitar colisiones en modo intervención del Rey.
- **Rutas de assets:** `_resolve_asset(ruta)` en `theme.py` prueba: ruta absoluta → relativa a `ekklesia/` → `Iconos e imagenes/<nombre>` → `ekklesia/assets/<nombre>`.
- **Glassmorphism:** solo activo en `main.py` (vía `aplicar_fondo_main()`). El CSS aplica glass a `.ekk-glass` divs HTML y a `[data-testid="stForm"]`. No afecta otras páginas.
- **Modo oscuro:** toggle en sidebar, disponible en todas las páginas. Los widgets nativos de Streamlit no se ven afectados (limitación del enfoque CSS).
