// Tema del sitio: light (por defecto) | cafe | dark — persistido en localStorage.
// Se carga en el <head> sin defer para aplicar el tema antes del primer render (sin parpadeo).
(function () {
    var theme = 'light';
    try { theme = localStorage.getItem('lrp-theme') || 'light'; } catch (e) { /* modo privado */ }
    document.documentElement.setAttribute('data-theme', theme);

    function mark(t) {
        var btns = document.querySelectorAll('[data-theme-btn]');
        for (var i = 0; i < btns.length; i++) {
            btns[i].classList.toggle('active', btns[i].getAttribute('data-theme-btn') === t);
        }
    }

    function setTheme(t) {
        document.documentElement.setAttribute('data-theme', t);
        try { localStorage.setItem('lrp-theme', t); } catch (e) { /* modo privado */ }
        mark(t);
    }

    document.addEventListener('DOMContentLoaded', function () {
        var btns = document.querySelectorAll('[data-theme-btn]');
        for (var i = 0; i < btns.length; i++) {
            btns[i].addEventListener('click', function () {
                setTheme(this.getAttribute('data-theme-btn'));
            });
        }
        mark(document.documentElement.getAttribute('data-theme') || 'light');
    });
})();
