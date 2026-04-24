-- ══════════════════════════════════════════════════════════════
-- schema.sql — TechNova Solutions
-- Sistema de Gestión de Proyectos, Sprints y Avances
--
-- Tablas:
--   1. usuarios      → Registro y login de usuarios
--   2. proyectos     → Proyectos de la empresa
--   3. sprints       → Sprints de cada proyecto
--   4. avances       → Registro de avances en sprints
-- ══════════════════════════════════════════════════════════════


-- ── Crear la base de datos ──
CREATE DATABASE IF NOT EXISTS technova
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_spanish_ci;

USE technova;


-- ════════════════════════════════════════════
-- TABLA: usuarios
-- Almacena los datos de los usuarios registrados
-- ════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS usuarios (

  -- id: identificador único autoincremental
  -- INT: número entero
  -- AUTO_INCREMENT: MySQL asigna el siguiente número disponible
  -- PRIMARY KEY: identifica de forma única cada usuario
  id INT AUTO_INCREMENT PRIMARY KEY,

  -- nombre: nombre completo del usuario
  -- VARCHAR(100): texto de hasta 100 caracteres
  -- NOT NULL: el campo es obligatorio
  nombre VARCHAR(100) NOT NULL,

  -- correo: correo electrónico del usuario
  -- VARCHAR(120): texto de hasta 120 caracteres
  -- UNIQUE: no permite dos usuarios con el mismo correo
  -- NOT NULL: el campo es obligatorio
  correo VARCHAR(120) NOT NULL UNIQUE,

  -- password: contraseña encriptada (con bcrypt en producción)
  -- VARCHAR(255): texto de hasta 255 caracteres (para hash)
  -- NOT NULL: el campo es obligatorio
  password VARCHAR(255) NOT NULL,

  -- rol: cargo del usuario en la empresa
  -- VARCHAR(50): texto de hasta 50 caracteres
  -- Valores posibles: Manager, Developer, Designer, QA, Admin
  rol VARCHAR(50) NOT NULL DEFAULT 'Developer',

  -- activo: indica si la cuenta está habilitada (1) o deshabilitada (0)
  -- TINYINT(1): se usa como booleano en MySQL (0 = false, 1 = true)
  -- NOT NULL: el campo es obligatorio
  -- DEFAULT 1: nuevo usuario está activo por defecto
  activo TINYINT(1) NOT NULL DEFAULT 1,

  -- creado_en: fecha y hora de creación del registro
  -- TIMESTAMP: almacena fecha y hora en formato YYYY-MM-DD HH:MM:SS
  -- DEFAULT CURRENT_TIMESTAMP: MySQL asigna automáticamente la fecha actual
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP

) ENGINE=InnoDB;
-- ENGINE=InnoDB: motor de almacenamiento con soporte de transacciones


-- ════════════════════════════════════════════
-- TABLA: proyectos
-- Almacena los proyectos de TechNova Solutions
-- ════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS proyectos (

  id INT AUTO_INCREMENT PRIMARY KEY,

  -- nombre: nombre del proyecto
  -- VARCHAR(150): texto de hasta 150 caracteres
  nombre VARCHAR(150) NOT NULL,

  -- descripcion: descripción detallada del proyecto
  -- TEXT: texto largo sin límite fijo (hasta 65,535 caracteres)
  -- Opcional: puede ser NULL
  descripcion TEXT,

  -- estado: estado actual del proyecto
  -- ENUM: solo acepta uno de los valores listados
  -- Valores: activo, pausado, completado, cancelado
  estado ENUM('activo','pausado','completado','cancelado') NOT NULL DEFAULT 'activo',

  -- fecha_inicio: fecha de inicio del proyecto
  -- DATE: almacena solo la fecha (YYYY-MM-DD)
  -- NOT NULL: el campo es obligatorio
  fecha_inicio DATE NOT NULL,

  -- fecha_fin_estimada: fecha estimada de finalización
  -- DATE: almacena solo la fecha
  -- Opcional: puede ser NULL si aún no se estima
  fecha_fin_estimada DATE,

  -- responsable_id: referencia al usuario que lidera el proyecto
  -- INT: número entero (id del usuario)
  -- NOT NULL: el campo es obligatorio
  responsable_id INT NOT NULL,

  -- creado_en: fecha y hora de creación del registro
  -- TIMESTAMP: automática
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- actualizado_en: se actualiza automáticamente en cada cambio
  -- ON UPDATE CURRENT_TIMESTAMP: Flask/MySQL actualiza este campo
  actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP,

  -- FOREIGN KEY: enlaza responsable_id con usuarios.id
  -- ON DELETE RESTRICT: no permite eliminar usuario mientras tenga proyectos
  CONSTRAINT fk_proyecto_usuario
    FOREIGN KEY (responsable_id) REFERENCES usuarios(id) ON DELETE RESTRICT

) ENGINE=InnoDB;


