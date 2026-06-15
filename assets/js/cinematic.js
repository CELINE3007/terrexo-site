(function () {
  'use strict';
  // NB : tout le moteur film est emballé dans un try/catch. Ainsi, si une
  // erreur survient ici, elle est isolée et n'interrompt PAS le script :
  // l'IIFE suivante (révélations au scroll des sections) s'exécute toujours.
  try {

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

  /* ---------- En-tête clair au-dessus des sections claires ---------- */
  var header = document.querySelector('.hd');
  var lightSection = document.getElementById('expertise');
  function headerLight() {
    if (!header || !lightSection) return;
    header.classList.toggle('on-light', lightSection.getBoundingClientRect().top <= 70);
  }

  /* ---------- Utilitaires ---------- */
  function clamp01(v){ return v < 0 ? 0 : v > 1 ? 1 : v; }
  function lerp(a,b,t){ return a + (b - a) * t; }
  function mix(a,b,t){ return [Math.round(lerp(a[0],b[0],t)),Math.round(lerp(a[1],b[1],t)),Math.round(lerp(a[2],b[2],t))]; }
  function smooth(t){ t = clamp01(t); return t*t*(3-2*t); }


  /* ============================================================
     MOTEUR FILM — une seule vidéo continue, scrub lissé.
     Un seul décodeur => fluidité réelle ; le scroll pilote le
     temps de lecture, lissé par easing image-par-image
     (la transition n'est jamais coupée : la vidéo va au bout).
     ============================================================ */
  var film  = document.getElementById('film');
  if (!film) { headerLight(); window.addEventListener('scroll', headerLight, {passive:true}); return; }

  var pin    = film.querySelector('.film-pin');
  var intro  = film.querySelector('.film-intro');
  var canvas = film.querySelector('.film-canvas');
  var caps   = Array.prototype.slice.call(film.querySelectorAll('.film-cap'));
  var bar    = film.querySelector('.film-bar');
  var hint   = film.querySelector('.film-hint');
  var prog   = film.querySelector('.cine-prog');
  var ctx    = canvas ? canvas.getContext('2d') : null;

  var NC = caps.length;          // nombre de légendes (réparties sur 0..1)
  // Course de scroll (en hauteurs d'écran). 10 morphes sur 3.5 écrans
  // => ~0.35 écran par morphe : un scroll fait défiler ~1 morphe (2 max),
  // pacing « snappy » demandé par le client (sans casser le scrub lissé).
  var SCROLL_VH = 3.5;
  var vh = window.innerHeight;

  var P = 0;                     // progression du scroll 0..1
  var targetF = 0;               // image cible pilotée par le scroll
  var curF = 0;                  // image courante lissée
  var running = false;
  var dots = [];

  /* ============================================================
     SÉQUENCE D'IMAGES (technique Apple/AirPods) :
     on précharge des frames HD (.webp) et on les DESSINE sur un
     <canvas> au scroll. Aucun décodage vidéo => aucun à-coup, et
     la qualité HD source est conservée (rendu net à tout DPR).
     ============================================================ */
  var FRAMES   = 200;            // 200 frames = 10 morphes × 20 (9 morphes + finale toit fermé 3/4), bornes propres
  var mobile   = window.matchMedia('(max-width:760px)').matches;
  var basePath = 'assets/img/film/' + (mobile ? 'm' : 'd') + '/';
  // cadrage : desktop = cover recadré vers le haut (44%) ; mobile = contain
  var FIT      = mobile ? 'contain' : 'cover';
  var FOCUS_Y  = 0.44;
  var imgs   = new Array(FRAMES);
  var loaded = 0;
  var ready  = false;
  var firstDrawn = false;
  var natW = 0, natH = 0;        // dimensions natives d'une frame

  function pad4(n){ n = String(n); while (n.length < 4) n = '0' + n; return n; }

  function preload(){
    for (var i = 0; i < FRAMES; i++){
      (function(idx){
        var im = new Image();
        im.decoding = 'async';
        im.onload = function(){
          loaded++;
          if (!natW){ natW = im.naturalWidth; natH = im.naturalHeight; }
          if (idx === 0){ ready = true; draw(0); }            // 1re frame prête : on peut afficher
        };
        im.onerror = function(){ loaded++; };
        im.src = basePath + pad4(idx + 1) + '.webp';
        imgs[idx] = im;
      })(i);
    }
  }

  /* ---------- Canvas : taille physique = CSS * DPR (plafonné à 2) ---------- */
  function sizeCanvas(){
    if (!canvas) return;
    var r = canvas.getBoundingClientRect();
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = Math.max(1, Math.round(r.width  * dpr));
    var h = Math.max(1, Math.round(r.height * dpr));
    if (canvas.width !== w || canvas.height !== h){
      canvas.width = w; canvas.height = h;
    }
  }

  /* ---------- Dessin d'une frame avec cadrage cover/contain ---------- */
  function draw(f){
    if (!ctx || !ready) return;
    var idx = Math.max(0, Math.min(FRAMES - 1, Math.round(f)));
    var im = imgs[idx];
    if (!im || !im.complete || !im.naturalWidth) return;
    var cw = canvas.width, ch = canvas.height;
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';   // redimensionnement HD net (sinon "low" par défaut)
    var iw = im.naturalWidth, ih = im.naturalHeight;
    var scale = (FIT === 'cover')
      ? Math.max(cw / iw, ch / ih)
      : Math.min(cw / iw, ch / ih);
    var dw = iw * scale, dh = ih * scale;
    var dx = (cw - dw) / 2;
    var dy = (FIT === 'cover') ? (ch - dh) * FOCUS_Y : (ch - dh) / 2;
    if (FIT === 'contain'){ ctx.fillStyle = '#05060a'; ctx.fillRect(0, 0, cw, ch); }
    ctx.drawImage(im, dx, dy, dw, dh);
    if (!firstDrawn){ firstDrawn = true; canvas.classList.add('is-drawn'); }
  }

  preload();

  /* ---------- Mise en page : hauteur de la section = course de scroll ---------- */
  function layout(){
    vh = window.innerHeight;
    film.style.height = Math.round(vh * (1 + SCROLL_VH)) + 'px';
    sizeCanvas();
    draw(curF);
  }

  function computeP(){
    var travel = film.offsetHeight - pin.offsetHeight;
    var rect = film.getBoundingClientRect();
    return travel > 0 ? clamp01(-rect.top / travel) : 0;
  }

  /* ---------- Légendes : NC réparties sur 0..1, fondu par proximité ---------- */
  function paintCaps(){
    var seg = NC > 1 ? 1 / (NC - 1) : 1;
    for (var i = 0; i < NC; i++){
      var center = i * seg;
      var op = clamp01(1 - Math.abs(P - center) / (seg * 0.62));
      if (i === 0 && P < 0.004) op = 1;
      if (i === NC - 1 && P > 0.996) op = 1;
      op = smooth(op);
      var c = caps[i];
      c.style.opacity = op.toFixed(3);
      c.style.transform = 'translateY(' + ((1 - op) * 26).toFixed(1) + 'px)';
      c.style.visibility = op <= 0.001 ? 'hidden' : 'visible';
    }
  }

  var curDot = -1;
  function paintDots(){
    if (!dots.length) return;
    var seg = NC > 1 ? 1 / (NC - 1) : 1;
    var act = Math.min(NC - 1, Math.round(P / seg));
    if (act !== curDot){ curDot = act; dots.forEach(function (d, k){ d.classList.toggle('on', k === act); }); }
  }

  /* ---------- Boucle d'easing : lisse curF -> targetF (clé de la fluidité) ---------- */
  var lastDrawn = -1;
  function tick(){
    var diff = targetF - curF;
    curF += diff * 0.18;
    if (Math.abs(diff) < 0.05){ curF = targetF; running = false; }
    var idx = Math.round(curF);
    if (idx !== lastDrawn){ lastDrawn = idx; draw(idx); }   // on ne redessine que si l'image change
    if (running) requestAnimationFrame(tick);
  }
  function ensureRunning(){ if (!running){ running = true; requestAnimationFrame(tick); } }

  /* ---------- Rendu sur scroll ---------- */
  function render(){
    P = computeP();
    targetF = P * (FRAMES - 1);
    if (bar)  bar.style.width = (P * 100).toFixed(2) + '%';
    if (hint) hint.style.opacity = P > 0.02 ? '0' : '1';
    // Voile de début : plein à l'arrêt, disparu après ~5 % de défilement.
    if (intro) intro.style.opacity = (P >= 0.05 ? 0 : 1 - P / 0.05).toFixed(3);
    paintCaps();
    paintDots();
    headerLight();
    ensureRunning();
  }

  var ticking = false;
  function onScroll(){ if (!ticking){ ticking = true; requestAnimationFrame(function (){ ticking = false; render(); }); } }
  function onResize(){ layout(); render(); }

  /* ---------- Pastilles de progression ---------- */
  function gotoSeg(i){
    var travel = film.offsetHeight - pin.offsetHeight;
    var seg = NC > 1 ? 1 / (NC - 1) : 1;
    window.scrollTo({ top: Math.round(film.offsetTop + i * seg * travel), behavior: 'smooth' });
  }
  if (prog){
    for (var d = 0; d < NC; d++){
      (function (idx){
        var b = document.createElement('button');
        b.type = 'button';
        b.setAttribute('aria-label', 'Scène ' + (idx + 1));
        b.addEventListener('click', function (){ gotoSeg(idx); });
        prog.appendChild(b); dots.push(b);
      })(d);
    }
  }

  /* ---------- Repli accessible : lecture libre, pas de scrubbing ---------- */
  function buildStatic(){
    docEl.classList.add('is-static');
    film.style.height = 'auto';
    caps.forEach(function (c, i){
      c.style.opacity = (i === 0) ? '1' : '0';
      c.style.transform = 'none';
      if (i !== 0) c.style.display = 'none';
    });
    headerLight();
    window.addEventListener('scroll', headerLight, { passive: true });
  }

  /* ---------- Démarrage ---------- */
  if (reduced){
    buildStatic();
  } else {
    layout();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onResize, { passive: true });
    window.addEventListener('load', function (){ layout(); render(); });
    render();
  }

  } catch (err) {
    if (window.console && console.error) console.error('Terrexo — moteur film :', err);
  }
})();

