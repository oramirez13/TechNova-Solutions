$(document).ready(function () {
  $("#btnLogin").click(function () {
    const data = {
      cedula: $("#inputCedula").val(),
      correo: $("#inputEmail").val(),
      password: $("#inputPassword").val(),
    };

    $.ajax({
      url: "/login",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify(data),
      success: function () {
        window.location.href = "/dashboard";
      },
      error: function () {
        alert("Credenciales inválidas");
      },
    });
  });
});