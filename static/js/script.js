/* =========================================================
   script.js — TechNova Solutions
   Autenticación para login y registro
========================================================= */

$(document).ready(function () {
  var $vistaLogin = $('#vistaLogin');
  var $vistaRegistro = $('#vistaRegistro');
  var $formLogin = $('#formLogin');
  var $formRegistro = $('#formRegistro');

  function marcarInvalido($campo, idError, mensaje) {
    $campo.addClass('is-invalid').removeClass('is-valid');
    $('#' + idError).text(mensaje);
  }

  function marcarValido($campo, idError) {
    $campo.addClass('is-valid').removeClass('is-invalid');
    $('#' + idError).text('');
  }

  function limpiarEstadoCampo($campo, idError) {
    $campo.removeClass('is-invalid is-valid');
    $('#' + idError).text('');
  }

  function mostrarAlerta($alerta, tipo, mensaje) {
    $alerta
      .removeClass('d-none alert-success alert-danger')
      .addClass(tipo === 'success' ? 'alert-success' : 'alert-danger')
      .text(mensaje);
  }

  function ocultarAlerta($alerta) {
    $alerta.addClass('d-none').removeClass('alert-success alert-danger').text('');
  }

  function cambiarVista(mostrarRegistro) {
    ocultarAlerta($('#alertLogin'));
    ocultarAlerta($('#alertRegistro'));

    if (mostrarRegistro) {
      $vistaLogin.addClass('d-none');
      $vistaRegistro.removeClass('d-none');
      $('#regNombre').trigger('focus');
      return;
    }

    $vistaRegistro.addClass('d-none');
    $vistaLogin.removeClass('d-none');
    $('#loginEmail').trigger('focus');
  }

  function validarLogin() {
    var email = $('#loginEmail').val().trim();
    var password = $('#loginPassword').val().trim();
    var valido = true;

    if (!email) {
      marcarInvalido($('#loginEmail'), 'errLoginEmail', 'El correo es obligatorio.');
      valido = false;
    } else {
      marcarValido($('#loginEmail'), 'errLoginEmail');
    }

    if (!password) {
      marcarInvalido(
        $('#loginPassword'),
        'errLoginPassword',
        'La contraseña es obligatoria.'
      );
      valido = false;
    } else {
      marcarValido($('#loginPassword'), 'errLoginPassword');
    }

    return valido;
  }

  function validarRegistro() {
    var nombre = $('#regNombre').val().trim();
    var email = $('#regEmail').val().trim();
    var rol = $('#regRol').val();
    var password = $('#regPassword').val().trim();
    var valido = true;

    if (nombre.length < 3) {
      marcarInvalido($('#regNombre'), 'errRegNombre', 'Ingresa al menos 3 caracteres.');
      valido = false;
    } else {
      marcarValido($('#regNombre'), 'errRegNombre');
    }

    if (!email) {
      marcarInvalido($('#regEmail'), 'errRegEmail', 'El correo es obligatorio.');
      valido = false;
    } else {
      marcarValido($('#regEmail'), 'errRegEmail');
    }

    if (!rol) {
      marcarInvalido($('#regRol'), 'errRegRol', 'Selecciona un rol.');
      valido = false;
    } else {
      marcarValido($('#regRol'), 'errRegRol');
    }

    if (password.length < 6) {
      marcarInvalido(
        $('#regPassword'),
        'errRegPassword',
        'La contraseña debe tener al menos 6 caracteres.'
      );
      valido = false;
    } else {
      marcarValido($('#regPassword'), 'errRegPassword');
    }

    return valido;
  }

  if ($('#irARegistro').length && $('#irALogin').length) {
    $('#irARegistro').on('click', function (event) {
      event.preventDefault();
      cambiarVista(true);
    });

    $('#irALogin').on('click', function (event) {
      event.preventDefault();
      cambiarVista(false);
    });
  }

  $('#loginEmail, #loginPassword').on('input', function () {
    limpiarEstadoCampo($(this), this.id === 'loginEmail' ? 'errLoginEmail' : 'errLoginPassword');
    ocultarAlerta($('#alertLogin'));
  });

  $('#regNombre, #regEmail, #regRol, #regPassword').on('input change', function () {
    var errores = {
      regNombre: 'errRegNombre',
      regEmail: 'errRegEmail',
      regRol: 'errRegRol',
      regPassword: 'errRegPassword'
    };

    limpiarEstadoCampo($(this), errores[this.id]);
    ocultarAlerta($('#alertRegistro'));
  });

  if ($formLogin.length) {
    $formLogin.on('submit', function (event) {
      event.preventDefault();
      ocultarAlerta($('#alertLogin'));

      if (!validarLogin()) {
        return;
      }

      var $boton = $('#btnLogin');
      $boton.prop('disabled', true).text('Ingresando...');

      $.ajax({
        url: '/api/login',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
          correo: $('#loginEmail').val().trim(),
          password: $('#loginPassword').val().trim()
        })
      })
        .done(function () {
          window.location.assign('/dashboard');
        })
        .fail(function (xhr) {
          var mensaje =
            (xhr.responseJSON && xhr.responseJSON.mensaje) ||
            'No fue posible iniciar sesión.';
          mostrarAlerta($('#alertLogin'), 'error', mensaje);
        })
        .always(function () {
          $boton.prop('disabled', false).text('Ingresar');
        });
    });
  }

  if ($formRegistro.length) {
    $formRegistro.on('submit', function (event) {
      event.preventDefault();
      ocultarAlerta($('#alertRegistro'));

      if (!validarRegistro()) {
        return;
      }

      var $boton = $('#btnRegistrar');
      var datos = {
        nombre: $('#regNombre').val().trim(),
        correo: $('#regEmail').val().trim(),
        rol: $('#regRol').val(),
        password: $('#regPassword').val().trim()
      };

      $boton.prop('disabled', true).text('Registrando...');

      $.ajax({
        url: '/api/registro',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(datos)
      })
        .done(function (respuesta) {
          mostrarAlerta(
            $('#alertRegistro'),
            'success',
            respuesta.mensaje || 'Usuario registrado correctamente.'
          );

          $formRegistro.trigger('reset');
          $('#loginEmail').val(datos.correo);
          $('#loginPassword').val('');
          $('#regNombre, #regEmail, #regRol, #regPassword').removeClass('is-valid is-invalid');
          cambiarVista(false);
          mostrarAlerta(
            $('#alertLogin'),
            'success',
            'Cuenta creada. Ahora puedes iniciar sesión.'
          );
        })
        .fail(function (xhr) {
          var mensaje =
            (xhr.responseJSON && xhr.responseJSON.mensaje) ||
            'No fue posible completar el registro.';
          mostrarAlerta($('#alertRegistro'), 'error', mensaje);
        })
        .always(function () {
          $boton.prop('disabled', false).text('Registrarse');
        });
    });
  }
});