/* ============================================================
   Révélations au scroll + comparateur avant/après
   (IIFE indépendante : s'exécute même si le moteur film
    a fait un return anticipé)
   ============================================================ */
(function () {
  'use strict';
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* --- Révélation ---
     On garde l'observer même en reduced-motion : le CSS bascule alors sur un
     simple fondu (sans rotation), donc l'apparition reste visible et accessible. */
  var els = Array.prototype.slice.call(document.querySelectorAll('.reveal'));
  if (els.length) {
    if (!('IntersectionObserver' in window)) {
      els.forEach(function (e) { e.classList.add('in'); });
    } else {
      var io = new IntersectionObserver(function (ens) {
        ens.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
        });
      }, { rootMargin: '0px 0px -18% 0px', threshold: 0.12 });
      els.forEach(function (e) { io.observe(e); });
    }
  }

  /* --- Comparateur avant / après --- */
  Array.prototype.slice.call(document.querySelectorAll('[data-ba]')).forEach(function (ba) {
    var range = ba.querySelector('.ba-range');
    function set(v) { ba.style.setProperty('--pos', v + '%'); }
    if (range) {
      range.addEventListener('input', function () { set(range.value); });
      // glisser au survol/pointeur directement sur l'image
      var dragging = false;
      function fromEvent(clientX) {
        var r = ba.getBoundingClientRect();
        var v = Math.max(0, Math.min(100, ((clientX - r.left) / r.width) * 100));
        range.value = v; set(v);
      }
      ba.addEventListener('pointerdown', function (e) { dragging = true; fromEvent(e.clientX); });
      window.addEventListener('pointermove', function (e) { if (dragging) fromEvent(e.clientX); });
      window.addEventListener('pointerup', function () { dragging = false; });
      set(range.value);
    }
  });
})();
