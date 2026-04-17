-- ============================================================
-- EKKLESIA — Esquema de Base de Datos (Supabase/PostgreSQL)
-- Ejecutar en el SQL Editor de Supabase
-- ============================================================

-- Sesión de juego activa
CREATE TABLE IF NOT EXISTS sesiones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL DEFAULT 'Sesión 1',
    activa BOOLEAN DEFAULT true,
    turno INT DEFAULT 1,
    started_at TIMESTAMPTZ DEFAULT now()
);

-- Ciudadanos (una fila por alumno/función)
CREATE TABLE IF NOT EXISTS ciudadanos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sesion_id UUID REFERENCES sesiones(id) ON DELETE CASCADE,
    nombre_real TEXT,                     -- Solo visible para el Rey
    alias TEXT NOT NULL,                  -- "Ciudadana f(x) — Magnitudia #01"
    provincia TEXT NOT NULL CHECK (provincia IN ('magnitudia', 'intervalia', 'brevitas')),
    funcion_json JSONB NOT NULL,          -- [{expr: "x**2", dominio: "[0,1)", condicion: "And(x>=0, x<1)"}]
    bloques INT DEFAULT 10 CHECK (bloques >= 0),
    rol_institucional TEXT DEFAULT 'ciudadano',  -- 'ciudadano' | 'diputado' | 'senador' | 'ministro'
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Propiedades matemáticas (pre-cargadas + ad-hoc)
CREATE TABLE IF NOT EXISTS propiedades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sesion_id UUID REFERENCES sesiones(id) ON DELETE CASCADE,
    codigo TEXT NOT NULL,                 -- 'cont_0', 'creciente_01', ...
    descripcion TEXT NOT NULL,            -- "f es continua en x=0"
    descripcion_corta TEXT,               -- "Continua en 0"
    sympy_expr TEXT,                      -- Expresión SymPy para evaluación dinámica
    primo_asignado INT,                   -- 2, 3, 5, 7, 11, ... (por orden de creación)
    nivel TEXT DEFAULT 'basico' CHECK (nivel IN ('basico', 'medio', 'bachillerato')),
    es_adhoc BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (sesion_id, codigo)
);

-- Matriz ciudadano × propiedad (pre-calculada)
CREATE TABLE IF NOT EXISTS ciudadano_propiedades (
    ciudadano_id UUID REFERENCES ciudadanos(id) ON DELETE CASCADE,
    propiedad_id UUID REFERENCES propiedades(id) ON DELETE CASCADE,
    satisface BOOLEAN NOT NULL,
    calculado_en TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (ciudadano_id, propiedad_id)
);

