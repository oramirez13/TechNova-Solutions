PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  correo TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  rol TEXT NOT NULL DEFAULT 'Developer'
      CHECK (rol IN ('Manager', 'Developer', 'Designer', 'QA', 'Admin')),
  activo INTEGER NOT NULL DEFAULT 1,
  creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS proyectos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  descripcion TEXT,
  estado TEXT NOT NULL DEFAULT 'activo'
      CHECK (estado IN ('activo', 'pausado', 'completado', 'cancelado')),
  fecha_inicio TEXT NOT NULL,
  fecha_fin_estimada TEXT,
  responsable_id INTEGER NOT NULL,
  creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (responsable_id) REFERENCES usuarios(id) ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS sprints (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proyecto_id INTEGER NOT NULL,
  numero INTEGER NOT NULL,
  nombre TEXT NOT NULL,
  descripcion TEXT,
  estado TEXT NOT NULL DEFAULT 'planificado'
      CHECK (estado IN ('planificado', 'en_progreso', 'completado')),
  fecha_inicio TEXT NOT NULL,
  fecha_fin TEXT NOT NULL,
  objetivo_completado INTEGER NOT NULL DEFAULT 0
      CHECK (objetivo_completado BETWEEN 0 AND 100),
  creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS avances (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sprint_id INTEGER NOT NULL,
  usuario_id INTEGER NOT NULL,
  descripcion TEXT NOT NULL,
  tipo_avance TEXT NOT NULL DEFAULT 'caracteristica'
      CHECK (tipo_avance IN ('caracteristica', 'bugfix', 'mejora', 'documentacion', 'testing')),
  horas_trabajadas REAL,
  estado_tarea TEXT NOT NULL DEFAULT 'completada'
      CHECK (estado_tarea IN ('pendiente', 'en_progreso', 'completada')),
  fecha_reporte TEXT NOT NULL DEFAULT CURRENT_DATE,
  creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (sprint_id) REFERENCES sprints(id) ON DELETE CASCADE,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT
);


CREATE INDEX IF NOT EXISTS idx_proyectos_responsable ON proyectos(responsable_id);
CREATE INDEX IF NOT EXISTS idx_sprints_proyecto ON sprints(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_avances_sprint ON avances(sprint_id);
CREATE INDEX IF NOT EXISTS idx_avances_usuario ON avances(usuario_id);


INSERT OR IGNORE INTO usuarios (id, nombre, correo, password, rol) VALUES
  (1, 'Osvaldo Ramirez', 'orami@technova.cr', '017240', 'Manager'),
  (2, 'Maria Gonzalez', 'maria@technova.cr', '123456', 'Developer'),
  (3, 'Carlos Lopez', 'carlos@technova.cr', '123456', 'Developer'),
  (4, 'Ana Rodriguez', 'ana@technova.cr', '123456', 'Designer');


INSERT OR IGNORE INTO proyectos (id, nombre, descripcion, estado, fecha_inicio, fecha_fin_estimada, responsable_id) VALUES
  (1, 'Portal Web TechNova', 'Desarrollo del sitio web corporativo', 'activo', '2026-01-15', '2026-06-30', 1),
  (2, 'App Movil Ventas', 'Aplicacion movil para gestion de ventas', 'activo', '2026-02-01', '2026-07-31', 1),
  (3, 'Sistema ERP', 'Sistema de planificacion de recursos empresariales', 'pausado', '2026-03-01', '2026-12-31', 1);


INSERT OR IGNORE INTO sprints (id, proyecto_id, numero, nombre, descripcion, estado, fecha_inicio, fecha_fin, objetivo_completado) VALUES
  (1, 1, '1', 'Sprint 1 - Estructura Base', 'Desarrollo de la estructura HTML y CSS del sitio', 'completado', '2026-01-15', '2026-01-29', 100),
  (2, 1, '2', 'Sprint 2 - Autenticacion', 'Sistema de login y registro de usuarios', 'en_progreso', '2026-01-30', '2026-02-12', 75),
  (3, 2, '1', 'Sprint 1 - Diseno UI', 'Diseno de interfaz grafica de la aplicacion', 'en_progreso', '2026-02-01', '2026-02-15', 60),
  (4, 3, '1', 'Sprint 1 - Planificacion', 'Analisis de requisitos y especificaciones', 'planificado', '2026-03-01', '2026-03-15', 0);


INSERT OR IGNORE INTO avances (id, sprint_id, usuario_id, descripcion, tipo_avance, horas_trabajadas, estado_tarea, fecha_reporte) VALUES
  (1, 1, 2, 'Creada estructura HTML5 del sitio web', 'caracteristica', 8.50, 'completada', '2026-01-15'),
  (2, 1, 3, 'Implementado sistema de estilos CSS responsivo', 'caracteristica', 12.00, 'completada', '2026-01-18'),
  (3, 2, 2, 'Desarrollado formulario de login con validaciones', 'caracteristica', 10.50, 'en_progreso', '2026-02-01'),
  (4, 2, 3, 'Corregidos bugs en validacion de email', 'bugfix', 3.00, 'completada', '2026-02-02'),
  (5, 3, 4, 'Disenadas pantallas principales de la app', 'caracteristica', 15.00, 'en_progreso', '2026-02-03');
