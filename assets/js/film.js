(function () {
  'use strict';

  var docEl = document.documentElement;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Année ---------- */
  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();

  /* ---------- Formulaire -> mailto (pas de backend) ---------- */
  var form = document.getElementById('devis-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var f = form.elements;
      var nom = (f.nom.value || '').trim();
      var email = (f.email.value || '').trim();
      var tel = (f.tel.value || '').trim();
      var msg = (f.message.value || '').trim();
      if (!nom || !email) { (nom ? f.email : f.nom).focus(); return; }
      var body =
        'Nom : ' + nom + '\n' +
        'E-mail : ' + email + '\n' +
        'Téléphone : ' + tel + '\n\n' +
        'Mon projet :\n' + msg + '\n';
      var href = 'mailto:info@terrexo.lu' +
        '?subject=' + encodeURIComponent('Étude gratuite — ' + nom) +
        '&body=' + encodeURIComponent(body);
      window.location.href = href;
    });
  }

  /* ---------- En-tête clair sur les sections fond clair ---------- */
  var header = document.querySelector('.hd');
  var lightSection = document.getElementById('expertise');

  /* ---------- Repli accessible (sans mouvement) ---------- */
  if (reduced) {
    docEl.classList.add('reduced');
    var v0 = document.querySelector('.fr video');
    if (v0) v0.setAttribute('controls', '');     // l'utilisateur lance la vidéo lui-même
    bindHeaderLight();
    window.addEventListener('scroll', bindHeaderLight, { passive: true });
    return;
  }

  /* ============================================================
     Moteur film : une seule progression --p (0→1) sur toute la
     scène. Chaque frame possède une fenêtre d'opacité centrée ;
     les frames voisines se fondent → la maison se transforme
     en place. La caméra ne s'arrête jamais (push-in / push-out).
     ============================================================ */
  var film = document.getElementById('film');
  var stage = film ? film.querySelector('.film-stage') : null;
  var frames = film ? Array.prototype.slice.call(film.querySelectorAll('.fr')) : [];
  var prog = film ? film.querySelector('.film-prog') : null;
  var hint = film ? film.querySelector('.film-hint') : null;
  var video = film ? film.querySelector('video') : null;

  if (!film || frames.length === 0) { bindHeaderLight(); return; }

  var N = frames.length;
  var seg = 1 / (N - 1);               // distance entre 2 centres de frame
  var imgs = frames.map(function (fr) { return fr.querySelector('.fr-img'); });
  var caps = frames.map(function (fr) { return fr.querySelector('.cap'); });
  var cams = frames.map(function (fr) { return fr.getAttribute('data-cam') || 'in'; });
  var capModes = caps.map(function (c) { return c ? (c.getAttribute('data-cap') || 'mid') : null; });

  var vh = window.innerHeight;
  var ticking = false;
  var videoOn = false;

  function clamp01(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function smooth(t) { t = clamp01(t); return t * t * (3 - 2 * t); }   // smoothstep

  function update() {
    ticking = false;
    var rect = film.getBoundingClientRect();
    var travel = film.offsetHeight - vh;                  // distance sticky
    var p = travel > 0 ? clamp01((-rect.top) / travel) : 0;

    for (var i = 0; i < N; i++) {
      var center = i * seg;
      var d = (p - center) / seg;                          // -1 .. +1 dans la fenêtre
      var op = clamp01(1 - Math.abs(d));                   // pic au centre, fond aux voisins
      op = smooth(op);
      frames[i].style.opacity = op.toFixed(3);

      // progression locale 0 (entrée) → 1 (sortie) pour la caméra
      var lp = clamp01((d + 1) / 2);

      // caméra : toujours en mouvement
      var img = imgs[i];
      if (img) {
        var scale, ty;
        if (cams[i] === 'still') { scale = 1.0; ty = 0; }
        else if (cams[i] === 'out') { scale = 1.085 - 0.065 * lp; ty = (lp - 0.5) * -1.6; }
        else { scale = 1.02 + 0.065 * lp; ty = (lp - 0.5) * 1.6; }   // 'in'
        img.style.transform = 'scale(' + scale.toFixed(4) + ') translateY(' + ty.toFixed(2) + '%)';
      }

      // légende : visible quand la frame domine, avec léger lever
      var cap = caps[i];
      if (cap) {
        var capOp;
        if (capModes[i] === 'early') capOp = clamp01((0.55 - lp) * 3) * smooth(op);
        else capOp = clamp01((op - 0.45) * 2.6);
        cap.style.opacity = capOp.toFixed(3);
        cap.style.transform = 'translateY(' + ((1 - smooth(capOp)) * 26).toFixed(1) + 'px)';
      }
    }

    if (prog) prog.style.width = (p * 100).toFixed(2) + '%';
    if (hint) hint.style.opacity = p > 0.04 ? '0' : '1';

    // vidéo : ne joue que dans sa fenêtre (≈ avant-dernière frame)
    if (video) {
      var vi = frames.indexOf(video.parentNode);
      var inWindow = Math.abs((p - vi * seg) / seg) < 0.9;
      if (inWindow && !videoOn) { videoOn = true; var pr = video.play(); if (pr && pr.catch) pr.catch(function () {}); }
      else if (!inWindow && videoOn) { videoOn = false; video.pause(); }
    }

    bindHeaderLight();
  }

  function bindHeaderLight() {
    if (header && lightSection) {
      header.classList.toggle('on-light', lightSection.getBoundingClientRect().top <= 72);
    }
  }

  function onScroll() {
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  }
  function onResize() { vh = window.innerHeight; update(); }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onResize, { passive: true });
  update();
  window.addEventListener('load', update);
})();
