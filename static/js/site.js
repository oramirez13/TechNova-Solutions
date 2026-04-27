$(document).ready(function () {
  $(document).on('click', '.js-logout', function () {
    $.post('/api/logout').always(function () {
      window.location.assign('/');
    });
  });
});
