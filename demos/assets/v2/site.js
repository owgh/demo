/* Demo sites v2. Reads the page's #site-data JSON and builds the working parts:
   the hero hook, services or menu, gift cards, hours and FAQ. No libraries. */
(function () {
  'use strict';
  var root = document.documentElement;
  root.classList.add('js');
  var S;
  try { S = JSON.parse(document.getElementById('site-data').textContent); }
  catch (e) { root.classList.add('is-ready'); return; }

  /* ── Helpers ─────────────────────────────────────────────────────────── */
  var NS = 'http://www.w3.org/2000/svg';
  var LIVE = !!S.live, LINKS = S.links || {};
  function demoText(demo, live) { return LIVE ? (live || null) : demo; }
  function send(kind, fields) {
    if (!LIVE || !S.form) return Promise.resolve();
    var body = { _subject: kind + ' from your website', _template: 'table' };
    Object.keys(fields).forEach(function (k) { if (fields[k] != null && fields[k] !== '') body[k] = String(fields[k]); });
    return fetch(S.form, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json().catch(function () { return {}; }); })
      .then(function (res) { if (res && (res.success === false || res.success === 'false')) throw new Error(res.message || 'Not sent'); });
  }
  function sendFail() { return 'That didn\u2019t go through. Please call us' + (S.phone ? ' at ' + S.phone : '') + '.'; }
  function openLink(url) { window.open(url, '_blank', 'noopener'); }
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function build(el, props, kids) {
    if (props) Object.keys(props).forEach(function (k) {
      var v = props[k];
      if (v == null || v === false) return;
      if (k === 'text') el.textContent = v;
      else if (k.slice(0, 2) === 'on' && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v);
      else el.setAttribute(k, v === true ? '' : v);
    });
    (function add(list) {
      list.forEach(function (kid) {
        if (kid == null || kid === false) return;
        if (Array.isArray(kid)) return add(kid);
        el.appendChild(kid.nodeType ? kid : document.createTextNode(String(kid)));
      });
    })(kids);
    return el;
  }
  function h(tag, props) { return build(document.createElement(tag), props, [].slice.call(arguments, 2)); }
  function s(tag, props) { return build(document.createElementNS(NS, tag), props, [].slice.call(arguments, 2)); }
  function add(el) { return build(el, null, [].slice.call(arguments, 1)); }
  function money(n, cents) {
    var d = cents != null ? cents : (n % 1 ? 2 : 0);
    return '$' + Number(n).toLocaleString('en-CA', { minimumFractionDigits: d, maximumFractionDigits: d });
  }
  function priceLabel(p) { return p === 0 ? 'Free' : p == null ? (S.hook === 'estimate' ? 'Quote' : 'Ask us') : money(p); }
  function minsLabel(m) {
    if (!m) return '';
    if (m < 60) return m + ' min';
    var hr = Math.floor(m / 60), mn = m % 60;
    return hr + ' h' + (mn ? ' ' + mn + ' min' : '');
  }
  function num(n) { return Number(n).toLocaleString('en-CA'); }
  function hash(str) { var x = 2166136261; for (var i = 0; i < str.length; i++) { x ^= str.charCodeAt(i); x = Math.imul(x, 16777619); } return x >>> 0; }
  function rand(key) {
    var t = (hash(S.slug + '|' + key) + 0x6d2b79f5) | 0;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  var DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var DOW_LONG = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var MON_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  function sameDay(a, b) { return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate(); }
  function dayKey(d) { return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }
  function fmtTime(m) { var hr = Math.floor(m / 60), mn = m % 60, ap = hr >= 12 ? 'pm' : 'am', h12 = hr % 12 || 12; return mn ? h12 + ':' + (mn < 10 ? '0' : '') + mn + ' ' + ap : h12 + ' ' + ap; }
  function fmtDay(d) {
    var today = new Date(), tmr = new Date(); tmr.setDate(today.getDate() + 1);
    if (sameDay(d, today)) return 'Today';
    if (sameDay(d, tmr)) return 'Tomorrow';
    return DOW[d.getDay()] + ' ' + MON[d.getMonth()] + ' ' + d.getDate();
  }
  function longDay(d) { return DOW_LONG[d.getDay()] + ', ' + MON_LONG[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear(); }
  function nextDays(n) {
    var out = [], t = new Date(); t.setHours(0, 0, 0, 0);
    for (var i = 0; i < n; i++) { var d = new Date(t); d.setDate(t.getDate() + i); out.push(d); }
    return out;
  }
  function hoursOn(d) {
    for (var i = 0; i < S.hours.length; i++) if (S.hours[i].days.indexOf(d.getDay()) > -1) return S.hours[i].open == null ? null : S.hours[i];
    return null;
  }
  function slots(d, dur) {
    var hrs = hoursOn(d); if (!hrs) return [];
    var out = [], open = hrs.open * 60, close = hrs.close * 60, len = Math.max(dur || 30, 30);
    var now = new Date(), cut = sameDay(d, now) ? now.getHours() * 60 + now.getMinutes() + 60 : -1;
    for (var t = open; t + len <= close; t += 30) {
      if (t < cut) continue;
      if (!LIVE && rand(dayKey(d) + ':' + t) < 0.42) continue;
      out.push(t);
    }
    return out;
  }
  function nextOpening(dur) {
    var days = nextDays(14);
    for (var i = 0; i < days.length; i++) { var sl = slots(days[i], dur); if (sl.length) return { day: days[i], time: sl[0] }; }
    return null;
  }
  function tween(from, to, ms, fn) {
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce || from === to) return fn(to);
    var t0 = performance.now();
    (function step(t) {
      var k = Math.min(1, (t - t0) / ms), e = 1 - Math.pow(1 - k, 3);
      fn(from + (to - from) * e);
      if (k < 1) requestAnimationFrame(step);
    })(t0);
  }
  function cardHead(title, note) {
    return h('div', { class: 'card-head' }, h('p', { class: 'card-title' }, title), note ? h('p', { class: 'card-note' }, note) : null);
  }
  function stepLbl(n, text) { return h('p', { class: 'step-lbl' }, h('span', { class: 'n', 'aria-hidden': 'true' }, n), text); }
  function ownerNote(text) { return LIVE ? null : h('p', { class: 'owner-note' }, text); }
  function tickIcon() {
    return h('span', { class: 'tick', 'aria-hidden': 'true' },
      s('svg', { viewBox: '0 0 24 24' }, s('path', { d: 'M5 12.5l4.5 4.5L19 7.5', fill: 'none', stroke: 'currentColor', 'stroke-width': '2.6', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })));
  }
  function radio(el, on) { el.setAttribute('role', 'radio'); el.setAttribute('aria-checked', on ? 'true' : 'false'); return el; }
  function firstName(n) { return (n || '').trim().split(/\s+/)[0] || ''; }
  function scrollToEl(el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }

  /* ── Sheet (dialog) ──────────────────────────────────────────────────── */
  var sheet = $('#sheet'), sheetBody = $('[data-mount="sheet"]'), sheetTitle = $('#sheet-title');
  function openSheet(title, fill) {
    sheetTitle.textContent = title;
    sheetBody.replaceChildren();
    fill(sheetBody);
    if (!sheet.open) { if (sheet.showModal) sheet.showModal(); else sheet.setAttribute('open', ''); }
  }
  function closeSheet() { if (sheet.close) sheet.close(); else sheet.removeAttribute('open'); }
  if (sheet) sheet.addEventListener('click', function (e) { if (e.target === sheet || e.target.closest('[data-close]')) closeSheet(); });

  /* ── Calendar file ───────────────────────────────────────────────────── */
  function downloadICS(title, day, startMin, mins) {
    function stamp(d, m) {
      var x = new Date(d); x.setHours(0, m, 0, 0);
      function p(n) { return (n < 10 ? '0' : '') + n; }
      return x.getFullYear() + p(x.getMonth() + 1) + p(x.getDate()) + 'T' + p(x.getHours()) + p(x.getMinutes()) + '00';
    }
    function esc(t) { return String(t).replace(/([,;\\])/g, '\\$1'); }
    var now = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+/, '');
    var ics = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//' + esc(S.name) + '//Booking//EN', 'BEGIN:VEVENT',
      'UID:' + Date.now() + '@' + S.slug, 'DTSTAMP:' + now, 'DTSTART:' + stamp(day, startMin), 'DTEND:' + stamp(day, startMin + (mins || 30)),
      'SUMMARY:' + esc(title + ' at ' + S.name), 'LOCATION:' + esc(S.address), 'END:VEVENT', 'END:VCALENDAR'].join('\r\n');
    var a = h('a', { href: URL.createObjectURL(new Blob([ics], { type: 'text/calendar' })), download: S.slug + '-booking.ics' });
    document.body.appendChild(a); a.click(); a.remove();
  }

  /* ── Booking flow (inline or in the sheet) ───────────────────────────── */
  var PET_ICONS = {
    Dog: 'M7 4c-2 0-4 3-4 6 0 1.5 1 2 2 1.6V14a7 7 0 0 0 14 0v-2.4c1 .4 2-.1 2-1.6 0-3-2-6-4-6-1.6 0-2.4 1.2-3 2.2a7 7 0 0 0-4 0C9.4 5.2 8.6 4 7 4zm2.5 8a1.2 1.2 0 1 1 0 2.4 1.2 1.2 0 0 1 0-2.4zm5 0a1.2 1.2 0 1 1 0 2.4 1.2 1.2 0 0 1 0-2.4zM12 15.5l1.4 1.2c-.4.6-.9.8-1.4.8s-1-.2-1.4-.8z',
    Cat: 'M4 3l4 4.2a8 8 0 0 1 8 0L20 3v8.5A8 8 0 0 1 4 11.5zm5.5 8.5a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4zm5 0a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4zM12 15.6l1.2 1c-.3.4-.7.6-1.2.6s-.9-.2-1.2-.6z',
    Other: 'M12 13c-2.8 0-5.5 2.6-5.5 5 0 1.5 1.2 2 2.4 2 1.3 0 2-.6 3.1-.6s1.8.6 3.1.6c1.2 0 2.4-.5 2.4-2 0-2.4-2.7-5-5.5-5zM6 8.5a2 2.5 0 1 1 0 5 2 2.5 0 0 1 0-5zm12 0a2 2.5 0 1 1 0 5 2 2.5 0 0 1 0-5zM9.5 3.5a2 2.5 0 1 1 0 5 2 2.5 0 0 1 0-5zm5 0a2 2.5 0 1 1 0 5 2 2.5 0 0 1 0-5z'
  };

  function Booking(mount, opts) {
    opts = opts || {};
    var list = opts.services || S.services;
    var st = { pet: null, svc: opts.svc != null ? opts.svc : (list.length === 1 ? 0 : null), staff: S.staff ? S.staff[0] : null,
      day: opts.day || null, time: opts.time != null ? opts.time : null, name: '', phone: '', note: opts.note || '', done: false, err: '' };
    var needPet = !!S.pets && !opts.skipPet;
    var shown = 0, dayScroll = 0;

    function render(focusSel) {
      var strip = $('.days', mount); if (strip) dayScroll = strip.scrollLeft;
      mount.replaceChildren();
      if (opts.title) mount.appendChild(cardHead(opts.title, opts.note === undefined ? demoText('Sample services and prices', 'Pick a time that suits you') : null));
      if (st.done) { mount.appendChild(done()); shown = 0; return; }
      var blocks = [], n = 0;
      if (needPet) { blocks.push([stepLbl(++n, 'Who is coming in?'), pets()]); }
      if (!needPet || st.pet) {
        if (!opts.lockSvc) blocks.push([stepLbl(++n, opts.svcLabel || 'Choose a service'), services()]);
        if (st.svc != null) {
          if (S.staff) blocks.push([stepLbl(++n, 'With'), staff()]);
          blocks.push([stepLbl(++n, 'Pick a day'), days()]);
          if (st.day) {
            blocks.push([stepLbl(++n, 'Pick a time'), times()]);
            if (st.time != null) blocks.push([stepLbl(++n, 'Your details'), details()]);
          }
        }
      }
      blocks.forEach(function (b, i) {
        var wrap = h('div', { class: i >= shown && shown > 0 ? 'enter' : null }, b);
        mount.appendChild(wrap);
      });
      shown = blocks.length;
      var s2 = $('.days', mount); if (s2) s2.scrollLeft = dayScroll;
      if (focusSel) { var f = $(focusSel, mount); if (f) f.focus({ preventScroll: true }); }
    }
    function pets() {
      return h('div', { class: 'pets', role: 'radiogroup', 'aria-label': 'Pet' }, ['Dog', 'Cat', 'Other'].map(function (p) {
        return radio(h('button', { type: 'button', class: 'pet', onclick: function () { st.pet = p; render(); } },
          s('svg', { viewBox: '0 0 24 24', 'aria-hidden': 'true' }, s('path', { d: PET_ICONS[p], fill: 'currentColor' })), p), st.pet === p);
      }));
    }
    function services() {
      return h('div', { class: 'bk-svcs', role: 'radiogroup', 'aria-label': 'Service' }, list.map(function (x, i) {
        return radio(h('button', { type: 'button', class: 'bk-svc', onclick: function () { st.svc = i; st.time = null; render(); } },
          h('b', null, x.name), h('span', { class: 'p' }, priceLabel(x.price)), h('small', null, minsLabel(x.mins) || x.desc || '')), st.svc === i);
      }));
    }
    function staff() {
      return h('div', { class: 'chips', role: 'radiogroup', 'aria-label': 'Staff' }, S.staff.map(function (p) {
        return radio(h('button', { type: 'button', class: 'chip', onclick: function () { st.staff = p; render(); } }, p), st.staff === p);
      }));
    }
    function days() {
      return h('div', { class: 'days', role: 'radiogroup', 'aria-label': 'Day' }, nextDays(14).map(function (d) {
        var open = slots(d, list[st.svc].mins).length > 0;
        return radio(h('button', { type: 'button', class: 'day', disabled: !open, 'aria-label': DOW_LONG[d.getDay()] + ' ' + MON_LONG[d.getMonth()] + ' ' + d.getDate() + (open ? '' : ', no times'),
          onclick: function () { st.day = d; st.time = null; render(); } },
          h('small', null, sameDay(d, new Date()) ? 'Today' : DOW[d.getDay()]), h('b', null, d.getDate()), h('small', null, MON[d.getMonth()])), st.day && sameDay(st.day, d));
      }));
    }
    function times() {
      var sl = slots(st.day, list[st.svc].mins);
      return h('div', { class: 'times', role: 'radiogroup', 'aria-label': 'Time' }, sl.map(function (t) {
        return radio(h('button', { type: 'button', class: 'time', onclick: function () { st.time = t; render('#bk-name'); } }, fmtTime(t)), st.time === t);
      }));
    }
    function details() {
      var name = h('input', { class: 'input', id: 'bk-name', autocomplete: 'name', value: st.name, oninput: function (e) { st.name = e.target.value; } });
      var phone = h('input', { class: 'input', id: 'bk-phone', type: 'tel', autocomplete: 'tel', inputmode: 'tel', value: st.phone, oninput: function (e) { st.phone = e.target.value; } });
      var x = list[st.svc];
      return h('form', { novalidate: true, onsubmit: function (e) {
        e.preventDefault();
        if (!st.name.trim()) { st.err = 'Add your name so we know who to expect.'; return render('#bk-name'); }
        if (st.phone.replace(/\D/g, '').length < 10) { st.err = 'Add a 10-digit phone number so we can confirm.'; return render('#bk-phone'); }
        st.err = '';
        if (!LIVE) { st.done = true; return render(); }
        st.sending = true; render();
        send(opts.kind || 'Booking request', { Service: x.name, Details: x.desc || '', With: S.staff ? st.staff : '', Pet: st.pet || '', Day: longDay(st.day), Time: fmtTime(st.time), Name: st.name, Phone: st.phone })
          .then(function () { st.sending = false; st.done = true; render(); }, function () { st.sending = false; st.err = sendFail(); render(); });
      } },
        h('div', { class: 'field' }, h('label', { for: 'bk-name' }, 'Name'), name),
        h('div', { class: 'field' }, h('label', { for: 'bk-phone' }, 'Mobile number'), phone),
        st.err ? h('p', { class: 'err', role: 'alert' }, st.err) : null,
        h('button', { class: 'btn btn-primary btn-block', type: 'submit', disabled: !!st.sending }, st.sending ? 'Sending\u2026' : (LIVE ? 'Request ' : 'Book ') + fmtDay(st.day) + ' at ' + fmtTime(st.time)),
        h('p', { class: 'foot-note' }, x.name + (x.mins ? ', ' + minsLabel(x.mins) : '') + (x.price ? ', ' + priceLabel(x.price) : '')));
    }
    function done() {
      var x = list[st.svc];
      var dl = h('dl', null,
        h('dt', null, 'What'), h('dd', null, x.name),
        st.pet ? [h('dt', null, 'For'), h('dd', null, st.pet === 'Other' ? 'Your pet' : 'Your ' + st.pet.toLowerCase())] : null,
        S.staff ? [h('dt', null, 'With'), h('dd', null, st.staff)] : null,
        h('dt', null, 'When'), h('dd', null, fmtDay(st.day) + ', ' + fmtTime(st.time)),
        h('dt', null, 'Where'), h('dd', null, S.street + ', ' + S.city));
      return h('div', { class: 'enter' },
        h('div', { class: 'ticket' },
          h('div', { class: 'ticket-top' }, tickIcon(), h('div', null, h('h3', null, opts.doneTitle || (LIVE ? 'Request sent, ' : 'You’re booked, ') + firstName(st.name)), h('p', { class: 'card-note' }, LIVE ? 'We’ll text ' + st.phone + ' to confirm your time.' : 'A confirmation text goes to ' + st.phone + '.'))),
          dl),
        h('div', { class: 'row-actions' },
          h('button', { class: 'btn btn-primary', type: 'button', onclick: function () { downloadICS(x.name, st.day, st.time, x.mins); } }, 'Add to calendar'),
          h('button', { class: 'btn btn-ghost', type: 'button', onclick: function () { st = Object.assign(st, { done: false, time: null, day: null, svc: list.length === 1 ? 0 : null, pet: null }); shown = 0; render(); } }, 'Book another')),
        ownerNote('On your real site, every booking lands in your inbox the moment it’s made.'));
    }
    render();
    return { set: function (patch) { Object.assign(st, patch, { done: false }); render(); } };
  }

  function openBooking(opts) {
    opts = opts || {};
    if (LIVE && LINKS.booking && !opts.services) return openLink(LINKS.booking);
    openSheet(opts.sheetTitle || S.cta, function (m) { Booking(m, opts); });
  }

  /* ── Hooks ───────────────────────────────────────────────────────────── */
  var HOOKS = {};

  HOOKS.booking = function (m) {
    if (LIVE && LINKS.booking) {
      add(m, cardHead('Book at ' + S.name, 'See live availability'),
        h('div', { class: 'bk-svcs' }, S.services.map(function (x) { return h('div', { class: 'bk-svc' }, h('b', null, x.name), h('span', { class: 'p' }, priceLabel(x.price)), h('small', null, minsLabel(x.mins) || x.desc || '')); })),
        h('a', { class: 'btn btn-primary btn-block', href: LINKS.booking, target: '_blank', rel: 'noopener', style: 'margin-top:14px' }, 'See open times and book'));
      return;
    }
    Booking(m, { title: 'Book at ' + S.name });
  };

  // Body map
  var ZONE_LABEL = { head: 'Head and jaw', neck: 'Neck', shoulders: 'Shoulders', upperback: 'Upper back', lowerback: 'Lower back', hips: 'Hips', legs: 'Legs and knees', feet: 'Feet and ankles' };
  var ZONE_XY = { head: [120, 46], neck: [120, 86], shoulders: [160, 106], upperback: [120, 134], lowerback: [120, 204], hips: [143, 240], legs: [97, 330], feet: [149, 420] };
  HOOKS.bodymap = function (m) {
    var cur = null;
    var glow = s('circle', { class: 'bm-glow', r: '46', fill: 'url(#heat)' });
    var limbs = [['M80 106 L58 176 L48 246', 22], ['M160 106 L182 176 L192 246', 22], ['M102 236 L96 330 L92 414', 30], ['M138 236 L144 330 L148 414', 30]];
    var svg = s('svg', { viewBox: '0 0 240 448', role: 'group', 'aria-label': 'Body map. Choose where it hurts.' },
      s('defs', null, s('radialGradient', { id: 'heat' }, s('stop', { offset: '0', 'stop-color': 'var(--accent)', 'stop-opacity': '.95' }), s('stop', { offset: '1', 'stop-color': 'var(--accent)', 'stop-opacity': '0' }))),
      limbs.map(function (l) { return s('path', { class: 'bm-limb', d: l[0], 'stroke-width': l[1], 'stroke-linejoin': 'round' }); }),
      s('circle', { class: 'bm-body', cx: '120', cy: '46', r: '27' }),
      s('rect', { class: 'bm-body', x: '107', y: '66', width: '26', height: '30', rx: '10' }),
      s('path', { class: 'bm-body', d: 'M78 94c18-9 66-9 84 0 13 6 16 18 14 34l-10 106c-14 16-78 16-92 0L64 128c-2-16 1-28 14-34z' }),
      s('path', { class: 'bm-spine', d: 'M120 100 V228' }),
      s('ellipse', { class: 'bm-body', cx: '88', cy: '424', rx: '17', ry: '9' }),
      s('ellipse', { class: 'bm-body', cx: '152', cy: '424', rx: '17', ry: '9' }),
      glow,
      Object.keys(ZONE_XY).map(function (z) {
        var xy = ZONE_XY[z];
        var g = s('g', { class: 'spot', tabindex: '0', role: 'button', 'aria-label': ZONE_LABEL[z], 'data-z': z },
          s('circle', { class: 'ring', cx: xy[0], cy: xy[1], r: '9' }),
          s('circle', { cx: xy[0], cy: xy[1], r: '22', fill: 'transparent' }),
          s('circle', { class: 'dot', cx: xy[0], cy: xy[1], r: '7' }));
        g.addEventListener('click', function () { pick(z); });
        g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(z); } });
        return g;
      }));
    var fig = h('div', { class: 'bm-fig' }, svg);
    var out = h('div', { class: 'bm-out', 'aria-live': 'polite' });
    var chips = h('div', { class: 'chips bm-zones', role: 'radiogroup', 'aria-label': 'Area' });
    Object.keys(ZONE_LABEL).forEach(function (z) {
      chips.appendChild(radio(h('button', { type: 'button', class: 'chip', 'data-z': z, onclick: function () { pick(z); } }, ZONE_LABEL[z]), false));
    });
    function empty() {
      out.replaceChildren(
        h('p', { class: 'bm-zone' }, 'Tap where you feel it.'),
        h('p', { class: 'bm-why' }, 'We’ll suggest the right ' + S.noun + ' and show the next open time.'));
    }
    function pick(z) {
      cur = z; svg.classList.add('picked');
      $$('.spot', svg).forEach(function (g) { g.classList.toggle('on', g.getAttribute('data-z') === z); });
      $$('.chip', chips).forEach(function (c) { c.setAttribute('aria-checked', c.getAttribute('data-z') === z ? 'true' : 'false'); });
      glow.setAttribute('cx', ZONE_XY[z][0]); glow.setAttribute('cy', ZONE_XY[z][1]);
      glow.classList.remove('on'); void glow.getBoundingClientRect(); glow.classList.add('on');
      var rec = S.zones[z] || [0, ''], i = rec[0], x = S.services[i] || S.services[0];
      var nx = nextOpening(x.mins);
      out.replaceChildren(h('div', { class: 'enter' },
        h('p', { class: 'bm-zone' }, ZONE_LABEL[z]),
        h('p', { class: 'bm-why' }, rec[1]),
        h('div', { class: 'bm-rec' }, h('span', null, 'We suggest'), h('b', null, x.name), h('span', null, [minsLabel(x.mins), priceLabel(x.price)].filter(Boolean).join(', '))),
        nx ? h('button', { type: 'button', class: 'btn btn-primary btn-block', onclick: function () { openBooking({ svc: i, day: nx.day, time: nx.time }); } }, 'Book ' + fmtDay(nx.day) + ', ' + fmtTime(nx.time)) : null,
        h('p', { class: 'foot-note' }, h('button', { type: 'button', class: 'link-btn', onclick: function () { openBooking({ svc: i }); } }, 'See other times'))));
    }
    empty();
    add(m, cardHead('Where does it hurt?', 'Tap a spot'), h('div', { class: 'bm' }, fig, out), chips);
  };

  // Instant estimate
  HOOKS.estimate = function (m) {
    var st = { job: 0, size: S.jobs[0].def, urg: 1 }, lo = 0, hi = 0;
    var jobsEl = h('div', { class: 'chips', role: 'radiogroup', 'aria-label': 'Job' });
    var range = h('input', { class: 'range', type: 'range', id: 'est-size' });
    var sizeOut = h('output', { for: 'est-size' });
    var sizeLbl = h('label', { for: 'est-size' });
    var seg = h('div', { class: 'seg', role: 'radiogroup', 'aria-label': 'When' });
    var big = h('span', { class: 'big-num', 'aria-live': 'polite' });
    var desc = h('p');
    function unitText(n, unit) { return num(n) + ' ' + (n === 1 && /^[a-z]+s$/.test(unit) ? unit.slice(0, -1) : unit); }
    function syncJob() {
      var j = S.jobs[st.job];
      jobsEl.replaceChildren.apply(jobsEl, S.jobs.map(function (x, i) {
        return radio(h('button', { type: 'button', class: 'chip', onclick: function () { st.job = i; st.size = x.def; syncJob(); } }, x.name), i === st.job);
      }));
      range.min = j.min; range.max = j.max; range.step = j.step; range.value = st.size;
      sizeLbl.textContent = 'Size of the job';
      calc();
    }
    function calc() {
      var j = S.jobs[st.job]; st.size = +range.value;
      range.style.setProperty('--fill', ((st.size - j.min) / (j.max - j.min) * 100) + '%');
      sizeOut.textContent = unitText(st.size, j.unit);
      var p = (j.base + j.rate * st.size) * S.urgency[st.urg][1];
      var nlo = Math.max(5, Math.round(p * 0.9 / 5) * 5), nhi = Math.round(p * 1.12 / 5) * 5;
      var flo = lo, fhi = hi; lo = nlo; hi = nhi;
      tween(0, 1, 450, function (k) { big.textContent = money(Math.round(flo + (nlo - flo) * k)) + ' – ' + money(Math.round(fhi + (nhi - fhi) * k)); });
      desc.textContent = j.name + ', ' + unitText(st.size, j.unit) + ', ' + S.urgency[st.urg][0].toLowerCase() + '. Labour and materials included. We confirm the price on site before we start.';
    }
    range.addEventListener('input', calc);
    S.urgency.forEach(function (u, i) {
      seg.appendChild(radio(h('button', { type: 'button', onclick: function () { st.urg = i; $$('button', seg).forEach(function (b, k) { b.setAttribute('aria-checked', k === i ? 'true' : 'false'); }); calc(); } }, u[0]), i === st.urg));
    });
    add(m, cardHead('Instant estimate', demoText('Sample prices. You set your own.', 'Estimate only. We confirm on site.')),
      h('p', { class: 'lbl', style: 'margin:0 0 10px' }, 'What do you need?'), jobsEl,
      h('div', { class: 'size-val', style: 'margin-top:18px' }, sizeLbl, sizeOut), range,
      h('p', { class: 'lbl', style: 'margin:10px 0 8px' }, 'When?'), seg,
      h('div', { class: 'est-out' }, h('span', { class: 'lbl' }, 'Your estimate'), big, desc),
      h('button', { type: 'button', class: 'btn btn-primary btn-block', style: 'margin-top:14px', onclick: function () {
        var j = S.jobs[st.job];
        openBooking({ sheetTitle: 'Book a free estimate visit', kind: 'Estimate visit request', lockSvc: true, services: [{ name: j.name + ', ' + unitText(st.size, j.unit), mins: 30, price: 0, desc: big.textContent }] });
      } }, 'Book a free visit to confirm'));
    syncJob();
  };

  // Ordering (food)
  var cart = {}, cartSubs = [];
  function cartKeys() { return Object.keys(cart).filter(function (k) { return cart[k] > 0; }); }
  function itemOf(k) { var p = k.split('|'); return S.menu[p[0]][+p[1]]; }
  function cartCount() { return cartKeys().reduce(function (a, k) { return a + cart[k]; }, 0); }
  function cartTotal() { return cartKeys().reduce(function (a, k) { return a + cart[k] * itemOf(k).price; }, 0); }
  function onCart(el, fn) { cartSubs.push([el, fn]); fn(); }
  function notify() {
    cartSubs = cartSubs.filter(function (x) { return x[0].isConnected; });
    cartSubs.forEach(function (x) { x[1](); });
  }
  function setQty(k, q) { cart[k] = Math.max(0, Math.min(20, q)); notify(); }
  function addCtl(k) {
    var box = h('div');
    onCart(box, function () {
      var q = cart[k] || 0, it = itemOf(k);
      box.replaceChildren(q === 0
        ? h('button', { type: 'button', class: 'add', 'aria-label': 'Add ' + it.name, onclick: function () { setQty(k, 1); } }, '+ Add')
        : h('div', { class: 'qty' },
            h('button', { type: 'button', 'aria-label': 'One less ' + it.name, onclick: function () { setQty(k, q - 1); } }, '−'),
            h('output', { 'aria-live': 'polite' }, q),
            h('button', { type: 'button', 'aria-label': 'One more ' + it.name, onclick: function () { setQty(k, q + 1); } }, '+')));
    });
    return box;
  }
  function pickupOptions() {
    var now = new Date(), nowMin = now.getHours() * 60 + now.getMinutes(), out = [], days = nextDays(4);
    for (var i = 0; i < days.length; i++) {
      var d = days[i], hrs = hoursOn(d); if (!hrs) continue;
      var openNow = i === 0 && nowMin >= hrs.open * 60 && nowMin < hrs.close * 60 - 20;
      var start = i === 0 ? Math.max(hrs.open * 60 + 30, Math.ceil((nowMin + 20) / 15) * 15) : hrs.open * 60 + 30;
      for (var t = start; t <= hrs.close * 60 - 15 && out.length < 5; t += 15) out.push({ day: d, time: t, asap: openNow && out.length === 0 });
      if (out.length) break;
    }
    return out;
  }
  function checkout() {
    var st = { pick: 0, name: '', phone: '', err: '' };
    openSheet('Your order', function (m) {
      function render(focus) {
        m.replaceChildren();
        var keys = cartKeys();
        if (!keys.length) { add(m, h('p', null, 'Your order is empty. Add something from the menu.'), h('button', { class: 'btn btn-primary', type: 'button', onclick: closeSheet }, 'Back to the menu')); return; }
        var sub = cartTotal(), tax = Math.round(sub * 13) / 100, opts = pickupOptions();
        var lines = h('div', { class: 'ord-items' }, keys.map(function (k) {
          var it = itemOf(k);
          return h('div', { class: 'ord-item' }, h('div', null, h('b', null, it.name), h('br'), h('small', null, money(it.price, 2) + ' each')),
            h('div', { class: 'qty' },
              h('button', { type: 'button', 'aria-label': 'One less', onclick: function () { setQty(k, cart[k] - 1); render(); } }, '−'),
              h('output', null, cart[k]),
              h('button', { type: 'button', 'aria-label': 'One more', onclick: function () { setQty(k, cart[k] + 1); render(); } }, '+')));
        }));
        var form = h('form', { novalidate: true, onsubmit: function (e) {
          e.preventDefault();
          if (!st.name.trim()) { st.err = 'Add your name for the pickup shelf.'; return render('#o-name'); }
          if (st.phone.replace(/\D/g, '').length < 10) { st.err = 'Add a 10-digit phone number so we can text you.'; return render('#o-phone'); }
          if (!LIVE) return placed(opts[st.pick], sub + tax);
          var o = opts[st.pick]; st.sending = true; st.err = ''; render();
          send('Pickup order', { Items: keys.map(function (k) { return cart[k] + ' x ' + itemOf(k).name; }).join(', '), Total: money(sub + tax, 2) + ' (pay at pickup)', Pickup: longDay(o.day) + ' at ' + fmtTime(o.time), Name: st.name, Phone: st.phone })
            .then(function () { placed(o, sub + tax); }, function () { st.sending = false; st.err = sendFail(); render(); });
        } },
          h('p', { class: 'step-lbl' }, 'Pickup time'),
          opts.length ? h('div', { class: 'chips', role: 'radiogroup', 'aria-label': 'Pickup time' }, opts.map(function (o, i) {
            return radio(h('button', { type: 'button', class: 'chip', onclick: function () { st.pick = i; render(); } }, o.asap ? 'ASAP, about 20 min' : fmtDay(o.day) + ' ' + fmtTime(o.time)), i === st.pick);
          })) : h('p', null, 'We’re closed for the next few days.'),
          h('div', { class: 'two', style: 'margin-top:16px' },
            h('div', { class: 'field' }, h('label', { for: 'o-name' }, 'Name'), h('input', { class: 'input', id: 'o-name', autocomplete: 'name', value: st.name, oninput: function (e) { st.name = e.target.value; } })),
            h('div', { class: 'field' }, h('label', { for: 'o-phone' }, 'Mobile'), h('input', { class: 'input', id: 'o-phone', type: 'tel', autocomplete: 'tel', value: st.phone, oninput: function (e) { st.phone = e.target.value; } }))),
          st.err ? h('p', { class: 'err', role: 'alert' }, st.err) : null,
          h('button', { class: 'btn btn-primary btn-block', type: 'submit', disabled: !opts.length || !!st.sending }, st.sending ? 'Sending\u2026' : 'Place order, ' + money(sub + tax, 2)),
          LIVE ? h('p', { class: 'foot-note' }, 'You pay when you pick up.') : null);
        add(m, lines,
          h('div', { class: 'ord-sum' }, h('span', null, 'Subtotal'), h('span', null, money(sub, 2))),
          h('div', { class: 'ord-sum', style: 'border:0;margin-top:4px;padding-top:0' }, h('span', null, 'HST (13%)'), h('span', null, money(tax, 2))),
          h('div', { class: 'ord-sum', style: 'margin-bottom:18px' }, h('strong', null, 'Total'), h('strong', null, money(sub + tax, 2))),
          form);
        if (focus) { var f = $(focus, m); if (f) f.focus(); }
      }
      function placed(o, total) {
        var no = 100 + Math.floor(Math.random() * 800);
        var steps = LIVE
          ? [['Order sent', money(total, 2) + ', pay at pickup'], ['Confirmed by text', 'We’ll text you shortly'], ['Ready for pickup', fmtDay(o.day) + ' at ' + fmtTime(o.time)]]
          : [['Order received', 'Order #' + no + ', ' + money(total, 2)], ['In the kitchen', 'We’re making it now'], ['Ready for pickup', fmtDay(o.day) + ' at ' + fmtTime(o.time)]];
        var track = h('ol', { class: 'track' }, steps.map(function (x, i) { return h('li', { class: i === 0 ? 'done' : null }, h('div', null, h('b', null, x[0]), x[1])); }));
        sheetTitle.textContent = 'Thanks, ' + firstName(st.name);
        m.replaceChildren(h('div', { class: 'enter' },
          h('div', { class: 'ticket' }, h('div', { class: 'ticket-top' }, tickIcon(), h('div', null, h('h3', null, LIVE ? 'Your order is in' : 'Order #' + no + ' is in'), h('p', { class: 'card-note' }, 'We’ll text ' + st.phone + (LIVE ? ' to confirm.' : ' when it’s ready.')))), track),
          ownerNote('On your real site, orders come straight to you and customers can pay online.')));
        if (!LIVE) setTimeout(function () { var li = $$('li', track)[1]; if (li) li.classList.add('done'); }, 1600);
        Object.keys(cart).forEach(function (k) { cart[k] = 0; });
        notify();
      }
      render();
    });
  }
  HOOKS.order = function (m) {
    var pop = (S.popular || []).map(function (p) { return p[0] + '|' + p[1]; });
    if (LIVE && LINKS.order) {
      add(m, cardHead('Order for pickup', 'Ready in about 20 min'), h('p', { class: 'lbl', style: 'margin:0' }, 'Popular right now'),
        h('div', { class: 'ord-items' }, pop.map(function (k) { var it = itemOf(k); return h('div', { class: 'ord-item' }, h('div', null, h('b', null, it.name), it.desc ? [h('br'), h('small', null, it.desc)] : null), h('span', { class: 'price' }, money(it.price, 2))); })),
        h('a', { class: 'btn btn-primary btn-block', href: LINKS.order, target: '_blank', rel: 'noopener', style: 'margin-top:16px' }, 'Order online'),
        h('p', { class: 'foot-note' }, h('a', { href: '#services' }, 'See the full menu')));
      return;
    }
    var list = h('div', { class: 'ord-items' }, pop.map(function (k) {
      var it = itemOf(k);
      return h('div', { class: 'ord-item' }, h('div', null, h('b', null, it.name), it.desc ? [h('br'), h('small', null, it.desc)] : null),
        h('div', { style: 'display:grid;justify-items:end;gap:6px' }, h('span', { class: 'price' }, money(it.price, 2)), addCtl(k)));
    }));
    var sum = h('div', { class: 'ord-sum' });
    onCart(sum, function () {
      var c = cartCount();
      sum.replaceChildren(h('div', null, h('strong', { class: c ? 'bump' : null }, money(cartTotal(), 2)), h('br'), h('small', null, c ? c + (c === 1 ? ' item' : ' items') : 'Nothing added yet')),
        h('button', { type: 'button', class: 'btn btn-primary', disabled: !c, onclick: checkout }, 'Checkout'));
    });
    add(m, cardHead('Order for pickup', 'Ready in about 20 min'), h('p', { class: 'lbl', style: 'margin:0' }, 'Popular right now'), list, sum,
      h('p', { class: 'foot-note' }, h('a', { href: '#services' }, 'See the full menu'), demoText('. Sample menu and prices.', '.')));
    var fab = h('button', { type: 'button', class: 'cart-fab', onclick: checkout, 'aria-label': 'View order' });
    document.body.appendChild(fab);
    onCart(fab, function () {
      var c = cartCount();
      fab.classList.toggle('show', c > 0);
      fab.replaceChildren(h('span', { class: 'count' }, c), 'View order, ' + money(cartTotal(), 2));
    });
  };
  function renderMenu(mount) {
    var cats = Object.keys(S.menu), cur = cats[0];
    var tabs = h('div', { class: 'menu-tabs', role: 'tablist', 'aria-label': 'Menu sections' });
    var grid = h('div', { class: 'menu-grid', role: 'tabpanel' });
    function draw() {
      tabs.replaceChildren.apply(tabs, cats.map(function (c) {
        return h('button', { type: 'button', class: 'chip', role: 'tab', 'aria-selected': c === cur ? 'true' : 'false', 'aria-pressed': c === cur ? 'true' : 'false', onclick: function () { cur = c; draw(); } }, c);
      }));
      grid.replaceChildren.apply(grid, S.menu[cur].map(function (it, i) {
        return h('div', { class: 'menu-item enter' }, h('div', null, h('h3', null, it.name, it.veg ? h('span', { class: 'veg', title: 'Vegetarian' }, 'V') : null), it.desc ? h('p', null, it.desc) : null),
          h('div', { class: 'right' }, h('span', { class: 'svc-price' }, money(it.price, 2)), LIVE && LINKS.order ? null : addCtl(cur + '|' + i)));
      }));
    }
    draw();
    add(mount, tabs, grid, LIVE && LINKS.order ? h('a', { class: 'btn btn-primary', href: LINKS.order, target: '_blank', rel: 'noopener', style: 'margin-top:20px' }, 'Order online') : null,
      demoText('x', null) ? h('p', { class: 'svc-note' }, 'Sample menu and prices. Yours go here, with photos.') : null);
  }

  // Mortgage calculator (Canadian: semi-annual compounding, CMHC premiums)
  HOOKS.mortgage = function (m) {
    var st = { price: 650000, down: 10, rate: 4.3, years: 25 }, shown = 0;
    function row(id, label, min, max, step, val, fmt, on) {
      var r = h('input', { class: 'range', type: 'range', id: id, min: min, max: max, step: step, value: val });
      var o = h('output', { for: id });
      function sync() { r.style.setProperty('--fill', ((r.value - min) / (max - min) * 100) + '%'); o.textContent = fmt(+r.value); on(+r.value); calc(); }
      r.addEventListener('input', sync);
      return { el: h('div', { class: 'calc-row' }, h('div', { class: 'size-val' }, h('label', { for: id }, label), o), r), sync: sync, input: r };
    }
    var big = h('span', { class: 'big-num', 'aria-live': 'polite' });
    var detail = h('p', { class: 'card-note' }), bar = h('div', { class: 'split', 'aria-hidden': 'true' }, h('i'), h('i')), legend = h('div', { class: 'legend' }), warn = h('div');
    var rPrice = row('m-price', 'Home price', 200000, 1500000, 5000, st.price, function (v) { return money(v); }, function (v) { st.price = v; });
    var rDown = row('m-down', 'Down payment', 5, 35, 1, st.down, function (v) { return v + '% (' + money(Math.round(st.price * v / 100)) + ')'; }, function (v) { st.down = v; });
    var rRate = row('m-rate', LIVE ? 'Interest rate' : 'Interest rate (sample)', 2, 8, 0.05, st.rate, function (v) { return v.toFixed(2) + '%'; }, function (v) { st.rate = v; });
    var seg = h('div', { class: 'seg', role: 'radiogroup', 'aria-label': 'Amortization' }, [25, 30].map(function (y) {
      return radio(h('button', { type: 'button', onclick: function () { st.years = y; $$('button', seg).forEach(function (b) { b.setAttribute('aria-checked', b.textContent.indexOf(String(y)) === 0 ? 'true' : 'false'); }); calc(); } }, y + ' years'), y === st.years);
    }));
    function minDown(p) { return p <= 500000 ? p * 0.05 : 25000 + (Math.min(p, 1500000) - 500000) * 0.10; }
    function calc() {
      var p = st.price, down = p * st.down / 100, notes = [];
      var need = p >= 1500000 ? p * 0.2 : minDown(p);
      if (down < need - 1) { down = need; notes.push('The minimum down payment at this price is ' + money(Math.ceil(need)) + ' (' + (need / p * 100).toFixed(1) + '%). We used that.'); }
      var pct = down / p * 100, prem = pct < 10 ? 0.04 : pct < 15 ? 0.031 : pct < 20 ? 0.028 : 0;
      var loan = (p - down) * (1 + prem), i = Math.pow(1 + st.rate / 200, 1 / 6) - 1, n = st.years * 12;
      var pay = loan * i / (1 - Math.pow(1 + i, -n)), interest = pay * n - loan;
      if (prem) notes.push('Includes ' + money(Math.round((p - down) * prem)) + ' mortgage default insurance, added to the loan.');
      var from = shown; shown = pay;
      tween(from, pay, 450, function (v) { big.textContent = money(Math.round(v)); });
      detail.textContent = 'a month on a ' + money(Math.round(loan)) + ' mortgage over ' + st.years + ' years';
      var a = loan / (loan + interest) * 100;
      bar.children[0].style.width = a + '%'; bar.children[1].style.width = (100 - a) + '%';
      legend.replaceChildren(h('span', null, 'Borrowed ' + money(Math.round(loan))), h('span', null, 'Interest ' + money(Math.round(interest))));
      warn.replaceChildren.apply(warn, notes.map(function (t) { return h('p', { class: 'warn' }, t); }));
    }
    add(m, cardHead('Monthly payment', demoText('Sample rate. Not a quote.', 'Estimate only. Not a mortgage offer.')), rPrice.el, rDown.el, rRate.el,
      h('p', { class: 'lbl', style: 'margin:4px 0 8px' }, 'Amortization'), seg,
      h('div', { class: 'pay' }, h('div', null, big, detail)), bar, legend, warn,
      h('button', { type: 'button', class: 'btn btn-primary btn-block', style: 'margin-top:16px', onclick: function () { openBooking({ svc: 0, sheetTitle: S.cta }); } }, 'Book a free call to beat this rate'));
    rPrice.sync(); rDown.sync(); rRate.sync();
  };

  // Tax deadline countdown + what to bring
  HOOKS.taxday = function (m) {
    var now = new Date(), y = now.getFullYear(), dl = new Date(y, 3, 30, 23, 59, 59);
    if (now > dl) dl = new Date(y + 1, 3, 30, 23, 59, 59);
    var cells = ['days', 'hours', 'min', 'sec'].map(function (u) { return h('div', null, h('b', null, '0'), h('small', null, u)); });
    var cd = h('div', { class: 'cd', role: 'timer', 'aria-label': 'Time left to file' }, cells);
    function tick() {
      var ms = Math.max(0, dl - new Date()), t = Math.floor(ms / 1000);
      [Math.floor(t / 86400), Math.floor(t % 86400 / 3600), Math.floor(t % 3600 / 60), t % 60].forEach(function (v, i) { cells[i].firstChild.textContent = v; });
    }
    tick(); setInterval(tick, 1000);
    var items = ['T4 slips from every employer', 'RRSP contribution receipts', 'Medical and dental receipts', 'Donation receipts', 'Rent or property tax paid (for the Ontario Trillium Benefit)', 'Childcare receipts', 'Last year’s notice of assessment'];
    var meter = h('i'), status = h('p', { class: 'card-note', 'aria-live': 'polite' });
    var checks = h('div', { class: 'checks' }, items.map(function (t, i) {
      return h('label', { class: 'check' }, h('input', { type: 'checkbox', onchange: upd }), h('span', null, t));
    }));
    function upd() {
      var n = $$('input:checked', checks).length;
      meter.style.width = (n / items.length * 100) + '%';
      status.textContent = n === items.length ? 'All set. Book your appointment and bring the lot.' : n + ' of ' + items.length + ' ready';
    }
    add(m, cardHead('Until the tax deadline', 'April 30, ' + dl.getFullYear()), cd,
      h('p', { class: 'lbl', style: 'margin:0' }, 'What to bring'), checks, h('div', { class: 'meter' }, meter), status,
      h('button', { type: 'button', class: 'btn btn-primary btn-block', style: 'margin-top:14px', onclick: function () { openBooking({ sheetTitle: S.cta }); } }, S.cta));
    upd();
  };

  // Intake (3 steps)
  HOOKS.intake = function (m) {
    var st = { step: 0, matter: null, when: null, best: 'Afternoon', name: '', phone: '', err: '' };
    var WHEN = ['As soon as possible', 'In the next few weeks', 'I’m just exploring'];
    function render(focus) {
      m.replaceChildren(cardHead('Free 15-minute call', 'Step ' + Math.min(st.step + 1, 3) + ' of 3'),
        h('div', { class: 'progress', 'aria-hidden': 'true' }, [0, 1, 2].map(function (i) { return h('i', { class: i <= st.step ? 'on' : null }); })));
      var body = h('div', { class: 'enter' });
      if (st.step === 0) {
        add(body, h('p', { class: 'q' }, 'What do you need help with?'), h('div', { class: 'opts', role: 'radiogroup' }, S.matters.map(function (x) {
          return radio(h('button', { type: 'button', class: 'opt', onclick: function () { st.matter = x; st.step = 1; render(); } }, x, h('span', { 'aria-hidden': 'true' }, '›')), st.matter === x);
        })));
      } else if (st.step === 1) {
        add(body, h('p', { class: 'q' }, 'How soon do you need help?'), h('div', { class: 'opts', role: 'radiogroup' }, WHEN.map(function (x) {
          return radio(h('button', { type: 'button', class: 'opt', onclick: function () { st.when = x; st.step = 2; render('#i-name'); } }, x, h('span', { 'aria-hidden': 'true' }, '›')), st.when === x);
        })), h('button', { type: 'button', class: 'link-btn back', onclick: function () { st.step = 0; render(); } }, 'Back'));
      } else if (st.step === 2) {
        add(body, h('p', { class: 'q' }, 'Where can we reach you?'),
          h('form', { novalidate: true, onsubmit: function (e) {
            e.preventDefault();
            if (!st.name.trim()) { st.err = 'Add your name so we know who we’re calling.'; return render('#i-name'); }
            if (st.phone.replace(/\D/g, '').length < 10) { st.err = 'Add a 10-digit phone number.'; return render('#i-phone'); }
            st.err = '';
            if (!LIVE) { st.step = 3; return render(); }
            st.sending = true; render();
            send('Consultation request', { About: st.matter, Timing: st.when, 'Best time to call': st.best, Name: st.name, Phone: st.phone })
              .then(function () { st.sending = false; st.step = 3; render(); }, function () { st.sending = false; st.err = sendFail(); render(); });
          } },
            h('div', { class: 'field' }, h('label', { for: 'i-name' }, 'Name'), h('input', { class: 'input', id: 'i-name', autocomplete: 'name', value: st.name, oninput: function (e) { st.name = e.target.value; } })),
            h('div', { class: 'field' }, h('label', { for: 'i-phone' }, 'Phone'), h('input', { class: 'input', id: 'i-phone', type: 'tel', autocomplete: 'tel', value: st.phone, oninput: function (e) { st.phone = e.target.value; } })),
            h('p', { class: 'lbl', style: 'margin:0 0 8px' }, 'Best time to call'),
            h('div', { class: 'chips', role: 'radiogroup', style: 'margin-bottom:16px' }, ['Morning', 'Afternoon', 'Evening'].map(function (x) {
              return radio(h('button', { type: 'button', class: 'chip', onclick: function () { st.best = x; render(); } }, x), st.best === x);
            })),
            st.err ? h('p', { class: 'err', role: 'alert' }, st.err) : null,
            h('button', { type: 'submit', class: 'btn btn-primary btn-block', disabled: !!st.sending }, st.sending ? 'Sending\u2026' : 'Request my free call')),
          h('button', { type: 'button', class: 'link-btn back', onclick: function () { st.step = 1; render(); } }, 'Back'));
      } else {
        add(body, h('div', { class: 'ticket' },
          h('div', { class: 'ticket-top' }, tickIcon(), h('div', null, h('h3', null, 'Thanks, ' + firstName(st.name)), h('p', { class: 'card-note' }, 'We’ll call ' + st.phone + ' in the ' + st.best.toLowerCase() + ', usually within one business day.'))),
          h('dl', null, h('dt', null, 'About'), h('dd', null, st.matter), h('dt', null, 'Timing'), h('dd', null, st.when))),
          ownerNote('On your real site, these requests land in your inbox with everything you need before you call back.'));
      }
      m.appendChild(body);
      if (focus) { var f = $(focus, m); if (f) f.focus({ preventScroll: true }); }
    }
    render();
  };

  // Quiz -> plan
  HOOKS.quiz = function (m) {
    var Q = S.quiz, ans = [];
    function render() {
      var i = ans.length;
      m.replaceChildren(cardHead(Q.mode === 'availability' ? 'Check for a spot' : 'Find your plan', i < Q.questions.length ? 'Question ' + (i + 1) + ' of ' + Q.questions.length : 'Your result'),
        h('div', { class: 'progress', 'aria-hidden': 'true' }, Q.questions.map(function (_, k) { return h('i', { class: k < i ? 'on' : null }); })));
      var body = h('div', { class: 'enter' });
      if (i < Q.questions.length) {
        var q = Q.questions[i];
        add(body, h('p', { class: 'q' }, q.q), h('div', { class: 'opts' }, q.options.map(function (o) {
          return h('button', { type: 'button', class: 'opt', onclick: function () { ans.push(o); render(); } }, o, h('span', { 'aria-hidden': 'true' }, '›'));
        })), i ? h('button', { type: 'button', class: 'link-btn back', onclick: function () { ans.pop(); render(); } }, 'Back') : null);
      } else {
        var r = Q.results[ans[0]] || Q.results[Object.keys(Q.results)[0]];
        var plan = h('div', { class: 'plan' });
        if (Q.mode === 'availability') {
          var start = new Date(); start.setMonth(start.getMonth() + (ans[2] === 'This month' ? 0 : ans[2] === 'Next month' ? 1 : 3));
          var later = rand('room|' + ans[0] + ans[1]) < 0.35;
          if (later) start.setMonth(start.getMonth() + 1);
          add(plan, h('span', { class: 'card-note' }, later ? 'Short waitlist' : 'Spots open'), h('h3', null, r[0]), h('p', { style: 'margin:0' }, r[1]),
            h('ul', null, h('li', null, ans[1] + ' a week'), h('li', null, (later ? 'Next opening: ' : 'Available from ') + MON_LONG[start.getMonth()] + ' ' + start.getFullYear())));
          add(body, plan, h('button', { type: 'button', class: 'btn btn-primary btn-block', style: 'margin-top:16px', onclick: function () {
            openBooking({ sheetTitle: 'Book a visit', kind: 'Visit request', lockSvc: true, services: [{ name: 'Visit and tour: ' + r[0], mins: 30, price: 0 }] });
          } }, 'Book a visit'));
        } else {
          add(plan, h('span', { class: 'card-note' }, 'Your plan'), h('h3', null, r[0]), h('p', { style: 'margin:0' }, r[1]),
            h('ul', null, Q.questions.slice(1).map(function (q, k) { return h('li', null, q.q.replace(/\?$/, '') + ': ' + ans[k + 1].toLowerCase()); }),
              Q.price ? h('li', null, money(Q.price) + ' per ' + Q.unit) : null));
          var free = S.services.filter(function (x) { return x.price === 0 && /free/i.test(x.name); })[0];
          add(body, plan, h('button', { type: 'button', class: 'btn btn-primary btn-block', style: 'margin-top:16px', onclick: function () {
            openBooking({ sheetTitle: 'Book your first ' + S.noun, kind: 'First ' + S.noun + ' request', lockSvc: true, services: [free ? { name: free.name + ': ' + r[0], mins: free.mins || 60, price: 0 } : { name: 'First ' + S.noun + ': ' + r[0], mins: 60, price: Q.price }] });
          } }, free ? 'Book my free first ' + S.noun : 'Book my first ' + S.noun));
        }
        add(body, h('button', { type: 'button', class: 'link-btn back', onclick: function () { ans = []; render(); } }, 'Start again'));
      }
      m.appendChild(body);
    }
    render();
  };

  // Timetable
  HOOKS.timetable = function (m) {
    var POOL = S.theme === 'kids' ? [960, 1020, 1080, 1140] : S.theme === 'gym' ? [390, 720, 1050, 1140] : [420, 570, 720, 1065, 1155];
    var days = nextDays(7), cur = 0, filter = 'All';
    function classesOn(d) {
      if (S.schedule) return S.schedule.filter(function (c) { return c.day === d.getDay(); }).map(function (c) { return { t: c.t, name: c.name, level: c.level || 'All levels', spots: null }; }).sort(function (a, b) { return a.t - b.t; });
      var hrs = hoursOn(d);
      if (!hrs && S.theme !== 'kids') return [];
      if (S.theme === 'kids' && (d.getDay() === 0)) return [];
      return POOL.filter(function (t) { return rand('c' + dayKey(d) + t) > 0.25; }).map(function (t) {
        var name = S.classes[Math.floor(rand('n' + dayKey(d) + t) * S.classes.length)];
        return { t: t, name: name, level: ['All levels', 'Beginner', 'Intermediate'][Math.floor(rand('l' + dayKey(d) + t) * 3)], spots: Math.floor(rand('s' + dayKey(d) + t) * 13) };
      });
    }
    var tabs = h('div', { class: 'days', role: 'radiogroup', 'aria-label': 'Day' });
    var filters = h('div', { class: 'chips', role: 'radiogroup', 'aria-label': 'Class', style: 'margin-top:10px' });
    var listEl = h('div', { class: 'tt-list', 'aria-live': 'polite' });
    function draw() {
      tabs.replaceChildren.apply(tabs, days.map(function (d, i) {
        return radio(h('button', { type: 'button', class: 'day', onclick: function () { cur = i; draw(); } }, h('small', null, i === 0 ? 'Today' : DOW[d.getDay()]), h('b', null, d.getDate()), h('small', null, MON[d.getMonth()])), i === cur);
      }));
      filters.replaceChildren.apply(filters, ['All'].concat(S.classes).map(function (c) {
        return radio(h('button', { type: 'button', class: 'chip', onclick: function () { filter = c; draw(); } }, c), c === filter);
      }));
      var cls = classesOn(days[cur]).filter(function (c) { return filter === 'All' || c.name === filter; });
      listEl.replaceChildren.apply(listEl, cls.length ? cls.map(function (c) {
        var full = c.spots === 0;
        return h('div', { class: 'cls enter' }, h('time', null, fmtTime(c.t)), h('div', null, h('b', null, c.name), h('small', { class: c.spots && c.spots < 4 ? 'spots-low' : null }, c.spots == null ? c.level : c.level + ', ' + (full ? 'full' : c.spots + (c.spots === 1 ? ' spot left' : ' spots left')))),
          h('button', { type: 'button', class: 'btn ' + (full ? 'btn-ghost' : 'btn-primary'), onclick: function () { reserve(c, days[cur], full); } }, full ? 'Waitlist' : 'Reserve'));
      }) : [h('p', { class: 'card-note', style: 'padding:20px 0' }, 'No ' + (filter === 'All' ? '' : filter + ' ') + 'classes on ' + DOW_LONG[days[cur].getDay()] + '. Try another day.')]);
    }
    function reserve(c, d, full) {
      openBooking({ sheetTitle: full ? 'Join the waitlist' : 'Reserve your spot', kind: full ? 'Waitlist request' : 'Class reservation', lockSvc: true, services: [{ name: c.name + ' (' + c.level.toLowerCase() + ')', mins: 60, price: 0 }], day: d, time: c.t,
        doneTitle: full ? 'You’re on the waitlist' : 'Your spot is saved' });
    }
    draw();
    add(m, cardHead('This week’s classes', 'First class free'), tabs, filters, listEl);
  };

  // Bouquet builder
  HOOKS.bouquet = function (m) {
    var FL = [
      { n: 'Roses', c: '#c8344f', p: 6, k: 3 }, { n: 'Peonies', c: '#f2a7b5', p: 8, k: 2 }, { n: 'Tulips', c: '#f07b4f', p: 4, k: 0 },
      { n: 'Ranunculus', c: '#f6b26b', p: 5, k: 2 }, { n: 'Lisianthus', c: '#b9a6e0', p: 5, k: 0 }, { n: 'Eucalyptus', c: '#7fa88a', p: 3, k: 3, leaf: true }];
    var WRAPS = [['Kraft', '#c9a37b'], ['Blush', '#f1c4cb'], ['Sage', '#a9bfa6']], wrap = 0;
    var stage = h('div', { class: 'bq-stage', 'aria-hidden': 'true' });
    var total = h('strong'), countEl = h('small');
    function flower(x, y, f, r, i) {
      var g = s('g', { class: 'bq-flower', style: 'animation-delay:' + (i * 25) + 'ms' });
      if (f.leaf) {
        for (var k = 0; k < 4; k++) g.appendChild(s('ellipse', { cx: x + (k % 2 ? 7 : -7), cy: y + k * 9 - 12, rx: 7, ry: 4.5, fill: f.c, transform: 'rotate(' + (k % 2 ? 35 : -35) + ' ' + (x + (k % 2 ? 7 : -7)) + ' ' + (y + k * 9 - 12) + ')' }));
        return g;
      }
      var petals = f.n === 'Tulips' ? 3 : f.n === 'Peonies' ? 9 : 6;
      for (var p = 0; p < petals; p++) {
        var a = 360 / petals * p;
        g.appendChild(s('ellipse', { cx: x, cy: y - r * 0.55, rx: r * (f.n === 'Tulips' ? 0.42 : 0.5), ry: r * 0.62, fill: f.c, opacity: '.92', transform: 'rotate(' + a + ' ' + x + ' ' + y + ')' }));
      }
      if (f.n === 'Roses') g.appendChild(s('circle', { cx: x, cy: y, r: r * 0.55, fill: 'none', stroke: 'rgba(0,0,0,.18)', 'stroke-width': 2 }));
      g.appendChild(s('circle', { cx: x, cy: y, r: r * 0.28, fill: f.n === 'Peonies' ? '#e88b9c' : 'rgba(60,30,20,.45)' }));
      return g;
    }
    function draw() {
      var stems = [];
      FL.forEach(function (f) { for (var i = 0; i < f.k; i++) stems.push(f); });
      stems.sort(function (a, b) { return (a.leaf ? 0 : 1) - (b.leaf ? 0 : 1); });
      var svg = s('svg', { viewBox: '0 0 300 360' });
      var n = stems.length, cx = 150, base = 300;
      stems.forEach(function (f, i) {
        var t = n === 1 ? 0.5 : i / (n - 1), ang = (-55 + t * 110 + (rand('a' + i) - 0.5) * 14) * Math.PI / 180;
        var len = 150 + rand('l' + i) * 50 - Math.abs(t - 0.5) * 50;
        var x = cx + Math.sin(ang) * len, y = base - Math.cos(ang) * len;
        svg.appendChild(s('path', { d: 'M' + cx + ' ' + base + ' Q ' + (cx + (x - cx) * 0.4) + ' ' + (base - 60) + ' ' + x + ' ' + y, stroke: '#4f7a52', 'stroke-width': 3, fill: 'none', 'stroke-linecap': 'round' }));
      });
      stems.forEach(function (f, i) {
        var t = n === 1 ? 0.5 : i / (n - 1), ang = (-55 + t * 110 + (rand('a' + i) - 0.5) * 14) * Math.PI / 180;
        var len = 150 + rand('l' + i) * 50 - Math.abs(t - 0.5) * 50;
        svg.appendChild(flower(cx + Math.sin(ang) * len, base - Math.cos(ang) * len, f, 20 + rand('r' + i) * 8, i));
      });
      var w = WRAPS[wrap][1];
      svg.appendChild(s('path', { d: 'M92 250 L150 352 L208 250 Q150 270 92 250 Z', fill: w }));
      svg.appendChild(s('path', { d: 'M92 250 L150 352 L150 262 Q120 262 92 250 Z', fill: 'rgba(0,0,0,.08)' }));
      svg.appendChild(s('path', { d: 'M128 300 q22 -10 44 0', stroke: '#fff', 'stroke-width': 5, fill: 'none', 'stroke-linecap': 'round', opacity: '.85' }));
      if (!n) svg.appendChild(s('text', { x: 150, y: 170, 'text-anchor': 'middle', fill: 'currentColor', 'font-size': 16 }, 'Add some stems'));
      stage.replaceChildren(svg);
      var sum = FL.reduce(function (a, f) { return a + f.k * f.p; }, 0) + (n ? 5 : 0);
      total.textContent = money(sum);
      countEl.textContent = n + (n === 1 ? ' stem' : ' stems') + ', ' + WRAPS[wrap][0].toLowerCase() + ' wrap' + (sum >= 75 ? ', free delivery' : ', delivery $12');
    }
    var stems = h('div', { class: 'stems' }, FL.map(function (f) {
      var out = h('output', null, f.k);
      return h('div', { class: 'stem' }, h('span', { class: 'sw', style: 'background:' + f.c }), h('div', null, f.n, h('small', null, money(f.p) + ' a stem')),
        h('div', { class: 'qty' },
          h('button', { type: 'button', 'aria-label': 'One less ' + f.n, onclick: function () { f.k = Math.max(0, f.k - 1); out.textContent = f.k; draw(); } }, '−'), out,
          h('button', { type: 'button', 'aria-label': 'One more ' + f.n, onclick: function () { f.k = Math.min(12, f.k + 1); out.textContent = f.k; draw(); } }, '+')));
    }));
    var wraps = h('div', { class: 'swatches', role: 'radiogroup', 'aria-label': 'Wrap', style: 'margin:12px 0' }, WRAPS.map(function (w, i) {
      return radio(h('button', { type: 'button', class: 'swatch', style: 'background:' + w[1], 'aria-label': w[0] + ' wrap', onclick: function () { wrap = i; $$('.swatch', wraps).forEach(function (b, k) { b.setAttribute('aria-checked', k === i ? 'true' : 'false'); }); draw(); } }), i === wrap);
    }));
    draw();
    add(m, cardHead('Build your bouquet', demoText('Sample prices', null)), h('div', { class: 'bq' }, stage, h('div', null, stems, wraps)),
      h('div', { class: 'ord-sum' }, h('div', null, total, h('br'), countEl),
        h('button', { type: 'button', class: 'btn btn-primary', onclick: function () {
          var n = FL.reduce(function (a, f) { return a + f.k; }, 0);
          if (!n) return;
          openBooking({ sheetTitle: 'Send your bouquet', kind: 'Bouquet order', svcLabel: 'Bouquet', lockSvc: true, services: [{ name: 'Your bouquet (' + n + ' stems), ' + total.textContent, mins: 30, price: null }], doneTitle: 'Your bouquet is ordered' });
        } }, 'Send it')));
  };

  /* ── Sections ────────────────────────────────────────────────────────── */
  function renderServices() {
    var mount = $('[data-mount="services"]'); if (!mount) return;
    if (S.hook === 'order') return renderMenu(mount);
    var label = S.hook === 'intake' || S.hook === 'mortgage' ? 'Book a call' : 'Book';
    var ul = h('ul', { class: 'svc-list' }, S.services.map(function (x, i) {
      return h('li', { class: 'svc' },
        h('div', null, h('h3', { class: 'svc-name' }, x.name), x.desc ? h('p', { class: 'svc-desc' }, x.desc) : null),
        h('div', { class: 'svc-meta' }, x.mins ? h('span', { class: 'svc-time' }, minsLabel(x.mins)) : null, h('span', { class: 'svc-price' }, priceLabel(x.price)),
          h('button', { type: 'button', class: 'btn btn-primary', 'aria-label': label + ': ' + x.name, onclick: function () { openBooking({ svc: i, sheetTitle: x.name }); } }, label)));
    }));
    add(mount, ul, demoText('x', null) ? h('p', { class: 'svc-note' }, 'Sample services and prices. Yours go here.') : null);
  }

  function renderGift() {
    var mount = $('[data-mount="gift"]'); if (!mount) return;
    var st = { amt: 50, design: 0, to: '', from: '', msg: '' }, shown = 50;
    var amtEl = h('div', { class: 'gc-amount' }, '$50');
    var toEl = h('span'), msgEl = h('span', { class: 'gc-msg' });
    var initial = (S.name.replace(/^the\s+/i, '').match(/[A-Za-z0-9]/) || ['G'])[0].toUpperCase();
    var card = h('div', { class: 'gc-card', 'data-design': '0', role: 'img', 'aria-label': 'Gift card preview' },
      s('svg', { class: 'motif', viewBox: '0 0 100 100', 'aria-hidden': 'true' }, s('text', { x: '50', y: '86', 'text-anchor': 'middle', 'font-size': '110', fill: 'currentColor', style: 'font-family:var(--font-d)' }, initial)),
      h('div', { class: 'gc-top' }, h('span', { class: 'gc-name' }, S.name), h('span', { class: 'gc-kind' }, 'Gift card')),
      amtEl,
      h('div', { class: 'gc-bottom' }, msgEl, toEl));
    var stage = h('div', { class: 'gc-stage' }, card);
    stage.addEventListener('pointermove', function (e) {
      if (e.pointerType === 'touch') return;
      var r = card.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      card.style.setProperty('--ry', ((x - 0.5) * 14) + 'deg'); card.style.setProperty('--rx', ((0.5 - y) * 12) + 'deg');
      card.style.setProperty('--mx', (x * 100) + '%'); card.style.setProperty('--my', (y * 100) + '%');
    });
    stage.addEventListener('pointerleave', function () { card.style.setProperty('--rx', '0deg'); card.style.setProperty('--ry', '0deg'); });
    function sync() {
      var from = shown; shown = st.amt;
      tween(from, st.amt, 380, function (v) { amtEl.textContent = money(Math.round(v)); });
      card.setAttribute('data-design', st.design);
      toEl.textContent = st.to ? 'For ' + st.to : '';
      msgEl.textContent = st.msg ? '“' + st.msg + '”' : '';
      buy.textContent = 'Buy a ' + money(st.amt) + ' gift card';
    }
    var amts = h('div', { class: 'chips', role: 'radiogroup', 'aria-label': 'Amount' });
    var other = h('input', { class: 'input amt-other', type: 'number', min: '10', max: '1000', step: '5', placeholder: 'Other', 'aria-label': 'Other amount', inputmode: 'numeric',
      oninput: function (e) { var v = Math.round(+e.target.value); if (v >= 10 && v <= 1000) { st.amt = v; drawAmts(); sync(); } } });
    function drawAmts() {
      amts.replaceChildren.apply(amts, S.gift.amounts.map(function (a) {
        return radio(h('button', { type: 'button', class: 'chip', onclick: function () { st.amt = a; other.value = ''; drawAmts(); sync(); } }, money(a)), st.amt === a);
      }).concat([other]));
    }
    var designs = h('div', { class: 'swatches', role: 'radiogroup', 'aria-label': 'Design' }, ['var(--primary)', 'var(--accent)', '#17171c'].map(function (c, i) {
      return radio(h('button', { type: 'button', class: 'swatch', style: 'background:' + c, 'aria-label': 'Design ' + (i + 1), onclick: function () { st.design = i; $$('.swatch', designs).forEach(function (b, k) { b.setAttribute('aria-checked', k === i ? 'true' : 'false'); }); sync(); } }), i === 0);
    }));
    var counter = h('p', { class: 'counter' }, '0 / 120');
    var err = h('div');
    var buy = h('button', { type: 'submit', class: 'btn btn-primary btn-block' });
    var form = h('form', { class: 'gc-form', novalidate: true, onsubmit: function (e) {
      e.preventDefault();
      if (LIVE && LINKS.giftCards) return openLink(LINKS.giftCards);
      var email = $('#gc-email', form).value.trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { err.replaceChildren(h('p', { class: 'err', role: 'alert' }, 'Add the email address the gift card should go to.')); $('#gc-email', form).focus(); return; }
      err.replaceChildren();
      if (LIVE) {
        buy.disabled = true; buy.textContent = 'Sending\u2026';
        send('Gift card request', { Amount: money(st.amt), To: st.to, From: st.from, Message: st.msg, 'Send to': email }).then(function () {
          openSheet('Request sent', function (m) {
            add(m, h('div', { class: 'enter' }, h('div', { class: 'ticket' },
              h('div', { class: 'ticket-top' }, tickIcon(), h('div', null, h('h3', null, 'Your ' + money(st.amt) + ' gift card request is in'), h('p', { class: 'card-note' }, 'We\u2019ll email you a payment link today.'))))));
          });
          sync(); buy.disabled = false;
        }, function () { err.replaceChildren(h('p', { class: 'err', role: 'alert' }, sendFail())); sync(); buy.disabled = false; });
        return;
      }
      var code = 'GC-' + Math.random().toString(36).slice(2, 6).toUpperCase() + '-' + Math.random().toString(36).slice(2, 6).toUpperCase();
      openSheet('Gift card sent', function (m) {
        add(m, h('div', { class: 'enter' }, h('div', { class: 'ticket' },
          h('div', { class: 'ticket-top' }, tickIcon(), h('div', null, h('h3', null, money(st.amt) + ' gift card on its way'), h('p', { class: 'card-note' }, 'Sent to ' + email))),
          h('dl', null, h('dt', null, 'Code'), h('dd', null, code), st.to ? [h('dt', null, 'For'), h('dd', null, st.to)] : null, st.from ? [h('dt', null, 'From'), h('dd', null, st.from)] : null)),
          ownerNote('On your real site, buyers pay online and the card arrives by email. You see every sale.')));
      });
    } },
      h('p', { class: 'lbl', style: 'margin:0 0 10px' }, 'Amount'), amts,
      h('p', { class: 'lbl', style: 'margin:18px 0 10px' }, 'Design'), designs,
      h('div', { class: 'two', style: 'margin-top:18px' },
        h('div', { class: 'field' }, h('label', { for: 'gc-to' }, 'To'), h('input', { class: 'input', id: 'gc-to', maxlength: '30', oninput: function (e) { st.to = e.target.value; sync(); } })),
        h('div', { class: 'field' }, h('label', { for: 'gc-from' }, 'From'), h('input', { class: 'input', id: 'gc-from', maxlength: '30', oninput: function (e) { st.from = e.target.value; sync(); } }))),
      h('div', { class: 'field' }, h('label', { for: 'gc-msg' }, 'Message'), h('textarea', { class: 'input', id: 'gc-msg', maxlength: '120', rows: '2', oninput: function (e) { st.msg = e.target.value; counter.textContent = st.msg.length + ' / 120'; sync(); } })),
      counter,
      LIVE && LINKS.giftCards ? null : h('div', { class: 'field' }, h('label', { for: 'gc-email' }, 'Send it to (email)'), h('input', { class: 'input', id: 'gc-email', type: 'email', autocomplete: 'email' })),
      err, buy, h('p', { class: 'foot-note' }, LIVE ? (LINKS.giftCards ? 'You\u2019ll finish on our secure checkout. The card arrives by email.' : 'We\u2019ll email you a secure payment link.') : 'Demo only. No payment is taken.'));
    drawAmts(); sync();
    add(mount, h('div', { class: 'gc' }, stage, form));
  }

  function renderHours() {
    var mount = $('[data-mount="hours"]'); if (!mount) return;
    var now = new Date(), today = now.getDay(), mins = now.getHours() * 60 + now.getMinutes();
    var hrs = hoursOn(now), open = hrs && mins >= hrs.open * 60 && mins < hrs.close * 60, badge;
    if (open) badge = 'Open now, until ' + fmtTime(hrs.close * 60);
    else {
      var nx = null;
      for (var i = 0; i < 8 && !nx; i++) {
        var d = new Date(now); d.setDate(now.getDate() + i);
        var e = hoursOn(d);
        if (e && (i > 0 || mins < e.open * 60)) nx = { d: d, e: e, i: i };
      }
      badge = 'Closed now' + (nx ? ', opens ' + (nx.i === 0 ? 'today' : nx.i === 1 ? 'tomorrow' : DOW_LONG[nx.d.getDay()]) + ' at ' + fmtTime(nx.e.open * 60) : '');
    }
    add(mount, h('p', { class: 'open-badge' + (open ? ' is-open' : '') }, badge),
      h('table', { class: 'hours' }, h('caption', { class: 'sr' }, 'Opening hours'), h('tbody', null, S.hours.map(function (r) {
        return h('tr', { class: r.days.indexOf(today) > -1 ? 'today' : null }, h('td', null, r.label), h('td', null, r.open == null ? 'Closed' : fmtTime(r.open * 60) + ' to ' + fmtTime(r.close * 60)));
      }))),
      demoText('x', null) ? h('p', { class: 'small-note' }, 'Sample hours. Yours go here.') : null);
  }

  function renderGallery() {
    var mount = $('[data-mount="gallery"]'), sec = $('#gallery');
    if (!mount || !sec || !S.photos || !S.photos.length) return;
    sec.hidden = false;
    add(mount, S.photos.map(function (p) { return h('figure', { class: 'ph' }, h('img', { src: p.src, alt: p.alt || '', loading: 'lazy', decoding: 'async' }), p.caption ? h('figcaption', null, p.caption) : null); }));
  }
  function renderFaq() {
    var mount = $('[data-mount="faq"]'); if (!mount) return;
    add(mount, S.faq.map(function (x) { return h('details', { class: 'qa' }, h('summary', null, x.q), h('p', null, x.a)); }));
  }

  /* ── Page load ───────────────────────────────────────────────────────── */
  function splitHeadline() {
    var el = $('.h1'); if (!el) return;
    var words = el.textContent.trim().split(/\s+/);
    el.setAttribute('aria-label', el.textContent.trim());
    el.replaceChildren.apply(el, words.map(function (w, i) {
      return [h('span', { class: 'w', 'aria-hidden': 'true' }, h('span', { style: '--i:' + i }, w)), i < words.length - 1 ? ' ' : null];
    }).reduce(function (a, b) { return a.concat(b); }, []).filter(function (x) { return x !== null; }));
  }
  function hdrShadow() {
    var hdr = $('.hdr'); if (!hdr) return;
    var on = false;
    window.addEventListener('scroll', function () { var v = window.scrollY > 8; if (v !== on) { on = v; hdr.classList.toggle('scrolled', v); } }, { passive: true });
  }
  function start() {
    splitHeadline();
    var hook = $('[data-mount="hook"]');
    try { if (hook && HOOKS[S.hook]) { hook.replaceChildren(); HOOKS[S.hook](hook); } } catch (e) { console.error(e); }
    [renderServices, renderGallery, renderGift, renderHours, renderFaq].forEach(function (f) { try { f(); } catch (e) { console.error(e); } });
    hdrShadow();
    $$('a[href="#hook"]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault(); scrollToEl($('#hook'));
        var f = $('#hook button, #hook input'); if (f) setTimeout(function () { f.focus({ preventScroll: true }); }, 500);
      });
    });
    var go = function () { requestAnimationFrame(function () { requestAnimationFrame(function () { root.classList.add('is-ready'); }); }); };
    if (document.fonts && document.fonts.ready) Promise.race([document.fonts.ready, new Promise(function (r) { setTimeout(r, 700); })]).then(go); else go();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
