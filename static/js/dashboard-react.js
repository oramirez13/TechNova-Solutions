(function () {
  var rootElement = document.getElementById('dashboardReactRoot');

  if (!rootElement || !window.React || !window.ReactDOM) {
    return;
  }

  var React = window.React;
  var createRoot = window.ReactDOM.createRoot;
  var e = React.createElement;

  function DashboardHeaderApp() {
    var body = document.body;
    var usuario = React.useMemo(function () {
      return {
        nombre: body.dataset.usuarioNombre || 'Equipo',
        rol: body.dataset.usuarioRol || 'Usuario',
        correo: body.dataset.usuarioCorreo || ''
      };
    }, []);
    var hoy = React.useMemo(function () {
      return new Intl.DateTimeFormat('es-CR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      }).format(new Date());
    }, []);
    var estadoInicial = React.useMemo(function () {
      return {
        proyectos: [],
        detallePorProyecto: {},
        filtros: { busqueda: '', estado: 'todos' }
      };
    }, []);
    var stateRef = React.useRef(estadoInicial);
    var _useState = React.useState(estadoInicial);
    var dashboardState = _useState[0];
    var setDashboardState = _useState[1];

    React.useEffect(function () {
      function manejarActualizacion(evento) {
        var detail = evento.detail || estadoInicial;
        stateRef.current = detail;
        setDashboardState(detail);
      }

      window.addEventListener('dashboard:data-updated', manejarActualizacion);
      return function () {
        window.removeEventListener('dashboard:data-updated', manejarActualizacion);
      };
    }, [estadoInicial]);

    function emitirFiltro(parcial) {
      var filtrosActuales = stateRef.current.filtros || { busqueda: '', estado: 'todos' };
      var siguientesFiltros = {
        busqueda: Object.prototype.hasOwnProperty.call(parcial, 'busqueda')
          ? parcial.busqueda
          : filtrosActuales.busqueda,
        estado: Object.prototype.hasOwnProperty.call(parcial, 'estado')
          ? parcial.estado
          : filtrosActuales.estado
      };

      window.dispatchEvent(
        new CustomEvent('dashboard:filters-changed', {
          detail: siguientesFiltros
        })
      );
    }

    var proyectos = dashboardState.proyectos || [];
    var detallePorProyecto = dashboardState.detallePorProyecto || {};
    var filtros = dashboardState.filtros || { busqueda: '', estado: 'todos' };
    var proyectosActivos = 0;
    var sprintsEnProgreso = 0;
    var tareasEnRevision = 0;
    var tareasCompletadas = 0;
    var entregasProximas = 0;
    var resumenEquipo = {};

    proyectos.forEach(function (proyecto) {
      var detalle = detallePorProyecto[proyecto.id] || { sprints: [], tareas: [] };
      var fechaFin = proyecto.fecha_fin_estimada ? new Date(proyecto.fecha_fin_estimada + 'T00:00:00') : null;
      var diasRestantes = fechaFin ? Math.ceil((fechaFin - new Date()) / 86400000) : null;

      if (proyecto.estado === 'activo') {
        proyectosActivos += 1;
      }

      if (fechaFin && diasRestantes >= 0 && diasRestantes <= 14) {
        entregasProximas += 1;
      }

      (detalle.sprints || []).forEach(function (sprint) {
        if (sprint.estado === 'en_progreso') {
          sprintsEnProgreso += 1;
        }
      });

      (detalle.tareas || []).forEach(function (tarea) {
        if (tarea.estado === 'en_revision') {
          tareasEnRevision += 1;
        }

        if (tarea.estado === 'completada') {
          tareasCompletadas += 1;
        }

        if (tarea.asignado_nombre) {
          resumenEquipo[tarea.asignado_nombre] = (resumenEquipo[tarea.asignado_nombre] || 0) + 1;
        }
      });
    });

    var cargaTotalEquipo = Object.keys(resumenEquipo)
      .map(function (nombre) {
        return { nombre: nombre, total: resumenEquipo[nombre] };
      })
      .sort(function (a, b) {
        return b.total - a.total;
      })
      .slice(0, 3);

    var kpis = [
      {
        label: 'Proyectos activos',
        value: String(proyectosActivos),
        helper: proyectos.length ? String(proyectos.length) + ' en cartera' : 'Sin proyectos'
      },
      {
        label: 'Sprints en progreso',
        value: String(sprintsEnProgreso),
        helper: 'Visibilidad del ritmo de entrega'
      },
      {
        label: 'Tareas en revision',
        value: String(tareasEnRevision),
        helper: 'Cuellos de botella del flujo'
      },
      {
        label: 'Entregas proximas',
        value: String(entregasProximas),
        helper: 'Con fecha estimada en 14 dias'
      }
    ];

    return e(
      React.Fragment,
      null,
      e(
        'section',
        { className: 'dashboard-hero dashboard-hero-modern' },
        e(
          'div',
          { className: 'dashboard-hero-copy' },
          e('p', { className: 'dashboard-kicker mb-2' }, 'Workspace TechNova'),
          e(
            'p',
            { className: 'dashboard-subtitle dashboard-subtitle-compact mb-0' },
            'Executive Summary'
          )
        ),
        e(
          'div',
          { className: 'dashboard-hero-side' },
          e(
            'div',
            { className: 'hero-presence-card' },
            e('span', { className: 'presence-dot' }),
            e(
              'div',
              null,
              e('p', { className: 'hero-presence-label mb-1' }, usuario.rol),
              e('strong', { className: 'hero-presence-name d-block' }, usuario.correo || usuario.nombre),
              e('small', { className: 'hero-presence-date' }, hoy)
            )
          ),
          e(
            'button',
            {
              type: 'button',
              className: 'btn btn-primary btn-lg hero-primary-action',
              onClick: function () {
                window.dispatchEvent(new CustomEvent('dashboard:new-project'));
              }
            },
            '+ Nuevo Proyecto'
          )
        )
      ),
      e(
        'section',
        { className: 'dashboard-command-bar' },
        e(
          'div',
          { className: 'command-search-shell' },
          e('label', { className: 'command-label', htmlFor: 'dashboardQuickSearch' }, 'Buscar proyecto'),
          e('input', {
            id: 'dashboardQuickSearch',
            className: 'command-search-input',
            type: 'search',
            placeholder: 'Nombre, descripcion o responsable',
            value: filtros.busqueda || '',
            onChange: function (evento) {
              emitirFiltro({ busqueda: evento.target.value });
            }
          })
        ),
        e(
          'div',
          { className: 'command-pill-group', role: 'tablist', 'aria-label': 'Filtro de estado' },
          ['todos', 'activo', 'pausado', 'completado', 'cancelado'].map(function (estado) {
            var activo = (filtros.estado || 'todos') === estado;
            var etiqueta = estado === 'todos'
              ? 'Todos'
              : estado.charAt(0).toUpperCase() + estado.slice(1);
            return e(
              'button',
              {
                key: estado,
                type: 'button',
                className: 'command-pill' + (activo ? ' active' : ''),
                onClick: function () {
                  emitirFiltro({ estado: estado });
                }
              },
              etiqueta
            );
          })
        )
      ),
      e(
        'section',
        { className: 'dashboard-kpi-grid' },
        kpis.map(function (item) {
          return e(
            'article',
            { key: item.label, className: 'dashboard-kpi-card' },
            e('span', { className: 'kpi-label' }, item.label),
            e('strong', { className: 'kpi-value' }, item.value),
            e('p', { className: 'kpi-helper mb-0' }, item.helper)
          );
        })
      ),
      e(
        'section',
        { className: 'dashboard-insights-grid' },
        e(
          'article',
          { className: 'insight-card insight-card-primary' },
          e('p', { className: 'workspace-eyebrow mb-2' }, 'Foco operativo'),
          e('h3', { className: 'insight-title' }, 'Panorama de entregas'),
          e(
            'p',
            { className: 'insight-copy mb-0' },
            tareasCompletadas > 0
              ? 'El tablero ya registra ' + tareasCompletadas + ' tareas completadas. Usa este ritmo para detectar proyectos listos para cierre o demos.'
              : 'Todavia no hay tareas completadas registradas. Este panel se volvera mas util conforme el equipo actualice el flujo.'
          )
        ),
        e(
          'article',
          { className: 'insight-card' },
          e('p', { className: 'workspace-eyebrow mb-2' }, 'Carga del equipo'),
          e('h3', { className: 'insight-title' }, 'Quien tiene mas movimiento'),
          cargaTotalEquipo.length
            ? e(
                'div',
                { className: 'team-load-list' },
                cargaTotalEquipo.map(function (persona) {
                  return e(
                    'div',
                    { key: persona.nombre, className: 'team-load-item' },
                    e('span', { className: 'team-load-name' }, persona.nombre),
                    e('strong', { className: 'team-load-total' }, persona.total, ' tareas')
                  );
                })
              )
            : e('p', { className: 'insight-copy mb-0' }, 'Aun no hay suficientes tareas asignadas para construir un mapa de carga.')
        )
      )
    );
  }

  createRoot(rootElement).render(e(DashboardHeaderApp));
})();