-- ════════════════════════════════════════════
-- TABLA: sprints
-- Almacena los sprints de cada proyecto
-- ════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS sprints (

  id INT AUTO_INCREMENT PRIMARY KEY,

  -- proyecto_id: referencia al proyecto al que pertenece el sprint
  -- INT: número entero (id del proyecto)
  -- NOT NULL: el campo es obligatorio
  proyecto_id INT NOT NULL,

  -- numero: número del sprint (1, 2, 3, etc.)
  -- TINYINT: entero pequeño (rango 0-255)
  -- NOT NULL: el campo es obligatorio
  numero TINYINT NOT NULL,

  -- nombre: nombre del sprint
  -- VARCHAR(100): texto de hasta 100 caracteres
  -- Ejemplo: "Sprint 1 - Autenticación", "Sprint 2 - Dashboard"
  nombre VARCHAR(100) NOT NULL,

  -- descripcion: descripción de objetivos del sprint
  -- TEXT: texto largo opcional
  descripcion TEXT,

  -- estado: estado del sprint
  -- ENUM: planificado, en_progreso, completado
  estado ENUM('planificado','en_progreso','completado') NOT NULL DEFAULT 'planificado',

  -- fecha_inicio: fecha de inicio del sprint
  -- DATE: almacena solo la fecha
  fecha_inicio DATE NOT NULL,

  -- fecha_fin: fecha de finalización del sprint
  -- DATE: almacena solo la fecha
  fecha_fin DATE NOT NULL,

  -- objetivo_completado: porcentaje de avance (0-100)
  -- TINYINT UNSIGNED: número de 0 a 255 (aquí usamos 0-100)
  -- NOT NULL: el campo es obligatorio
  -- DEFAULT 0: inicia en 0%
  objetivo_completado TINYINT UNSIGNED NOT NULL DEFAULT 0,

  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP,

  -- FOREIGN KEY: enlaza proyecto_id con proyectos.id
  -- ON DELETE CASCADE: si se elimina el proyecto, se eliminan sus sprints
  CONSTRAINT fk_sprint_proyecto
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE

) ENGINE=InnoDB;


-- ════════════════════════════════════════════
-- TABLA: avances
-- Registra los avances en cada sprint
-- ════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS avances (

  id INT AUTO_INCREMENT PRIMARY KEY,

  -- sprint_id: referencia al sprint al que pertenece el avance
  -- INT: número entero (id del sprint)
  -- NOT NULL: el campo es obligatorio
  sprint_id INT NOT NULL,

  -- usuario_id: referencia al usuario que registra el avance
  -- INT: número entero (id del usuario)
  -- NOT NULL: el campo es obligatorio
  usuario_id INT NOT NULL,

  -- descripcion: descripción detallada del avance realizado
  -- TEXT: texto largo sin límite fijo
  -- Ejemplo: "Implementadas funciones de autenticación", "Corregido bug en login"
  descripcion TEXT NOT NULL,

  -- tipo_avance: clasificación del tipo de trabajo realizado
  -- ENUM: caracteristica, bugfix, mejora, documentacion, testing
  tipo_avance ENUM('caracteristica','bugfix','mejora','documentacion','testing') NOT NULL DEFAULT 'caracteristica',

  -- horas_trabajadas: horas invertidas en este avance
  -- DECIMAL(5,2): número decimal con 5 dígitos y 2 decimales
  -- Ejemplo: 7.50 (7 horas 30 minutos)
  horas_trabajadas DECIMAL(5,2),

  -- estado_tarea: estado de la tarea relacionada al avance
  -- ENUM: pendiente, en_progreso, completada
  estado_tarea ENUM('pendiente','en_progreso','completada') NOT NULL DEFAULT 'completada',

  -- fecha_reporte: fecha en que se registra el avance
  -- DATE: almacena solo la fecha
  -- DEFAULT CURDATE(): la fecha actual
  fecha_reporte DATE NOT NULL DEFAULT CURDATE(),

  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP,

  -- FOREIGN KEY para sprint_id
  -- ON DELETE CASCADE: si se elimina el sprint, se eliminan sus avances
  CONSTRAINT fk_avance_sprint
    FOREIGN KEY (sprint_id) REFERENCES sprints(id) ON DELETE CASCADE,

  -- FOREIGN KEY para usuario_id
  -- ON DELETE RESTRICT: no permite eliminar usuario mientras tenga avances
  CONSTRAINT fk_avance_usuario
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT

) ENGINE=InnoDB;


