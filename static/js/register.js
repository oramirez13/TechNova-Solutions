$(document).ready(function () {
  $("#formRegister").on("submit", function (event) {
    event.preventDefault();

    var $alerta = $("#alertRegister");
    var $boton = $(this).find('button[type="submit"]');
    const data = {
      nombre: $("#nombre").val().trim(),
      correo: $("#email").val().trim(),
      rol: "Developer",
      password: $("#password").val().trim(),
    };

    $alerta.addClass("d-none").removeClass("alert-success alert-danger").text("");
    $boton.prop("disabled", true).text("Registrando...");

    $.ajax({
      url: "/api/registro",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify(data),
      success: function (res) {
        $alerta
          .removeClass("d-none alert-danger")
          .addClass("alert-success")
          .text(res.mensaje || "Usuario registrado correctamente.");
        $("#formRegister").trigger("reset");
        window.setTimeout(function () {
          window.location.href = "/";
        }, 1200);
      },
      error: function (xhr) {
        var mensaje =
          (xhr.responseJSON && xhr.responseJSON.mensaje) ||
          "Error al registrar.";
        $alerta
          .removeClass("d-none alert-success")
          .addClass("alert-danger")
          .text(mensaje);
      },
      complete: function () {
        $boton.prop("disabled", false).text("Registrarse");
      },
    });
  });
});
