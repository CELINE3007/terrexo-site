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
     MOTEUR FILM
     ============================================================ */
  var film  = document.getElementById('film');
  if (!film) { headerLight(); window.addEventListener('scroll', headerLight, {passive:true}); return; }

  var pin    = film.querySelector('.film-pin');
  var layers = Array.prototype.slice.call(film.querySelectorAll('.film-layer'));
  var caps   = Array.prototype.slice.call(film.querySelectorAll('.film-cap'));
  var bar    = film.querySelector('.film-bar');
  var hint   = film.querySelector('.film-hint');
  var prog   = film.querySelector('.cine-prog');

  var videos = layers.map(function (l){ return l.querySelector('video'); });
  var lyImgs = layers.map(function (l){ return l.querySelector('.ly-img'); });
  var houses = layers.map(function (l){ return l.querySelector('.ly-house'); });

  var N = layers.length;
  var w = 1 / N;                 // largeur d'un segment dans la progression 0..1
  var band = 0.55 * w;           // zone de fondu enchaîné autour de chaque frontière
  var half = band / 2;
  var SEG  = 0.92;               // course de scroll par segment (en hauteurs d'écran)

  var vh = window.innerHeight;

  /* ---------- Média : chargement différé + amorçage décodeur ---------- */
  var mediaLoaded = false;
  function loadAll(){
    if (mediaLoaded) return;
    mediaLoaded = true;
    layers.forEach(function (l, i){
      var v = videos[i];
      if (v && v.dataset.src && !v.src){
        v.preload = 'auto';
        v.src = v.dataset.src;
        v.load();
        // amorçage : on lance puis on met en pause pour forcer le décodage
        // (indispensable pour un scrubbing fluide, notamment iOS)
        var pr = v.play();
        if (pr && pr.then) pr.then(function(){ v.pause(); }).catch(function(){});
        else { try { v.pause(); } catch(e){} }
      }
      var im = lyImgs[i];
      if (im && im.dataset.bg && !im.style.backgroundImage){
        im.style.backgroundImage = "url('" + im.dataset.bg + "')";
      }
    });
  }

  /* ---------- Mise en page : hauteur de la section = course de scroll ---------- */
  function layout(){
    vh = window.innerHeight;
    film.style.height = Math.round(vh + N * SEG * vh) + 'px';
  }

  /* ---------- Boucle de rendu ---------- */
  var ticking = false;
  var curDot = -1;

  function update(){
    ticking = false;
    var rect = film.getBoundingClientRect();
    var travel = film.offsetHeight - pin.offsetHeight;
    var P = travel > 0 ? clamp01(-rect.top / travel) : 0;

    // charge les médias dès qu'on approche du film
    if (!mediaLoaded && rect.top < vh * 1.4 && rect.bottom > -vh * 0.4) loadAll();

    for (var i = 0; i < N; i++){
      var Lb = i * w, Rb = (i + 1) * w;

      // opacité trapézoïdale -> fondu enchaîné avec les voisins
      var lr = (i === 0)     ? 1 : clamp01((P - (Lb - half)) / band);
      var rr = (i === N - 1) ? 1 : clamp01(((Rb + half) - P) / band);
      var op = Math.min(lr, rr);

      var L = layers[i];
      L.style.opacity = op.toFixed(3);
      L.style.visibility = op <= 0.001 ? 'hidden' : 'visible';

      var lp = clamp01((P - Lb) / w); // progression locale 0..1 dans le segment

      // vidéo : on « scrube » le temps de lecture avec le scroll
      var v = videos[i];
      if (v && op > 0.02 && v.readyState >= 1 && v.duration){
        var t = lp * (v.duration - 0.04);
        if (Math.abs(v.currentTime - t) > 0.033){
          try { if (v.fastSeek) v.fastSeek(t); else v.currentTime = t; } catch (e){}
        }
      }

      // image fixe : léger mouvement de caméra (Ken Burns)
      var im = lyImgs[i];
      if (im) im.style.transform = 'scale(' + (1.085 - 0.085 * lp).toFixed(4) + ') translateY(' + ((lp - 0.5) * -2).toFixed(2) + '%)';

      // maison détourée : douce respiration + léger zoom
      var ho = houses[i];
      if (ho) ho.style.transform = 'scale(' + (1.0 + 0.06 * lp).toFixed(4) + ') translateY(' + ((0.5 - lp) * -1.4).toFixed(2) + '%)';

      // légende : pic au centre du segment
      var cap = caps[i];
      if (cap){
        var capOp = clamp01(1 - Math.abs(lp - 0.5) / 0.46);
        if (i === 0 && P < 0.001) capOp = 1;
        capOp = smooth(capOp);
        cap.style.opacity = capOp.toFixed(3);
        cap.style.transform = 'translateY(' + ((1 - capOp) * 24).toFixed(1) + 'px)';
      }
    }

    if (bar)  bar.style.width = (P * 100).toFixed(2) + '%';
    if (hint) hint.style.opacity = P > 0.03 ? '0' : '1';

    var act = Math.min(N - 1, Math.floor(P / w + 1e-6));
    if (dots.length && act !== curDot){
      curDot = act;
      dots.forEach(function (d, k){ d.classList.toggle('on', k === act); });
    }

    neon(P);
    headerLight();
  }

  function onScroll(){ if (!ticking){ ticking = true; requestAnimationFrame(update); } }
  function onResize(){ layout(); update(); }

  /* ---------- Pastilles de progression ---------- */
  var dots = [];
  function gotoSeg(i){
    var travel = film.offsetHeight - pin.offsetHeight;
    var targetP = (i + 0.5) * w;
    window.scrollTo({ top: Math.round(film.offsetTop + targetP * travel), behavior: 'smooth' });
  }
  if (prog){
    for (var d = 0; d < N; d++){
      (function (idx){
        var b = document.createElement('button');
        b.type = 'button';
        b.setAttribute('aria-label', 'Scène ' + (idx + 1));
        b.addEventListener('click', function (){ gotoSeg(idx); });
        prog.appendChild(b); dots.push(b);
      })(d);
    }
  }

  /* ---------- Repli accessible : empilement simple, pas de scrubbing ---------- */
  function buildStatic(){
    docEl.classList.add('is-static');
    film.style.height = 'auto';
    layers.forEach(function (l, i){
      var cap = caps[i];
      if (cap){ l.appendChild(cap); cap.style.opacity = '1'; cap.style.transform = 'none'; }
      var v = videos[i];
      if (v && v.dataset.src){ v.preload = 'metadata'; v.src = v.dataset.src; v.setAttribute('controls', ''); v.removeAttribute('loop'); }
      var im = lyImgs[i];
      if (im && im.dataset.bg){ im.style.backgroundImage = "url('" + im.dataset.bg + "')"; }
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
    window.addEventListener('load', function (){ layout(); update(); });
    update();
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