-- Colectivos (conjuntos por propiedades comunes)
CREATE TABLE IF NOT EXISTS colectivos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sesion_id UUID REFERENCES sesiones(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    ambito TEXT NOT NULL CHECK (ambito IN ('provincial', 'nacional')),
    provincia TEXT,                       -- NULL si nacional
    propiedades UUID[] NOT NULL DEFAULT '{}',  -- Array de propiedad_id
    estado TEXT DEFAULT 'incompleto' CHECK (estado IN ('incompleto', 'completo')),
    created_by TEXT NOT NULL,             -- rol que lo creó
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Miembros de colectivos
CREATE TABLE IF NOT EXISTS colectivo_miembros (
    colectivo_id UUID REFERENCES colectivos(id) ON DELETE CASCADE,
    ciudadano_id UUID REFERENCES ciudadanos(id) ON DELETE CASCADE,
    verificado BOOLEAN DEFAULT false,
    PRIMARY KEY (colectivo_id, ciudadano_id)
);

-- Asociaciones (identificación única por primos)
CREATE TABLE IF NOT EXISTS asociaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sesion_id UUID REFERENCES sesiones(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    ambito TEXT NOT NULL CHECK (ambito IN ('provincial', 'nacional')),
    provincia TEXT,
    propiedades_ord UUID[] NOT NULL DEFAULT '{}',  -- EN ORDEN: define asignación de primos
    estado TEXT DEFAULT 'borrador' CHECK (estado IN ('borrador', 'pendiente_validacion', 'registrada', 'rechazada')),
    es_valida BOOLEAN,                    -- NULL=no evaluado, TRUE=válida, FALSE=inválida
    motivo_rechazo TEXT,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Miembros de asociaciones con su ID racional
CREATE TABLE IF NOT EXISTS asociacion_miembros (
    asociacion_id UUID REFERENCES asociaciones(id) ON DELETE CASCADE,
    ciudadano_id UUID REFERENCES ciudadanos(id) ON DELETE CASCADE,
    id_numerador BIGINT,                  -- Producto de primos satisfechos
    id_denominador BIGINT,               -- Producto de primos no satisfechos
    id_racional TEXT,                     -- "6/5"
    id_decimal FLOAT,                     -- 1.2
    PRIMARY KEY (asociacion_id, ciudadano_id)
);

-- Leyes propuestas y aprobadas
CREATE TABLE IF NOT EXISTS leyes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sesion_id UUID REFERENCES sesiones(id) ON DELETE CASCADE,
    titulo TEXT NOT NULL,
    tipo TEXT DEFAULT 'ordinaria' CHECK (tipo IN ('ordinaria', 'organica', 'decreto', 'reforma_constitucional')),
    estado TEXT DEFAULT 'propuesta' CHECK (estado IN ('propuesta', 'en_votacion', 'aprobada_congreso', 'vetada_senado', 'promulgada', 'rechazada')),
    propuesta_por TEXT NOT NULL,          -- rol o partido que propone
    paquete_json JSONB NOT NULL,          -- [{propiedad_id, delta_bloques, toma_de: 'provincia'|'comun'}]
    votos_favor INT DEFAULT 0,
    votos_contra INT DEFAULT 0,
    votos_abstencion INT DEFAULT 0,
    suma_neta INT DEFAULT 0,              -- debe ser 0 para ordinarias
    turno INT,                            -- turno en que se votó
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Registro de movimientos de bloques (auditoría)
CREATE TABLE IF NOT EXISTS movimientos_bloques (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sesion_id UUID REFERENCES sesiones(id) ON DELETE CASCADE,
    ley_id UUID REFERENCES leyes(id),
    ciudadano_id UUID REFERENCES ciudadanos(id) ON DELETE CASCADE,
    delta INT NOT NULL,                   -- positivo = gana, negativo = pierde
    bloques_antes INT NOT NULL,
    bloques_despues INT NOT NULL,
    motivo TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- ÍNDICES para rendimiento
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_ciudadanos_sesion ON ciudadanos(sesion_id);
CREATE INDEX IF NOT EXISTS idx_ciudadanos_provincia ON ciudadanos(provincia);
CREATE INDEX IF NOT EXISTS idx_cp_ciudadano ON ciudadano_propiedades(ciudadano_id);
CREATE INDEX IF NOT EXISTS idx_cp_propiedad ON ciudadano_propiedades(propiedad_id);
CREATE INDEX IF NOT EXISTS idx_leyes_sesion ON leyes(sesion_id);
CREATE INDEX IF NOT EXISTS idx_leyes_estado ON leyes(estado);

-- ============================================================
-- ROW LEVEL SECURITY (opcional, para producción)
-- Por ahora deshabilitado para simplificar el prototipo
-- ============================================================
-- ALTER TABLE ciudadanos ENABLE ROW LEVEL SECURITY;
-- (configurar policies según roles cuando esté listo)

-- ============================================================
-- FUNCIÓN AUXILIAR: siguiente primo
-- ============================================================
CREATE OR REPLACE FUNCTION siguiente_primo_disponible(sesion UUID)
RETURNS INT AS $$
DECLARE
    ultimo INT;
    candidato INT;
    es_primo BOOLEAN;
    divisor INT;
BEGIN
    SELECT COALESCE(MAX(primo_asignado), 1) INTO ultimo FROM propiedades WHERE sesion_id = sesion;
    candidato := ultimo + 1;
    LOOP
        es_primo := true;
        divisor := 2;
        WHILE divisor * divisor <= candidato LOOP
            IF candidato % divisor = 0 THEN
                es_primo := false;
                EXIT;
            END IF;
            divisor := divisor + 1;
        END LOOP;
        IF es_primo AND candidato > 1 THEN
            RETURN candidato;
        END IF;
        candidato := candidato + 1;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
