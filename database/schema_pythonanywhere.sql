-- schema_pythonanywhere.sql
-- Importa este archivo directamente en la base de datos de PythonAnywhere:
-- mysql -u TU_USUARIO -h TU_HOST -p 'TU_USUARIO$technova' < database/schema_pythonanywhere.sql

CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  correo VARCHAR(120) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  rol VARCHAR(50) NOT NULL DEFAULT 'Developer',
  activo TINYINT(1) NOT NULL DEFAULT 1,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS proyectos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  descripcion TEXT,
  estado ENUM('activo','pausado','completado','cancelado') NOT NULL DEFAULT 'activo',
  fecha_inicio DATE NOT NULL,
  fecha_fin_estimada DATE,
  responsable_id INT NOT NULL,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_proyecto_usuario
    FOREIGN KEY (responsable_id) REFERENCES usuarios(id) ON DELETE RESTRICT
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS sprints (
  id INT AUTO_INCREMENT PRIMARY KEY,
  proyecto_id INT NOT NULL,
  numero TINYINT NOT NULL,
  nombre VARCHAR(100) NOT NULL,
  descripcion TEXT,
  estado ENUM('planificado','en_progreso','completado') NOT NULL DEFAULT 'planificado',
  fecha_inicio DATE NOT NULL,
  fecha_fin DATE NOT NULL,
  objetivo_completado TINYINT UNSIGNED NOT NULL DEFAULT 0,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_sprint_proyecto
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS avances (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sprint_id INT NOT NULL,
  usuario_id INT NOT NULL,
  descripcion TEXT NOT NULL,
  tipo_avance ENUM('caracteristica','bugfix','mejora','documentacion','testing') NOT NULL DEFAULT 'caracteristica',
  horas_trabajadas DECIMAL(5,2),
  estado_tarea ENUM('pendiente','en_progreso','completada') NOT NULL DEFAULT 'completada',
  fecha_reporte DATE NOT NULL DEFAULT (CURDATE()),
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_avance_sprint
    FOREIGN KEY (sprint_id) REFERENCES sprints(id) ON DELETE CASCADE,
  CONSTRAINT fk_avance_usuario
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT
) ENGINE=InnoDB;


CREATE INDEX idx_proyectos_responsable ON proyectos(responsable_id);
CREATE INDEX idx_sprints_proyecto ON sprints(proyecto_id);
CREATE INDEX idx_avances_sprint ON avances(sprint_id);
CREATE INDEX idx_avances_usuario ON avances(usuario_id);


INSERT INTO usuarios (nombre, correo, password, rol) VALUES
  ('Osvaldo Ramirez', 'orami@technova.cr', '017240', 'Manager'),
  ('Maria Gonzalez', 'maria@technova.cr', '123456', 'Developer'),
  ('Carlos Lopez', 'carlos@technova.cr', '123456', 'Developer'),
  ('Ana Rodriguez', 'ana@technova.cr', '123456', 'Designer');


INSERT INTO proyectos (nombre, descripcion, estado, fecha_inicio, fecha_fin_estimada, responsable_id) VALUES
  ('Portal Web TechNova', 'Desarrollo del sitio web corporativo', 'activo', '2026-01-15', '2026-06-30', 1),
  ('App Movil Ventas', 'Aplicacion movil para gestion de ventas', 'activo', '2026-02-01', '2026-07-31', 1),
  ('Sistema ERP', 'Sistema de planificacion de recursos empresariales', 'pausado', '2026-03-01', '2026-12-31', 1);


INSERT INTO sprints (proyecto_id, numero, nombre, descripcion, estado, fecha_inicio, fecha_fin, objetivo_completado) VALUES
  (1, 1, 'Sprint 1 - Estructura Base', 'Desarrollo de la estructura HTML y CSS del sitio', 'completado', '2026-01-15', '2026-01-29', 100),
  (1, 2, 'Sprint 2 - Autenticacion', 'Sistema de login y registro de usuarios', 'en_progreso', '2026-01-30', '2026-02-12', 75),
  (2, 1, 'Sprint 1 - Diseno UI', 'Diseno de interfaz grafica de la aplicacion', 'en_progreso', '2026-02-01', '2026-02-15', 60),
  (3, 1, 'Sprint 1 - Planificacion', 'Analisis de requisitos y especificaciones', 'planificado', '2026-03-01', '2026-03-15', 0);


INSERT INTO avances (sprint_id, usuario_id, descripcion, tipo_avance, horas_trabajadas, estado_tarea, fecha_reporte) VALUES
  (1, 2, 'Creada estructura HTML5 del sitio web', 'caracteristica', 8.50, 'completada', '2026-01-15'),
  (1, 3, 'Implementado sistema de estilos CSS responsivo', 'caracteristica', 12.00, 'completada', '2026-01-18'),
  (2, 2, 'Desarrollado formulario de login con validaciones', 'caracteristica', 10.50, 'en_progreso', '2026-02-01'),
  (2, 3, 'Corregidos bugs en validacion de email', 'bugfix', 3.00, 'completada', '2026-02-02'),
  (3, 4, 'Disenadas pantallas principales de la app', 'caracteristica', 15.00, 'en_progreso', '2026-02-03');
