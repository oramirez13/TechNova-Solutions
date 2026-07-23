$(document).ready(function () {
  window.csrfToken = document.body.getAttribute('data-csrf-token') || '';

  $(document).on('click', '.js-logout', function () {
    $.ajax({
      url: '/api/logout',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ csrf_token: window.csrfToken })
    }).always(function () {
      window.location.assign('/');
    });
  });
});
