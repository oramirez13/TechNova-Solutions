$(document).ready(function () {
  var csrfToken = $('body').data('csrf-token');

  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      if (settings.type && settings.type !== 'GET' && settings.type !== 'HEAD') {
        if (settings.contentType && settings.contentType.indexOf('application/json') !== -1) {
          var body = JSON.parse(settings.data || '{}');
          body.csrf_token = csrfToken;
          settings.data = JSON.stringify(body);
        } else {
          xhr.setRequestHeader('X-CSRF-Token', csrfToken);
        }
      }
    }
  });

  var $contenedor = $('#proyectosContainer');
  var $alertas = $('#dashboardAlerts');
  var $modalProyecto = $('#modalProyecto');
  var $modalSprint = $('#modalSprint');
  var $modalTarea = $('#modalTarea');
  var $modalAvance = $('#modalAvance');
  var $formProyecto = $('#formProyecto');
  var $formSprint = $('#formSprint');
  var $formTarea = $('#formTarea');
  var $formAvance = $('#formAvance');
  var $usuarioNombre = $('#usuarioNombre');
  var $modalProyectoTitulo = $('#modalProyectoTitulo');
  var $modalSprintTitulo = $('#modalSprintTitulo');
  var $modalAvanceTitulo = $('#modalAvanceTitulo');

  var proyectos = [];
  var usuarios = [];
  var detallePorProyecto = {};
  var dragContexto = null;
  var dashboardFiltros = {
    busqueda: '',
    estado: 'todos'
  };

  var columnasKanban = [
    { key: 'pendiente', titulo: 'Pendiente' },
    { key: 'en_progreso', titulo: 'En progreso' },
    { key: 'en_revision', titulo: 'En revision' },
    { key: 'avances', titulo: 'Avances' },
    { key: 'completada', titulo: 'Completada' }
  ];

  function escaparHtml(texto) {
    return $('<div>').text(texto || '').html();
  }

  function formatearFecha(valor) {
    if (!valor) {
      return 'Sin definir';
    }

    return valor;
  }

  function textoEstadoProyecto(estado) {
    var mapa = {
      activo: 'Activo',
      pausado: 'Pausado',
      completado: 'Completado',
      cancelado: 'Cancelado'
    };

    return mapa[estado] || estado || 'Activo';
  }

  function puedeAlternarEstadoProyecto(estado) {
    return estado === 'activo' || estado === 'pausado';
  }

  function etiquetaBotonEstadoProyecto(estado) {
    if (estado === 'pausado') {
      return 'Activar';
    }

    return 'Pausar';
  }

  function siguienteEstadoProyecto(estado) {
    if (estado === 'pausado') {
      return 'activo';
    }

    return 'pausado';
  }

  function textoEstadoSprint(estado) {
    var mapa = {
      planificado: 'Planificado',
      en_progreso: 'En progreso',
      completado: 'Completado'
    };

    return mapa[estado] || estado || 'Planificado';
  }

  function textoPrioridad(prioridad) {
    var mapa = {
      baja: 'Baja',
      media: 'Media',
      alta: 'Alta'
    };

    return mapa[prioridad] || prioridad || 'Media';
  }

  function textoTipoAvance(tipo) {
    var mapa = {
      caracteristica: 'Caracteristica',
      bugfix: 'Bugfix',
      mejora: 'Mejora',
      documentacion: 'Documentacion',
      testing: 'Testing'
    };

    return mapa[tipo] || tipo || 'Caracteristica';
  }

  function textoEstadoTarea(estado) {
    var mapa = {
      pendiente: 'Pendiente',
      en_progreso: 'En progreso',
      en_revision: 'En revision',
      avances: 'Avances',
      completada: 'Completada'
    };

    return mapa[estado] || estado || 'Pendiente';
  }

  function etiquetaSprintTab(sprint) {
    var nombre = (sprint.nombre || '').trim();
    var base = 'Sprint ' + sprint.numero;

    if (!nombre) {
      return base;
    }

    return base + ' · ' + nombre;
  }

  function mostrarAlerta(tipo, mensaje) {
    var clase = tipo === 'error' ? 'alert-danger' : 'alert-success';
    var html =
      '<div class="alert ' + clase + ' alert-dismissible fade show" role="alert">' +
        escaparHtml(mensaje) +
        '<button type="button" class="close" data-dismiss="alert" aria-label="Cerrar">' +
          '<span aria-hidden="true">&times;</span>' +
        '</button>' +
      '</div>';

    $alertas.html(html);
  }

  function limpiarAlerta() {
    $alertas.empty();
  }

  function manejarErrorAjax(xhr, mensajeBase) {
    if (xhr && xhr.status === 401) {
      window.location.assign('/');
      return null;
    }

    return (xhr && xhr.responseJSON && xhr.responseJSON.mensaje) || mensajeBase;
  }

  function emitirEstadoDashboard() {
    window.dispatchEvent(
      new CustomEvent('dashboard:data-updated', {
        detail: {
          proyectos: proyectos.slice(),
          detallePorProyecto: detallePorProyecto,
          filtros: {
            busqueda: dashboardFiltros.busqueda,
            estado: dashboardFiltros.estado
          }
        }
      })
    );
  }

  function filtrarProyectos(lista) {
    var busqueda = (dashboardFiltros.busqueda || '').trim().toLowerCase();
    var estado = dashboardFiltros.estado || 'todos';

    return lista.filter(function (proyecto) {
      var coincideBusqueda = true;
      var responsable = (proyecto.responsable_nombre || '').toLowerCase();
      var descripcion = (proyecto.descripcion || '').toLowerCase();
      var nombre = (proyecto.nombre || '').toLowerCase();

      if (busqueda) {
        coincideBusqueda =
          nombre.indexOf(busqueda) !== -1 ||
          descripcion.indexOf(busqueda) !== -1 ||
          responsable.indexOf(busqueda) !== -1;
      }

      if (!coincideBusqueda) {
        return false;
      }

      if (estado !== 'todos' && proyecto.estado !== estado) {
        return false;
      }

      return true;
    });
  }

  function obtenerDetalle(proyectoId) {
    if (!detallePorProyecto[proyectoId]) {
      detallePorProyecto[proyectoId] = {
        abierto: false,
        cargando: false,
        cargado: false,
        sprintActivo: '0',
        sprints: [],
        tareas: [],
        avancesPorSprint: {}
      };
    }

    return detallePorProyecto[proyectoId];
  }

  function obtenerProyecto(proyectoId) {
    for (var i = 0; i < proyectos.length; i += 1) {
      if (String(proyectos[i].id) === String(proyectoId)) {
        return proyectos[i];
      }
    }

    return null;
  }

  function obtenerTarea(proyectoId, tareaId) {
    var detalle = obtenerDetalle(proyectoId);

    for (var i = 0; i < detalle.tareas.length; i += 1) {
      if (String(detalle.tareas[i].id) === String(tareaId)) {
        return detalle.tareas[i];
      }
    }

    return null;
  }

  function obtenerSprint(proyectoId, sprintId) {
    var detalle = obtenerDetalle(proyectoId);

    for (var i = 0; i < detalle.sprints.length; i += 1) {
      if (String(detalle.sprints[i].id) === String(sprintId)) {
        return detalle.sprints[i];
      }
    }

    return null;
  }

  function obtenerAvance(proyectoId, avanceId) {
    var detalle = obtenerDetalle(proyectoId);
    var sprintIds = Object.keys(detalle.avancesPorSprint || {});
    var i;
    var j;
    var avances;

    for (i = 0; i < sprintIds.length; i += 1) {
      avances = detalle.avancesPorSprint[sprintIds[i]] || [];

      for (j = 0; j < avances.length; j += 1) {
        if (String(avances[j].id) === String(avanceId)) {
          return avances[j];
        }
      }
    }

    return null;
  }

  function contarTareasPorEstado(tareas, estado) {
    var total = 0;

    tareas.forEach(function (tarea) {
      if (tarea.estado === estado) {
        total += 1;
      }
    });

    return total;
  }

  function obtenerSprintActivo(detalle) {
    var sprintActivo = String(detalle.sprintActivo || '0');
    var existe = detalle.sprints.some(function (sprint) {
      return String(sprint.id) === sprintActivo;
    });

    if (sprintActivo !== '0' && !existe) {
      detalle.sprintActivo = '0';
      sprintActivo = '0';
    }

    return sprintActivo;
  }

  function obtenerSprintSeleccionado(detalle) {
    var sprintActivo = obtenerSprintActivo(detalle);
    var sprintSeleccionado = null;

    if (sprintActivo === '0') {
      return null;
    }

    detalle.sprints.some(function (sprint) {
      if (String(sprint.id) === sprintActivo) {
        sprintSeleccionado = sprint;
        return true;
      }

      return false;
    });

    return sprintSeleccionado;
  }

  function obtenerTareasVisibles(detalle) {
    var sprintSeleccionado = obtenerSprintSeleccionado(detalle);

    if (!sprintSeleccionado) {
      return detalle.tareas.slice();
    }

    return detalle.tareas.filter(function (tarea) {
      return String(tarea.sprint_id || '') === String(sprintSeleccionado.id);
    });
  }

  function renderizarSprints(proyectoId, detalle) {
    if (!detalle.sprints.length) {
      return (
        '<div class="empty-state small">Todavia no hay sprints. Crea el primero para organizar entregas.</div>'
      );
    }

    var sprintActivo = obtenerSprintActivo(detalle);
    var sprintSeleccionado = obtenerSprintSeleccionado(detalle);
    var totalAvance = 0;

    detalle.sprints.forEach(function (sprint) {
      totalAvance += Number(sprint.objetivo_completado || 0);
    });

    var tabs =
      '<div class="sprint-nav" id="sprintNav-' + escaparHtml(proyectoId) + '">' +
        '<button class="nav-btn js-sprint-tab ' + (sprintActivo === '0' ? 'active' : '') + '" data-project-id="' + escaparHtml(proyectoId) + '" data-sprint="0">Todos</button>' +
        detalle.sprints
          .map(function (sprint) {
            return (
              '<button class="nav-btn js-sprint-tab ' + (String(sprint.id) === sprintActivo ? 'active' : '') + '" data-project-id="' + escaparHtml(proyectoId) + '" data-sprint="' + escaparHtml(sprint.id) + '">' +
                escaparHtml(etiquetaSprintTab(sprint)) +
              '</button>'
            );
          })
          .join('') +
      '</div>';

    if (sprintActivo === '0') {
      return (
        '<div class="sprint-tab-shell">' +
          tabs +
          '<article class="sprint-card sprint-card-highlight">' +
            '<div class="d-flex justify-content-between align-items-start">' +
              '<div>' +
                '<h5 class="sprint-title mb-1">Vista general</h5>' +
                '<p class="mb-1 font-weight-bold">Todos los sprints del proyecto</p>' +
                '<p class="sprint-copy mb-0">Usa las pestañas para enfocarte en un sprint especifico y filtrar el kanban.</p>' +
              '</div>' +
              '<span class="badge badge-pill badge-sprint badge-sprint-planificado">' +
                escaparHtml(String(detalle.sprints.length)) + ' sprints' +
              '</span>' +
            '</div>' +
            '<div class="sprint-meta mt-3">' +
              '<span>Total de sprints: ' + escaparHtml(String(detalle.sprints.length)) + '</span>' +
              '<span>Promedio de avance: ' + escaparHtml(String(Math.round(totalAvance / detalle.sprints.length))) + '%</span>' +
              '<span>Tareas visibles: ' + escaparHtml(String(detalle.tareas.length)) + '</span>' +
            '</div>' +
          '</article>' +
        '</div>'
      );
    }

    if (!sprintSeleccionado) {
      return tabs;
    }

    return (
      '<div class="sprint-tab-shell">' +
        tabs +
        '<article class="sprint-card sprint-card-highlight">' +
          '<div class="d-flex justify-content-between align-items-start">' +
            '<div>' +
              '<h5 class="sprint-title mb-1">Sprint ' + escaparHtml(sprintSeleccionado.numero) + '</h5>' +
              '<p class="mb-1 font-weight-bold">' + escaparHtml(sprintSeleccionado.nombre) + '</p>' +
              '<p class="sprint-copy mb-0">' +
                escaparHtml(sprintSeleccionado.descripcion || 'Sin descripcion registrada.') +
              '</p>' +
            '</div>' +
            '<div class="d-flex align-items-start">' +
              '<button class="btn btn-link btn-sm p-0 mr-3 js-editar-sprint" data-project-id="' + escaparHtml(proyectoId) + '" data-sprint-id="' + escaparHtml(sprintSeleccionado.id) + '">Editar</button>' +
              '<span class="badge badge-pill badge-sprint badge-sprint-' + escaparHtml(sprintSeleccionado.estado) + '">' +
                escaparHtml(textoEstadoSprint(sprintSeleccionado.estado)) +
              '</span>' +
            '</div>' +
          '</div>' +
          '<div class="sprint-meta mt-3">' +
            '<span>Inicio: ' + escaparHtml(formatearFecha(sprintSeleccionado.fecha_inicio)) + '</span>' +
            '<span>Fin: ' + escaparHtml(formatearFecha(sprintSeleccionado.fecha_fin)) + '</span>' +
            '<span>Avance: ' + escaparHtml(String(sprintSeleccionado.objetivo_completado || 0)) + '%</span>' +
          '</div>' +
        '</article>' +
      '</div>'
    );
  }

  function renderizarAvances(proyectoId, detalle) {
    var sprintSeleccionado = obtenerSprintSeleccionado(detalle);
    var avances;

    if (!sprintSeleccionado) {
      return '<div class="empty-state small">Selecciona un sprint especifico para registrar y consultar avances.</div>';
    }

    avances = detalle.avancesPorSprint[String(sprintSeleccionado.id)] || [];

    return (
      '<div class="avances-shell">' +
        '<div class="avances-head">' +
          '<div>' +
            '<p class="workspace-eyebrow mb-1">Seguimiento</p>' +
            '<h5 class="workspace-title mb-0">Avances del sprint</h5>' +
          '</div>' +
          '<button class="btn btn-sm btn-secondary js-nuevo-avance" data-project-id="' + escaparHtml(proyectoId) + '" data-sprint-id="' + escaparHtml(sprintSeleccionado.id) + '">' +
            '+ Avance' +
          '</button>' +
        '</div>' +
        (
          avances.length
            ? '<div class="avances-list">' +
                avances.map(function (avance) {
                  return (
                    '<article class="avance-card">' +
                      '<div class="avance-card-head">' +
                        '<span class="badge badge-sprint badge-sprint-en_progreso">' + escaparHtml(textoTipoAvance(avance.tipo_avance)) + '</span>' +
                        '<div class="task-actions">' +
                          '<button class="btn btn-link btn-sm p-0 mr-2 js-editar-avance" data-project-id="' + escaparHtml(proyectoId) + '" data-advance-id="' + escaparHtml(avance.id) + '">Editar</button>' +
                          '<button class="btn btn-link btn-sm p-0 text-danger js-eliminar-avance" data-project-id="' + escaparHtml(proyectoId) + '" data-advance-id="' + escaparHtml(avance.id) + '">Eliminar</button>' +
                        '</div>' +
                      '</div>' +
                      '<p class="avance-card-copy">' + escaparHtml(avance.descripcion || 'Sin descripcion registrada.') + '</p>' +
                      '<div class="avance-card-meta">' +
                        '<span><strong>Usuario:</strong> ' + escaparHtml(avance.usuario_nombre || 'Sin asignar') + '</span>' +
                        '<span><strong>Horas:</strong> ' + escaparHtml(String(avance.horas_trabajadas || 0)) + '</span>' +
                        '<span><strong>Estado:</strong> ' + escaparHtml(textoEstadoTarea(avance.estado_tarea)) + '</span>' +
                        '<span><strong>Fecha:</strong> ' + escaparHtml(formatearFecha(avance.fecha_reporte)) + '</span>' +
                      '</div>' +
                    '</article>'
                  );
                }).join('') +
              '</div>'
            : '<div class="empty-state">Todavia no hay avances registrados para este sprint.</div>'
        ) +
      '</div>'
    );
  }

  function renderizarTarjetaTarea(proyectoId, tarea) {
    return (
      '<article class="kanban-task" draggable="true" data-project-id="' + escaparHtml(proyectoId) + '" data-task-id="' + escaparHtml(tarea.id) + '">' +
        '<div class="kanban-task-head">' +
          '<span class="badge badge-priority badge-priority-' + escaparHtml(tarea.prioridad) + '">' +
            escaparHtml(textoPrioridad(tarea.prioridad)) +
          '</span>' +
          '<div class="task-actions">' +
            '<button class="btn btn-link btn-sm p-0 mr-2 js-editar-tarea" data-project-id="' + escaparHtml(proyectoId) + '" data-task-id="' + escaparHtml(tarea.id) + '">Editar</button>' +
            '<button class="btn btn-link btn-sm p-0 text-danger js-eliminar-tarea" data-project-id="' + escaparHtml(proyectoId) + '" data-task-id="' + escaparHtml(tarea.id) + '">Eliminar</button>' +
          '</div>' +
        '</div>' +
        '<h5 class="kanban-task-title">' + escaparHtml(tarea.titulo) + '</h5>' +
        '<p class="kanban-task-copy">' +
          escaparHtml(tarea.descripcion || 'Sin descripcion registrada.') +
        '</p>' +
        '<div class="kanban-task-meta">' +
          '<span><strong>Asignado:</strong> ' + escaparHtml(tarea.asignado_nombre || 'Sin asignar') + '</span>' +
          '<span><strong>Sprint:</strong> ' + escaparHtml(tarea.sprint_nombre || 'Backlog') + '</span>' +
          '<span><strong>Fecha:</strong> ' + escaparHtml(formatearFecha(tarea.fecha_limite)) + '</span>' +
        '</div>' +
      '</article>'
    );
  }

  function renderizarKanban(proyectoId, detalle) {
    var tareasVisibles = obtenerTareasVisibles(detalle);

    return columnasKanban
      .map(function (columna) {
        var tareas = tareasVisibles.filter(function (tarea) {
          return tarea.estado === columna.key;
        });

        return (
          '<section class="kanban-column">' +
            '<header class="kanban-column-header">' +
              '<h5 class="mb-0">' + escaparHtml(columna.titulo) + '</h5>' +
              '<span class="kanban-counter">' + escaparHtml(String(tareas.length)) + '</span>' +
            '</header>' +
            '<div class="kanban-column-cards" data-project-id="' + escaparHtml(proyectoId) + '" data-target-status="' + escaparHtml(columna.key) + '">' +
              (
                tareas.length
                  ? tareas.map(function (tarea) {
                      return renderizarTarjetaTarea(proyectoId, tarea);
                    }).join('')
                  : '<div class="empty-state">Sin tareas en esta columna.</div>'
              ) +
            '</div>' +
          '</section>'
        );
      })
      .join('');
  }

  function renderizarWorkspace(proyecto, detalle) {
    if (!detalle.abierto) {
      return '';
    }

    if (detalle.cargando && !detalle.cargado) {
      return '<div class="workspace-loading">Cargando sprints y tareas del proyecto...</div>';
    }

    return (
      '<section class="project-workspace">' +
        '<div class="workspace-grid">' +
          '<div class="workspace-panel">' +
            '<div class="workspace-panel-head">' +
              '<div>' +
                '<p class="workspace-eyebrow mb-1">Planificacion agile</p>' +
                '<h4 class="workspace-title mb-0">Sprints del proyecto</h4>' +
              '</div>' +
              '<button class="btn btn-sm btn-secondary js-nuevo-sprint" data-project-id="' + escaparHtml(proyecto.id) + '">' +
                '+ Sprint' +
              '</button>' +
            '</div>' +
            '<div class="workspace-panel-body">' +
              renderizarSprints(proyecto.id, detalle) +
              renderizarAvances(proyecto.id, detalle) +
            '</div>' +
          '</div>' +
          '<div class="workspace-panel workspace-panel-kanban">' +
            '<div class="workspace-panel-head">' +
              '<div>' +
                '<p class="workspace-eyebrow mb-1">Operacion diaria</p>' +
                '<h4 class="workspace-title mb-0">Tablero Kanban</h4>' +
              '</div>' +
              '<button class="btn btn-sm btn-primary js-nueva-tarea" data-project-id="' + escaparHtml(proyecto.id) + '">' +
                '+ Tarea' +
              '</button>' +
            '</div>' +
            '<div class="workspace-panel-body">' +
              '<div class="kanban-board">' + renderizarKanban(proyecto.id, detalle) + '</div>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</section>'
    );
  }

  function renderizarProyectos() {
    var proyectosVisibles = filtrarProyectos(proyectos);

    emitirEstadoDashboard();

    if (!proyectos.length) {
      $contenedor.html(
        '<div class="empty-dashboard">Aun no hay proyectos registrados. Crea el primero para empezar.</div>'
      );
      return;
    }

    if (!proyectosVisibles.length) {
      $contenedor.html(
        '<div class="empty-dashboard">No hay proyectos que coincidan con los filtros actuales.</div>'
      );
      return;
    }

    var html = proyectosVisibles
      .map(function (proyecto) {
        var detalle = obtenerDetalle(proyecto.id);
        var totalPendientes = contarTareasPorEstado(detalle.tareas, 'pendiente');
        var totalActivas = contarTareasPorEstado(detalle.tareas, 'en_progreso');
        var totalRevision = contarTareasPorEstado(detalle.tareas, 'en_revision');

        return (
          '<article class="project-shell">' +
            '<div class="project-card project-card-wide">' +
              '<div class="project-card-head">' +
                '<div>' +
                  '<p class="project-kicker mb-2">Proyecto</p>' +
                  '<h2 class="project-name mb-2">' + escaparHtml(proyecto.nombre) + '</h2>' +
                  '<p class="project-description mb-0">' +
                    escaparHtml(proyecto.descripcion || 'Sin descripcion registrada.') +
                  '</p>' +
                '</div>' +
                '<div class="project-actions">' +
                  '<button class="btn btn-sm btn-secondary js-toggle-proyecto" data-project-id="' + escaparHtml(proyecto.id) + '">' +
                    (detalle.abierto ? 'Ocultar workspace' : 'Ver workspace') +
                  '</button>' +
                  '<button class="btn btn-sm btn-secondary js-editar-proyecto" data-project-id="' + escaparHtml(proyecto.id) + '">Editar</button>' +
                  (
                    puedeAlternarEstadoProyecto(proyecto.estado)
                      ? '<button class="btn btn-sm btn-secondary js-cambiar-estado-proyecto" data-project-id="' + escaparHtml(proyecto.id) + '" data-estado-actual="' + escaparHtml(proyecto.estado) + '">' + etiquetaBotonEstadoProyecto(proyecto.estado) + '</button>'
                      : ''
                  ) +
                  '<button class="btn btn-sm btn-outline-danger js-eliminar-proyecto" data-project-id="' + escaparHtml(proyecto.id) + '">Eliminar</button>' +
                '</div>' +
              '</div>' +
              '<div class="project-summary">' +
                '<div class="project-summary-item">' +
                  '<span class="summary-label">Estado</span>' +
                  '<strong>' + escaparHtml(textoEstadoProyecto(proyecto.estado)) + '</strong>' +
                '</div>' +
                '<div class="project-summary-item">' +
                  '<span class="summary-label">Responsable</span>' +
                  '<strong>' + escaparHtml(proyecto.responsable_nombre || 'Sin asignar') + '</strong>' +
                '</div>' +
                '<div class="project-summary-item">' +
                  '<span class="summary-label">Sprints</span>' +
                  '<strong>' + escaparHtml(String(proyecto.total_sprints || 0)) + '</strong>' +
                '</div>' +
                '<div class="project-summary-item">' +
                  '<span class="summary-label">Tareas</span>' +
                  '<strong>' + escaparHtml(String(proyecto.total_tareas || 0)) + '</strong>' +
                '</div>' +
                '<div class="project-summary-item">' +
                  '<span class="summary-label">Pendientes</span>' +
                  '<strong>' + escaparHtml(String(totalPendientes)) + '</strong>' +
                '</div>' +
                '<div class="project-summary-item">' +
                  '<span class="summary-label">En curso</span>' +
                  '<strong>' + escaparHtml(String(totalActivas + totalRevision)) + '</strong>' +
                '</div>' +
                '<div class="project-summary-item">' +
                  '<span class="summary-label">Inicio</span>' +
                  '<strong>' + escaparHtml(formatearFecha(proyecto.fecha_inicio)) + '</strong>' +
                '</div>' +
                '<div class="project-summary-item">' +
                  '<span class="summary-label">Entrega</span>' +
                  '<strong>' + escaparHtml(formatearFecha(proyecto.fecha_fin_estimada)) + '</strong>' +
                '</div>' +
              '</div>' +
              renderizarWorkspace(proyecto, detalle) +
            '</div>' +
          '</article>'
        );
      })
      .join('');

    $contenedor.html(html);
  }

  function cargarUsuarios() {
    return $.getJSON('/api/usuarios')
      .done(function (respuesta) {
        usuarios = respuesta.usuarios || [];
        emitirEstadoDashboard();
      })
      .fail(function (xhr) {
        var mensaje = manejarErrorAjax(xhr, 'No fue posible cargar los usuarios.');

        if (mensaje) {
          mostrarAlerta('error', mensaje);
        }
      });
  }

  function cargarProyectos() {
    $contenedor.html('<div class="workspace-loading">Cargando proyectos...</div>');

    return $.getJSON('/api/proyectos')
      .done(function (respuesta) {
        proyectos = respuesta.proyectos || [];
        renderizarProyectos();
      })
      .fail(function (xhr) {
        var mensaje = manejarErrorAjax(xhr, 'No fue posible cargar los proyectos.');

        if (mensaje) {
          $contenedor.html('<div class="empty-dashboard empty-dashboard-error">' + escaparHtml(mensaje) + '</div>');
        }
      });
  }

  function cargarDetalleProyecto(proyectoId, silencioso) {
    var detalle = obtenerDetalle(proyectoId);
    detalle.cargando = true;

    if (!silencioso) {
      renderizarProyectos();
    }

    return $.when(
      $.getJSON('/api/sprints/' + proyectoId),
      $.getJSON('/api/tareas/' + proyectoId)
    )
      .done(function (respuestaSprints, respuestaTareas) {
        detalle.sprints = respuestaSprints[0].sprints || [];
        detalle.tareas = respuestaTareas[0].tareas || [];
        detalle.avancesPorSprint = {};
        obtenerSprintActivo(detalle);

        var solicitudesAvances = detalle.sprints.map(function (sprint) {
          return $.getJSON('/api/avances/' + sprint.id)
            .done(function (respuestaAvances) {
              detalle.avancesPorSprint[String(sprint.id)] = respuestaAvances.avances || [];
            });
        });

        if (!solicitudesAvances.length) {
          detalle.cargado = true;
          detalle.cargando = false;
          renderizarProyectos();
          return;
        }

        $.when.apply($, solicitudesAvances)
          .done(function () {
            detalle.cargado = true;
            detalle.cargando = false;
            renderizarProyectos();
          })
          .fail(function (xhr) {
            detalle.cargando = false;
            var mensaje = manejarErrorAjax(xhr, 'No fue posible cargar los avances del sprint.');

            if (mensaje) {
              mostrarAlerta('error', mensaje);
            }

            renderizarProyectos();
          });
      })
      .fail(function (xhr) {
        detalle.cargando = false;
        var mensaje = manejarErrorAjax(xhr, 'No fue posible cargar el workspace del proyecto.');

        if (mensaje) {
          mostrarAlerta('error', mensaje);
          renderizarProyectos();
        }
      });
  }

  function popularSelectUsuarios(seleccionadoId) {
    var opciones = ['<option value="">Sin asignar</option>'];

    usuarios.forEach(function (usuario) {
      opciones.push(
        '<option value="' + escaparHtml(usuario.id) + '"' +
          (String(usuario.id) === String(seleccionadoId || '') ? ' selected' : '') +
          '>' +
          escaparHtml(usuario.nombre + ' - ' + usuario.rol) +
        '</option>'
      );
    });

    $('#tareaAsignadoId').html(opciones.join(''));
  }

  function popularSelectResponsables(seleccionadoId) {
    var opciones = usuarios.map(function (usuario) {
      return (
        '<option value="' + escaparHtml(usuario.id) + '"' +
          (String(usuario.id) === String(seleccionadoId || '') ? ' selected' : '') +
          '>' +
          escaparHtml(usuario.nombre + ' - ' + usuario.rol) +
        '</option>'
      );
    });

    $('#proyectoResponsableId').html(opciones.join(''));
  }

  function popularSelectSprints(proyectoId, seleccionadoId) {
    var detalle = obtenerDetalle(proyectoId);
    var opciones = ['<option value="">Backlog</option>'];

    detalle.sprints.forEach(function (sprint) {
      opciones.push(
        '<option value="' + escaparHtml(sprint.id) + '"' +
          (String(sprint.id) === String(seleccionadoId || '') ? ' selected' : '') +
          '>' +
          escaparHtml('Sprint ' + sprint.numero + ' - ' + sprint.nombre) +
        '</option>'
      );
    });

    $('#tareaSprintId').html(opciones.join(''));
  }

  function abrirModalProyecto(proyecto) {
    $formProyecto.trigger('reset');
    popularSelectResponsables(proyecto ? proyecto.responsable_id : $('body').data('usuarioId'));

    if (proyecto) {
      $modalProyectoTitulo.text('Editar Proyecto');
      $('#proyectoId').val(proyecto.id);
      $('#proyectoNombre').val(proyecto.nombre || '');
      $('#proyectoDescripcion').val(proyecto.descripcion || '');
      $('#proyectoEstado').val(proyecto.estado || 'activo');
      $('#proyectoFechaInicio').val(proyecto.fecha_inicio || '');
      $('#proyectoFechaFin').val(proyecto.fecha_fin_estimada || '');
      $('#proyectoResponsableId').val(String(proyecto.responsable_id || ''));
      $('#btnGuardarProyecto').text('Actualizar Proyecto');
    } else {
      $modalProyectoTitulo.text('Nuevo Proyecto');
      $('#proyectoId').val('');
      $('#proyectoEstado').val('activo');
      $('#btnGuardarProyecto').text('Guardar Proyecto');
    }

    $modalProyecto.modal('show');
  }

  function abrirModalSprint(proyectoId, sprint) {
    var detalle = obtenerDetalle(proyectoId);
    var siguienteNumero = 1;

    detalle.sprints.forEach(function (sprint) {
      if (Number(sprint.numero) >= siguienteNumero) {
        siguienteNumero = Number(sprint.numero) + 1;
      }
    });

    $formSprint.trigger('reset');
    $('#sprintProyectoId').val(proyectoId);
    $('#sprintId').val('');
    $('#sprintObjetivoCompletado').val(0);

    if (sprint) {
      $modalSprintTitulo.text('Editar Sprint');
      $('#sprintId').val(sprint.id);
      $('#sprintNumero').val(sprint.numero || '');
      $('#sprintNombre').val(sprint.nombre || '');
      $('#sprintDescripcion').val(sprint.descripcion || '');
      $('#sprintFechaInicio').val(sprint.fecha_inicio || '');
      $('#sprintFechaFin').val(sprint.fecha_fin || '');
      $('#sprintEstado').val(sprint.estado || 'planificado');
      $('#sprintObjetivoCompletado').val(sprint.objetivo_completado || 0);
      $('#btnGuardarSprint').text('Actualizar Sprint');
    } else {
      $modalSprintTitulo.text('Nuevo Sprint');
      $('#sprintNumero').val(siguienteNumero);
      $('#sprintEstado').val('planificado');
      $('#btnGuardarSprint').text('Guardar Sprint');
    }

    $modalSprint.modal('show');
  }

  function abrirModalTarea(proyectoId, tarea) {
    $formTarea.trigger('reset');
    $('#tareaProyectoId').val(proyectoId);

    if (tarea) {
      $('#modalTareaTitulo').text('Editar Tarea');
      $('#tareaId').val(tarea.id);
      $('#tareaTitulo').val(tarea.titulo || '');
      $('#tareaDescripcion').val(tarea.descripcion || '');
      $('#tareaPrioridad').val(tarea.prioridad || 'media');
      $('#tareaEstado').val(tarea.estado || 'pendiente');
      $('#tareaFechaLimite').val(tarea.fecha_limite || '');
      popularSelectUsuarios(tarea.asignado_id);
      popularSelectSprints(proyectoId, tarea.sprint_id);
    } else {
      $('#modalTareaTitulo').text('Nueva Tarea');
      $('#tareaId').val('');
      $('#tareaEstado').val('pendiente');
      $('#tareaPrioridad').val('media');
      popularSelectUsuarios(null);
      popularSelectSprints(
        proyectoId,
        obtenerSprintActivo(obtenerDetalle(proyectoId)) !== '0'
          ? obtenerSprintActivo(obtenerDetalle(proyectoId))
          : null
      );
    }

    $modalTarea.modal('show');
  }

  function abrirModalAvance(proyectoId, sprintId, avance) {
    $formAvance.trigger('reset');
    $('#avanceProyectoId').val(proyectoId);
    $('#avanceSprintId').val(sprintId);
    $('#avanceId').val('');
    $('#avanceEstadoTarea').val('avances');
    $('#avanceTipo').val('caracteristica');

    if (avance) {
      $modalAvanceTitulo.text('Editar Avance');
      $('#avanceId').val(avance.id);
      $('#avanceSprintId').val(avance.sprint_id || sprintId);
      $('#avanceDescripcion').val(avance.descripcion || '');
      $('#avanceTipo').val(avance.tipo_avance || 'caracteristica');
      $('#avanceHoras').val(avance.horas_trabajadas || '');
      $('#avanceEstadoTarea').val(avance.estado_tarea || 'avances');
      $('#btnGuardarAvance').text('Actualizar Avance');
    } else {
      $modalAvanceTitulo.text('Nuevo Avance');
      $('#avanceHoras').val('');
      $('#btnGuardarAvance').text('Guardar Avance');
    }

    $modalAvance.modal('show');
  }

  function guardarProyecto() {
    var proyectoId = $('#proyectoId').val();
    var nombre = $('#proyectoNombre').val().trim();
    var fechaInicio = $('#proyectoFechaInicio').val();

    if (!nombre || !fechaInicio) {
      window.alert('Completa el nombre y la fecha de inicio del proyecto.');
      return;
    }

    var $boton = $('#btnGuardarProyecto');
    $boton.prop('disabled', true).text('Guardando...');

    $.ajax({
      url: proyectoId ? '/api/proyectos/' + proyectoId : '/api/proyectos',
      type: proyectoId ? 'PUT' : 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        nombre: nombre,
        descripcion: $('#proyectoDescripcion').val().trim(),
        estado: $('#proyectoEstado').val(),
        fecha_inicio: fechaInicio,
        fecha_fin_estimada: $('#proyectoFechaFin').val() || null,
        responsable_id: $('#proyectoResponsableId').val() || null
      })
    })
      .done(function (respuesta) {
        $modalProyecto.modal('hide');
        limpiarAlerta();
        mostrarAlerta('success', respuesta.mensaje || 'Proyecto guardado correctamente.');
        cargarProyectos().done(function () {
          if (proyectoId) {
            var detalle = obtenerDetalle(proyectoId);

            if (detalle.abierto) {
              cargarDetalleProyecto(proyectoId, true);
            }
          }
        });
      })
      .fail(function (xhr) {
        var mensaje = manejarErrorAjax(xhr, 'No fue posible guardar el proyecto.');

        if (mensaje) {
          window.alert(mensaje);
        }
      })
      .always(function () {
        $boton.prop('disabled', false).text(proyectoId ? 'Actualizar Proyecto' : 'Guardar Proyecto');
      });
  }

  function guardarSprint() {
    var proyectoId = $('#sprintProyectoId').val();
    var sprintId = $('#sprintId').val();
    var nombre = $('#sprintNombre').val().trim();
    var fechaInicio = $('#sprintFechaInicio').val();
    var fechaFin = $('#sprintFechaFin').val();

    if (!proyectoId || !nombre || !fechaInicio || !fechaFin) {
      window.alert('Completa nombre, proyecto y fechas del sprint.');
      return;
    }

    var $boton = $('#btnGuardarSprint');
    $boton.prop('disabled', true).text('Guardando...');

    $.ajax({
      url: sprintId ? '/api/sprint/' + sprintId : '/api/sprints/' + proyectoId,
      type: sprintId ? 'PUT' : 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        numero: $('#sprintNumero').val() || null,
        nombre: nombre,
        descripcion: $('#sprintDescripcion').val().trim(),
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        estado: $('#sprintEstado').val(),
        objetivo_completado: $('#sprintObjetivoCompletado').val() || 0
      })
    })
      .done(function (respuesta) {
        $modalSprint.modal('hide');
        mostrarAlerta('success', respuesta.mensaje || 'Sprint guardado correctamente.');
        cargarProyectos().done(function () {
          var detalle = obtenerDetalle(proyectoId);
          detalle.abierto = true;
          cargarDetalleProyecto(proyectoId, true);
        });
      })
      .fail(function (xhr) {
        var mensaje = manejarErrorAjax(xhr, 'No fue posible guardar el sprint.');

        if (mensaje) {
          window.alert(mensaje);
        }
      })
      .always(function () {
        $boton.prop('disabled', false).text(sprintId ? 'Actualizar Sprint' : 'Guardar Sprint');
      });
  }

  function guardarTarea() {
    var proyectoId = $('#tareaProyectoId').val();
    var tareaId = $('#tareaId').val();
    var titulo = $('#tareaTitulo').val().trim();

    if (!proyectoId || !titulo) {
      window.alert('Completa al menos el titulo de la tarea.');
      return;
    }

    var $boton = $('#btnGuardarTarea');
    $boton.prop('disabled', true).text('Guardando...');

    $.ajax({
      url: tareaId ? '/api/tarea/' + tareaId : '/api/tareas/' + proyectoId,
      type: tareaId ? 'PUT' : 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        titulo: titulo,
        descripcion: $('#tareaDescripcion').val().trim(),
        sprint_id: $('#tareaSprintId').val() || null,
        asignado_id: $('#tareaAsignadoId').val() || null,
        prioridad: $('#tareaPrioridad').val(),
        estado: $('#tareaEstado').val(),
        fecha_limite: $('#tareaFechaLimite').val() || null
      })
    })
      .done(function (respuesta) {
        $modalTarea.modal('hide');
        mostrarAlerta('success', respuesta.mensaje || 'Tarea guardada correctamente.');
        var detalle = obtenerDetalle(proyectoId);
        detalle.abierto = true;
        cargarProyectos().done(function () {
          cargarDetalleProyecto(proyectoId, true);
        });
      })
      .fail(function (xhr) {
        var mensaje = manejarErrorAjax(xhr, 'No fue posible guardar la tarea.');

        if (mensaje) {
          window.alert(mensaje);
        }
      })
      .always(function () {
        $boton.prop('disabled', false).text('Guardar Tarea');
      });
  }

  function guardarAvance() {
    var proyectoId = $('#avanceProyectoId').val();
    var sprintId = $('#avanceSprintId').val();
    var avanceId = $('#avanceId').val();
    var descripcion = $('#avanceDescripcion').val().trim();

    if (!proyectoId || !sprintId || !descripcion) {
      window.alert('Completa el sprint y la descripcion del avance.');
      return;
    }

    var $boton = $('#btnGuardarAvance');
    $boton.prop('disabled', true).text('Guardando...');

    $.ajax({
      url: avanceId ? '/api/avance/' + avanceId : '/api/avances/' + sprintId,
      type: avanceId ? 'PUT' : 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        descripcion: descripcion,
        tipo_avance: $('#avanceTipo').val(),
        horas_trabajadas: $('#avanceHoras').val() || null,
        estado_tarea: $('#avanceEstadoTarea').val()
      })
    })
      .done(function (respuesta) {
        $modalAvance.modal('hide');
        mostrarAlerta('success', respuesta.mensaje || 'Avance guardado correctamente.');
        var detalle = obtenerDetalle(proyectoId);
        detalle.abierto = true;
        cargarProyectos().done(function () {
          cargarDetalleProyecto(proyectoId, true);
        });
      })
      .fail(function (xhr) {
        var mensaje = manejarErrorAjax(xhr, 'No fue posible guardar el avance.');

        if (mensaje) {
          window.alert(mensaje);
        }
      })
      .always(function () {
        $boton.prop('disabled', false).text(avanceId ? 'Actualizar Avance' : 'Guardar Avance');
      });
  }

  function eliminarProyecto(proyectoId) {
    var proyecto = obtenerProyecto(proyectoId);
    var nombre = proyecto ? proyecto.nombre : 'este proyecto';

    if (!window.confirm('Se eliminara "' + nombre + '" junto con sus sprints y tareas. Deseas continuar?')) {
      return;
    }

    $.ajax({
      url: '/api/proyectos/' + proyectoId,
      type: 'DELETE'
    })
      .done(function (respuesta) {
        delete detallePorProyecto[proyectoId];
        mostrarAlerta('success', respuesta.mensaje || 'Proyecto eliminado correctamente.');
        cargarProyectos();
      })
      .fail(function (xhr) {
        var mensaje = manejarErrorAjax(xhr, 'No fue posible eliminar el proyecto.');

        if (mensaje) {
          mostrarAlerta('error', mensaje);
        }
      });
  }

  function cambiarEstadoProyecto(proyectoId, estadoActual) {
    var estadoDestino = siguienteEstadoProyecto(estadoActual);
    var proyecto = obtenerProyecto(proyectoId);
    var nombre = proyecto ? proyecto.nombre : 'este proyecto';
    var accion = estadoDestino === 'activo' ? 'activar' : 'pausar';

    if (!window.confirm('Se va a ' + accion + ' "' + nombre + '". Deseas continuar?')) {
      return;
    }

    $.ajax({
      url: '/api/proyectos/' + proyectoId + '/estado',
      type: 'PATCH',
      contentType: 'application/json',
      data: JSON.stringify({
        estado: estadoDestino
      })
    })
      .done(function (respuesta) {
        mostrarAlerta('success', respuesta.mensaje || 'Estado del proyecto actualizado correctamente.');
        cargarProyectos().done(function () {
          var detalle = obtenerDetalle(proyectoId);

          if (detalle.abierto) {
            cargarDetalleProyecto(proyectoId, true);
          }
        });
      })
      .fail(function (xhr) {
        var mensaje = manejarErrorAjax(xhr, 'No fue posible cambiar el estado del proyecto.');

        if (mensaje) {
          mostrarAlerta('error', mensaje);
        }
      });
  }

  function eliminarTarea(proyectoId, tareaId) {
    if (!window.confirm('Esta tarea se eliminara del tablero. Deseas continuar?')) {
      return;
    }

    $.ajax({
      url: '/api/tarea/' + tareaId,
      type: 'DELETE'
    })
      .done(function (respuesta) {
        mostrarAlerta('success', respuesta.mensaje || 'Tarea eliminada correctamente.');
        var detalle = obtenerDetalle(proyectoId);
        detalle.abierto = true;
        cargarProyectos().done(function () {
          cargarDetalleProyecto(proyectoId, true);
        });
      })
      .fail(function (xhr) {
        var mensaje = manejarErrorAjax(xhr, 'No fue posible eliminar la tarea.');

        if (mensaje) {
          mostrarAlerta('error', mensaje);
        }
      });
  }

  function eliminarAvance(proyectoId, avanceId) {
    if (!window.confirm('Este avance se eliminara del sprint. Deseas continuar?')) {
      return;
    }

    $.ajax({
      url: '/api/avance/' + avanceId,
      type: 'DELETE'
    })
      .done(function (respuesta) {
        mostrarAlerta('success', respuesta.mensaje || 'Avance eliminado correctamente.');
        var detalle = obtenerDetalle(proyectoId);
        detalle.abierto = true;
        cargarProyectos().done(function () {
          cargarDetalleProyecto(proyectoId, true);
        });
      })
      .fail(function (xhr) {
        var mensaje = manejarErrorAjax(xhr, 'No fue posible eliminar el avance.');

        if (mensaje) {
          mostrarAlerta('error', mensaje);
        }
      });
  }

  function moverTareaKanban(proyectoId, tareaId, estadoDestino, posicionDestino) {
    $.ajax({
      url: '/api/tarea/' + tareaId + '/kanban',
      type: 'PATCH',
      contentType: 'application/json',
      data: JSON.stringify({
        estado: estadoDestino,
        posicion: posicionDestino
      })
    })
      .done(function () {
        var detalle = obtenerDetalle(proyectoId);
        detalle.abierto = true;
        cargarDetalleProyecto(proyectoId, true);
      })
      .fail(function (xhr) {
        var mensaje = manejarErrorAjax(xhr, 'No fue posible mover la tarea.');

        if (mensaje) {
          mostrarAlerta('error', mensaje);
          cargarDetalleProyecto(proyectoId, true);
        }
      });
  }

  function calcularPosicionDrop($contenedorDestino, clientY, tareaId) {
    var posicion = 1;
    var encontrada = false;
    var $tarjetas = $contenedorDestino.children('.kanban-task').filter(function () {
      return String($(this).data('taskId')) !== String(tareaId);
    });

    $tarjetas.each(function (indice) {
      var rect = this.getBoundingClientRect();
      var puntoCorte = rect.top + rect.height / 2;

      if (!encontrada && clientY < puntoCorte) {
        posicion = indice + 1;
        encontrada = true;
        return false;
      }

      return true;
    });

    if (!encontrada) {
      posicion = $tarjetas.length + 1;
    }

    return posicion;
  }

  $('#btnNuevoProyecto').on('click', function () {
    abrirModalProyecto(null);
  });

  window.addEventListener('dashboard:new-project', function () {
    abrirModalProyecto(null);
  });

  window.addEventListener('dashboard:filters-changed', function (evento) {
    var detail = evento.detail || {};
    dashboardFiltros.busqueda = detail.busqueda || '';
    dashboardFiltros.estado = detail.estado || 'todos';
    renderizarProyectos();
  });

  $('#btnGuardarProyecto').on('click', guardarProyecto);
  $('#btnGuardarSprint').on('click', guardarSprint);
  $('#btnGuardarTarea').on('click', guardarTarea);
  $('#btnGuardarAvance').on('click', guardarAvance);

  $contenedor.on('click', '.js-toggle-proyecto', function () {
    var proyectoId = $(this).data('projectId');
    var detalle = obtenerDetalle(proyectoId);
    detalle.abierto = !detalle.abierto;

    renderizarProyectos();

    if (detalle.abierto) {
      cargarDetalleProyecto(proyectoId, true);
    }
  });

  $contenedor.on('click', '.js-nuevo-sprint', function () {
    abrirModalSprint($(this).data('projectId'), null);
  });

  $contenedor.on('click', '.js-nueva-tarea', function () {
    abrirModalTarea($(this).data('projectId'), null);
  });

  $contenedor.on('click', '.js-nuevo-avance', function () {
    abrirModalAvance($(this).data('projectId'), $(this).data('sprintId'), null);
  });

  $contenedor.on('click', '.js-editar-proyecto', function () {
    var proyecto = obtenerProyecto($(this).data('projectId'));

    if (proyecto) {
      abrirModalProyecto(proyecto);
    }
  });

  $contenedor.on('click', '.js-editar-sprint', function () {
    var proyectoId = $(this).data('projectId');
    var sprint = obtenerSprint(proyectoId, $(this).data('sprintId'));

    if (sprint) {
      abrirModalSprint(proyectoId, sprint);
    }
  });

  $contenedor.on('click', '.js-sprint-tab', function () {
    var proyectoId = $(this).data('projectId');
    var detalle = obtenerDetalle(proyectoId);
    detalle.sprintActivo = String($(this).data('sprint'));
    renderizarProyectos();
  });

  $contenedor.on('click', '.js-eliminar-proyecto', function () {
    eliminarProyecto($(this).data('projectId'));
  });

  $contenedor.on('click', '.js-cambiar-estado-proyecto', function () {
    cambiarEstadoProyecto($(this).data('projectId'), $(this).data('estadoActual'));
  });

  $contenedor.on('click', '.js-editar-tarea', function () {
    var proyectoId = $(this).data('projectId');
    var tareaId = $(this).data('taskId');
    var tarea = obtenerTarea(proyectoId, tareaId);

    if (tarea) {
      abrirModalTarea(proyectoId, tarea);
    }
  });

  $contenedor.on('click', '.js-eliminar-tarea', function () {
    eliminarTarea($(this).data('projectId'), $(this).data('taskId'));
  });

  $contenedor.on('click', '.js-editar-avance', function () {
    var proyectoId = $(this).data('projectId');
    var avanceId = $(this).data('advanceId');
    var avance = obtenerAvance(proyectoId, avanceId);

    if (avance) {
      abrirModalAvance(proyectoId, avance.sprint_id, avance);
    }
  });

  $contenedor.on('click', '.js-eliminar-avance', function () {
    eliminarAvance($(this).data('projectId'), $(this).data('advanceId'));
  });

  $contenedor.on('dragstart', '.kanban-task', function (evento) {
    var original = evento.originalEvent;
    dragContexto = {
      proyectoId: $(this).data('projectId'),
      tareaId: $(this).data('taskId')
    };

    $(this).addClass('is-dragging');
    original.dataTransfer.effectAllowed = 'move';
    original.dataTransfer.setData('text/plain', String(dragContexto.tareaId));
  });

  $contenedor.on('dragend', '.kanban-task', function () {
    $('.kanban-task').removeClass('is-dragging');
    $('.kanban-column-cards').removeClass('is-drop-target');
    dragContexto = null;
  });

  $contenedor.on('dragover', '.kanban-column-cards', function (evento) {
    evento.preventDefault();
    $(this).addClass('is-drop-target');
  });

  $contenedor.on('dragleave', '.kanban-column-cards', function () {
    $(this).removeClass('is-drop-target');
  });

  $contenedor.on('drop', '.kanban-column-cards', function (evento) {
    evento.preventDefault();
    $(this).removeClass('is-drop-target');

    if (!dragContexto) {
      return;
    }

    var $zona = $(this);
    var estadoDestino = $zona.data('targetStatus');
    var proyectoId = $zona.data('projectId');
    var posicionDestino = calcularPosicionDrop($zona, evento.originalEvent.clientY, dragContexto.tareaId);

    moverTareaKanban(proyectoId, dragContexto.tareaId, estadoDestino, posicionDestino);
  });

  $usuarioNombre.text($('body').data('usuarioNombre') || $usuarioNombre.text());

  $.when(cargarUsuarios(), cargarProyectos());
});