-- ════════════════════════════════════════════
-- ÍNDICES PARA OPTIMIZACIÓN
-- Mejoran la velocidad de consultas frecuentes
-- ════════════════════════════════════════════

-- Índice para búsquedas por correo (login)
CREATE UNIQUE INDEX idx_usuarios_correo ON usuarios(correo);

-- Índice para proyectos de un usuario responsable
CREATE INDEX idx_proyectos_responsable ON proyectos(responsable_id);

-- Índice para sprints de un proyecto
CREATE INDEX idx_sprints_proyecto ON sprints(proyecto_id);

-- Índice para avances de un sprint
CREATE INDEX idx_avances_sprint ON avances(sprint_id);

-- Índice para avances de un usuario
CREATE INDEX idx_avances_usuario ON avances(usuario_id);


-- ════════════════════════════════════════════
-- DATOS INICIALES
-- ════════════════════════════════════════════

-- Insertar usuarios de ejemplo
INSERT INTO usuarios (nombre, correo, password, rol) VALUES
  ('Osvaldo Ramírez', 'orami@technova.cr', '017240', 'Manager'),
  ('María González', 'maria@technova.cr', '123456', 'Developer'),
  ('Carlos López', 'carlos@technova.cr', '123456', 'Developer'),
  ('Ana Rodríguez', 'ana@technova.cr', '123456', 'Designer');

-- Insertar proyectos de ejemplo
INSERT INTO proyectos (nombre, descripcion, estado, fecha_inicio, fecha_fin_estimada, responsable_id) VALUES
  ('Portal Web TechNova', 'Desarrollo del sitio web corporativo', 'activo', '2026-01-15', '2026-06-30', 1),
  ('App Móvil Ventas', 'Aplicación móvil para gestión de ventas', 'activo', '2026-02-01', '2026-07-31', 1),
  ('Sistema ERP', 'Sistema de planificación de recursos empresariales', 'pausado', '2026-03-01', '2026-12-31', 1);

-- Insertar sprints de ejemplo
INSERT INTO sprints (proyecto_id, numero, nombre, descripcion, estado, fecha_inicio, fecha_fin, objetivo_completado) VALUES
  (1, 1, 'Sprint 1 - Estructura Base', 'Desarrollo de la estructura HTML y CSS del sitio', 'completado', '2026-01-15', '2026-01-29', 100),
  (1, 2, 'Sprint 2 - Autenticación', 'Sistema de login y registro de usuarios', 'en_progreso', '2026-01-30', '2026-02-12', 75),
  (2, 1, 'Sprint 1 - Diseño UI', 'Diseño de interfaz gráfica de la aplicación', 'en_progreso', '2026-02-01', '2026-02-15', 60),
  (3, 1, 'Sprint 1 - Planificación', 'Análisis de requisitos y especificaciones', 'planificado', '2026-03-01', '2026-03-15', 0);

-- Insertar avances de ejemplo
INSERT INTO avances (sprint_id, usuario_id, descripcion, tipo_avance, horas_trabajadas, estado_tarea, fecha_reporte) VALUES
  (1, 2, 'Creada estructura HTML5 del sitio web', 'caracteristica', 8.50, 'completada', '2026-01-15'),
  (1, 3, 'Implementado sistema de estilos CSS responsivo', 'caracteristica', 12.00, 'completada', '2026-01-18'),
  (2, 2, 'Desarrollado formulario de login con validaciones', 'caracteristica', 10.50, 'en_progreso', '2026-02-01'),
  (2, 3, 'Corregidos bugs en validación de email', 'bugfix', 3.00, 'completada', '2026-02-02'),
  (3, 4, 'Diseñadas pantallas principales de la app', 'caracteristica', 15.00, 'en_progreso', '2026-02-03');


-- ════════════════════════════════════════════
-- CONSULTAS DE VERIFICACIÓN
-- ════════════════════════════════════════════

-- Ver usuarios creados
SELECT 'Usuarios creados:' AS resultado;
SELECT id, nombre, correo, rol FROM usuarios;

-- Ver proyectos
SELECT '' AS '';
SELECT 'Proyectos registrados:' AS resultado;
SELECT id, nombre, estado, fecha_inicio FROM proyectos;

-- Ver sprints
SELECT '' AS '';
SELECT 'Sprints creados:' AS resultado;
SELECT id, proyecto_id, numero, nombre, estado, objetivo_completado FROM sprints;

-- Ver avances
SELECT '' AS '';
SELECT 'Avances registrados:' AS resultado;
SELECT id, sprint_id, usuario_id, tipo_avance, horas_trabajadas FROM avances;
