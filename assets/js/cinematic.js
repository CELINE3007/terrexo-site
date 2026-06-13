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

  /* ---------- Néon de fond qui évolue avec la progression du film ---------- */
  var rootStyle = docEl.style;
  var neonKeys = [
    {at:0.00, c1:[224,64,196], c2:[58,118,255], p1:[12,16], p2:[88,84]},
    {at:0.50, c1:[150,70,255], c2:[40,200,235], p1:[10,86], p2:[90,14]},
    {at:1.00, c1:[255,70,150], c2:[60,120,255], p1:[14,12], p2:[86,88]}
  ];
  function neon(p){
    var i = 0; while (i < neonKeys.length-1 && p > neonKeys[i+1].at) i++;
    var a = neonKeys[i], b = neonKeys[Math.min(i+1, neonKeys.length-1)];
    var t = b.at > a.at ? (p - a.at)/(b.at - a.at) : 0;
    var c1 = mix(a.c1,b.c1,t), c2 = mix(a.c2,b.c2,t);
    rootStyle.setProperty('--c1', c1.join(','));
    rootStyle.setProperty('--c2', c2.join(','));
    rootStyle.setProperty('--p1x', lerp(a.p1[0],b.p1[0],t).toFixed(1)+'%');
    rootStyle.setProperty('--p1y', lerp(a.p1[1],b.p1[1],t).toFixed(1)+'%');
    rootStyle.setProperty('--p2x', lerp(a.p2[0],b.p2[0],t).toFixed(1)+'%');
    rootStyle.setProperty('--p2y', lerp(a.p2[1],b.p2[1],t).toFixed(1)+'%');
  }

  /* ============================================================
     MOTEUR FILM — une seule vidéo continue, scrub lissé.
     Un seul décodeur => fluidité réelle ; le scroll pilote le
     temps de lecture, lissé par easing image-par-image
     (la transition n'est jamais coupée : la vidéo va au bout).
     ============================================================ */
  var film  = document.getElementById('film');
  if (!film) { headerLight(); window.addEventListener('scroll', headerLight, {passive:true}); return; }

  var pin   = film.querySelector('.film-pin');
  var video = film.querySelector('.film-video');
  var caps  = Array.prototype.slice.call(film.querySelectorAll('.film-cap'));
  var bar   = film.querySelector('.film-bar');
  var hint  = film.querySelector('.film-hint');
  var prog  = film.querySelector('.cine-prog');

  var NC = caps.length;          // nombre de légendes (réparties sur 0..1)
  var SCROLL_VH = 6.5;           // course de scroll (en hauteurs d'écran)
  var vh = window.innerHeight;

  var dur = 0;                   // durée de la vidéo (s)
  var P = 0;                     // progression du scroll 0..1
  var targetT = 0;               // temps cible piloté par le scroll
  var curT = 0;                  // temps courant lissé
  var ready = false;
  var running = false;
  var dots = [];

  /* ---------- Amorçage de la vidéo ---------- */
  function onMeta(){
    dur = (video.duration && isFinite(video.duration)) ? video.duration : 36;
    ready = true;
  }
  if (video){
    if (video.readyState >= 1) onMeta();
    video.addEventListener('loadedmetadata', onMeta);
    // play->pause muet : force le décodage initial (indispensable iOS/Safari)
    var pr = video.play && video.play();
    if (pr && pr.then) pr.then(function(){ try{ video.pause(); }catch(e){} }).catch(function(){});
  }

  /* ---------- Mise en page : hauteur de la section = course de scroll ---------- */
  function layout(){
    vh = window.innerHeight;
    film.style.height = Math.round(vh * (1 + SCROLL_VH)) + 'px';
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

  /* ---------- Boucle d'easing : lisse curT -> targetT (clé de la fluidité) ---------- */
  function tick(){
    // on ne laisse jamais la vidéo se lire seule : seul le scroll pilote le temps
    if (video && !video.paused){ try { video.pause(); } catch (e){} }
    var diff = targetT - curT;
    curT += diff * 0.16;
    if (Math.abs(diff) < 0.004){ curT = targetT; running = false; }
    if (ready && video && Math.abs(video.currentTime - curT) > 0.012){
      try { video.currentTime = curT; } catch (e){}
    }
    if (running) requestAnimationFrame(tick);
  }
  function ensureRunning(){ if (!running){ running = true; requestAnimationFrame(tick); } }

  /* ---------- Rendu sur scroll ---------- */
  function render(){
    P = computeP();
    targetT = P * ((dur || 36) - 0.05);
    if (bar)  bar.style.width = (P * 100).toFixed(2) + '%';
    if (hint) hint.style.opacity = P > 0.02 ? '0' : '1';
    paintCaps();
    paintDots();
    neon(P);
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
    if (video){ video.setAttribute('controls', ''); video.muted = true; }
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
})();

/* ============================================================
   Révélations au scroll + comparateur avant/après
   (IIFE indépendante : s'exécute même si le moteur film
    a fait un return anticipé)
   ============================================================ */
(function () {
  'use strict';
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* --- Révélation --- */
  var els = Array.prototype.slice.call(document.querySelectorAll('.reveal'));
  if (els.length) {
    if (!('IntersectionObserver' in window) || reduced) {
      els.forEach(function (e) { e.classList.add('in'); });
    } else {
      var io = new IntersectionObserver(function (ens) {
        ens.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
        });
      }, { rootMargin: '0px 0px -10% 0px', threshold: 0.12 });
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
