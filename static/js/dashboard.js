/* =========================================================
   dashboard.js — TechNova Solutions
   Carga de proyectos y cierre de sesión
========================================================= */

$(document).ready(function () {
  var $contenedor = $('#proyectosContainer');
  var $modalProyecto = $('#modalProyecto');
  var $formProyecto = $('#formProyecto');
  var $usuarioNombre = $('#usuarioNombre');

  function escaparHtml(texto) {
    return $('<div>').text(texto || '').html();
  }

  function formatearFecha(valor) {
    if (!valor) {
      return 'Sin definir';
    }

    return valor;
  }

  function renderizarProyectos(proyectos) {
    if (!proyectos.length) {
      $contenedor.html(
        '<div class="col-12"><div class="alert alert-light border">Aun no hay proyectos registrados.</div></div>'
      );
      return;
    }

    var tarjetas = proyectos
      .map(function (proyecto) {
        return (
          '<div class="col-12 col-md-6 col-xl-4 mb-4">' +
            '<div class="card project-card">' +
              '<div class="card-body">' +
                '<h5 class="card-title">' + escaparHtml(proyecto.nombre) + '</h5>' +
                '<p class="card-text">' +
                  escaparHtml(proyecto.descripcion || 'Sin descripcion registrada.') +
                '</p>' +
                '<p class="project-meta mb-1"><strong>Estado:</strong> ' +
                  escaparHtml(proyecto.estado || 'pendiente') +
                '</p>' +
                '<p class="project-meta mb-1"><strong>Inicio:</strong> ' +
                  escaparHtml(formatearFecha(proyecto.fecha_inicio)) +
                '</p>' +
                '<p class="project-meta mb-0"><strong>Responsable:</strong> ' +
                  escaparHtml(proyecto.responsable_nombre || 'No asignado') +
                '</p>' +
              '</div>' +
            '</div>' +
          '</div>'
        );
      })
      .join('');

    $contenedor.html(tarjetas);
  }

  function cargarProyectos() {
    $contenedor.html(
      '<div class="col-12"><div class="alert alert-light border">Cargando proyectos...</div></div>'
    );

    $.getJSON('/api/proyectos')
      .done(function (respuesta) {
        renderizarProyectos(respuesta.proyectos || []);
      })
      .fail(function (xhr) {
        if (xhr.status === 401) {
          window.location.assign('/');
          return;
        }

        $contenedor.html(
          '<div class="col-12"><div class="alert alert-danger">No fue posible cargar los proyectos.</div></div>'
        );
      });
  }

  $('#btnNuevoProyecto').on('click', function () {
    $formProyecto.trigger('reset');
    $modalProyecto.modal('show');
  });

  $('#btnGuardarProyecto').on('click', function () {
    var nombre = $('#proyectoNombre').val().trim();
    var fechaInicio = $('#proyectoFechaInicio').val();

    if (!nombre || !fechaInicio) {
      window.alert('Completa el nombre y la fecha de inicio del proyecto.');
      return;
    }

    var $boton = $(this);
    $boton.prop('disabled', true).text('Guardando...');

    $.ajax({
      url: '/api/proyectos',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        nombre: nombre,
        descripcion: $('#proyectoDescripcion').val().trim(),
        fecha_inicio: fechaInicio,
        fecha_fin_estimada: $('#proyectoFechaFin').val() || null
      })
    })
      .done(function (respuesta) {
        $modalProyecto.modal('hide');
        cargarProyectos();
        window.alert(respuesta.mensaje || 'Proyecto creado correctamente.');
      })
      .fail(function (xhr) {
        if (xhr.status === 401) {
          window.location.assign('/');
          return;
        }

        var mensaje =
          (xhr.responseJSON && xhr.responseJSON.mensaje) ||
          'No fue posible guardar el proyecto.';
        window.alert(mensaje);
      })
      .always(function () {
        $boton.prop('disabled', false).text('Guardar');
      });
  });

  $('#btnLogout').on('click', function () {
    $.post('/api/logout')
      .always(function () {
        window.location.assign('/');
      });
  });

  $usuarioNombre.text($('body').data('usuarioNombre') || $usuarioNombre.text());
  cargarProyectos();
});
