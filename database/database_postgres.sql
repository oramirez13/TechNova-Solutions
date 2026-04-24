-- =============================================================
--  TechNova Solutions – Schema PostgreSQL (Render)
--  Adaptado desde database/schema.sql (MySQL 8.x)
-- =============================================================

-- ----------------------------------------------------------------
-- Tabla: usuarios
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id          SERIAL          PRIMARY KEY,
    nombre      VARCHAR(100)    NOT NULL,
    correo      VARCHAR(120)    NOT NULL UNIQUE,
    password    VARCHAR(255)    NOT NULL,
    -- MySQL ENUM → CHECK en PostgreSQL
    rol         VARCHAR(50)     NOT NULL DEFAULT 'Developer'
                    CHECK (rol IN ('Manager','Developer','Designer','QA','Admin')),
    -- MySQL TINYINT(1) → BOOLEAN en PostgreSQL
    activo      BOOLEAN         NOT NULL DEFAULT TRUE,
    creado_en   TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_correo ON usuarios (correo);


-- ----------------------------------------------------------------
-- Tabla: proyectos
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS proyectos (
    id                  SERIAL          PRIMARY KEY,
    nombre              VARCHAR(150)    NOT NULL,
    descripcion         TEXT,
    estado              VARCHAR(20)     NOT NULL DEFAULT 'activo'
                            CHECK (estado IN ('activo','pausado','completado','cancelado')),
    fecha_inicio        DATE            NOT NULL,
    fecha_fin_estimada  DATE,
    responsable_id      INTEGER         NOT NULL
                            REFERENCES usuarios (id) ON DELETE RESTRICT,
    creado_en           TIMESTAMP       NOT NULL DEFAULT NOW(),
    -- ON UPDATE equivale a un trigger en PostgreSQL;
    -- se inicializa igual que creado_en y se actualiza vía trigger abajo
    actualizado_en      TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_proyectos_responsable ON proyectos (responsable_id);

-- Trigger para actualizar actualizado_en automáticamente
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_proyectos_updated_at ON proyectos;
CREATE TRIGGER trg_proyectos_updated_at
    BEFORE UPDATE ON proyectos
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();


-- ----------------------------------------------------------------
-- Tabla: sprints
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sprints (
    id                  SERIAL          PRIMARY KEY,
    proyecto_id         INTEGER         NOT NULL
                            REFERENCES proyectos (id) ON DELETE CASCADE,
    -- MySQL TINYINT → SMALLINT en PostgreSQL
    numero              SMALLINT        NOT NULL,
    nombre              VARCHAR(100)    NOT NULL,
    descripcion         TEXT,
    estado              VARCHAR(20)     NOT NULL DEFAULT 'planificado'
                            CHECK (estado IN ('planificado','en_progreso','completado')),
    fecha_inicio        DATE            NOT NULL,
    fecha_fin           DATE            NOT NULL,
    -- MySQL TINYINT UNSIGNED (0-100) → SMALLINT con CHECK
    objetivo_completado SMALLINT        NOT NULL DEFAULT 0
                            CHECK (objetivo_completado BETWEEN 0 AND 100),
    creado_en           TIMESTAMP       NOT NULL DEFAULT NOW(),
    actualizado_en      TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sprints_proyecto ON sprints (proyecto_id);

DROP TRIGGER IF EXISTS trg_sprints_updated_at ON sprints;
CREATE TRIGGER trg_sprints_updated_at
    BEFORE UPDATE ON sprints
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();


-- ----------------------------------------------------------------
-- Tabla: avances
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS avances (
    id               SERIAL          PRIMARY KEY,
    sprint_id        INTEGER         NOT NULL
                         REFERENCES sprints (id) ON DELETE CASCADE,
    usuario_id       INTEGER         NOT NULL
                         REFERENCES usuarios (id) ON DELETE RESTRICT,
    descripcion      TEXT            NOT NULL,
    tipo_avance      VARCHAR(20)     NOT NULL DEFAULT 'caracteristica'
                         CHECK (tipo_avance IN ('caracteristica','bugfix','mejora','documentacion','testing')),
    -- MySQL DECIMAL(5,2) → NUMERIC(5,2) en PostgreSQL
    horas_trabajadas NUMERIC(5,2),
    estado_tarea     VARCHAR(20)     NOT NULL DEFAULT 'completada'
                         CHECK (estado_tarea IN ('pendiente','en_progreso','completada')),
    -- MySQL DEFAULT CURDATE() → DEFAULT CURRENT_DATE en PostgreSQL
    fecha_reporte    DATE            NOT NULL DEFAULT CURRENT_DATE,
    creado_en        TIMESTAMP       NOT NULL DEFAULT NOW(),
    actualizado_en   TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_avances_sprint  ON avances (sprint_id);
CREATE INDEX IF NOT EXISTS idx_avances_usuario ON avances (usuario_id);

DROP TRIGGER IF EXISTS trg_avances_updated_at ON avances;
CREATE TRIGGER trg_avances_updated_at
    BEFORE UPDATE ON avances
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();


-- ----------------------------------------------------------------
-- Datos de ejemplo – usuarios
-- Nota: passwords en texto plano tal como están en el proyecto
--       original. En producción usar hashes (bcrypt, argon2, etc.)
-- ----------------------------------------------------------------
INSERT INTO usuarios (nombre, correo, password, rol) VALUES
    ('Osvaldo Ramírez', 'orami@technova.cr',  '017240', 'Manager'),
    ('María González',  'maria@technova.cr',  '123456', 'Developer'),
    ('Carlos López',    'carlos@technova.cr', '123456', 'Developer'),
    ('Ana Rodríguez',   'ana@technova.cr',    '123456', 'Designer')
ON CONFLICT (correo) DO NOTHING;


-- ----------------------------------------------------------------
-- Datos de ejemplo – proyectos
-- ----------------------------------------------------------------
INSERT INTO proyectos (nombre, descripcion, estado, fecha_inicio, fecha_fin_estimada, responsable_id) VALUES
    ('Portal Web TechNova', 'Desarrollo del sitio web corporativo',                 'activo', '2026-01-15', '2026-06-30', 1),
    ('App Móvil Ventas',    'Aplicación móvil para gestión de ventas',              'activo', '2026-02-01', '2026-07-31', 1),
    ('Sistema ERP',         'Sistema de planificación de recursos empresariales',   'pausado','2026-03-01', '2026-12-31', 1)
ON CONFLICT DO NOTHING;


-- ----------------------------------------------------------------
-- Datos de ejemplo – sprints
-- ----------------------------------------------------------------
INSERT INTO sprints (proyecto_id, numero, nombre, descripcion, estado, fecha_inicio, fecha_fin, objetivo_completado) VALUES
    (1, 1, 'Sprint 1 - Estructura Base', 'Desarrollo de la estructura HTML y CSS del sitio', 'completado',  '2026-01-15', '2026-01-29', 100),
    (1, 2, 'Sprint 2 - Autenticación',   'Sistema de login y registro de usuarios',          'en_progreso', '2026-01-30', '2026-02-12',  75),
    (2, 1, 'Sprint 1 - Diseño UI',       'Diseño de interfaz gráfica de la aplicación',      'en_progreso', '2026-02-01', '2026-02-15',  60),
    (3, 1, 'Sprint 1 - Planificación',   'Análisis de requisitos y especificaciones',         'planificado', '2026-03-01', '2026-03-15',   0)
ON CONFLICT DO NOTHING;


-- ----------------------------------------------------------------
-- Datos de ejemplo – avances
-- ----------------------------------------------------------------
INSERT INTO avances (sprint_id, usuario_id, descripcion, tipo_avance, horas_trabajadas, estado_tarea, fecha_reporte) VALUES
    (1, 2, 'Creada estructura HTML5 del sitio web',              'caracteristica',  8.50, 'completada',  '2026-01-15'),
    (1, 3, 'Implementado sistema de estilos CSS responsivo',     'caracteristica', 12.00, 'completada',  '2026-01-18'),
    (2, 2, 'Desarrollado formulario de login con validaciones',  'caracteristica', 10.50, 'en_progreso', '2026-02-01'),
    (2, 3, 'Corregidos bugs en validación de email',             'bugfix',          3.00, 'completada',  '2026-02-02'),
    (3, 4, 'Diseñadas pantallas principales de la app',          'caracteristica', 15.00, 'en_progreso', '2026-02-03')
ON CONFLICT DO NOTHING;
