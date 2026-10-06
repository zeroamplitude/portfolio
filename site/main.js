(() => {
  const FORM_ENDPOINT = 'https://formspree.io/f/xgavyroa';
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  /* ---------- Mobile menu ---------- */
  const menuBtn = $('.menu-btn');
  const menu = $('#nav-menu');
  function setMenu(open) {
    menu.hidden = !open;
    menuBtn.setAttribute('aria-expanded', String(open));
    menuBtn.textContent = open ? 'Close' : 'Menu';
  }
  menuBtn.addEventListener('click', () => setMenu(menu.hidden));
  $$('a', menu).forEach(a => a.addEventListener('click', () => setMenu(false)));
  matchMedia('(min-width: 760px)').addEventListener('change', e => { if (e.matches) setMenu(false); });

  /* ---------- Contact form modal ---------- */
  // Every page gets the same modal; the case study overrides the heading via data attributes.
  const title = document.body.dataset.formTitle || 'Let’s talk';
  const intro = document.body.dataset.formIntro || 'Tell me what you’re building.';
  const formOverlay = document.createElement('div');
  formOverlay.className = 'overlay';
  formOverlay.hidden = true;
  formOverlay.innerHTML = `
    <form class="modal" role="dialog" aria-modal="true" aria-labelledby="form-title" novalidate>
      <div class="modal-head">
        <div>
          <h3 id="form-title">${title}</h3>
          <p>${intro}</p>
        </div>
        <button type="button" class="icon-btn" data-close aria-label="Close">✕</button>
      </div>
      <div class="modal-body" data-step="form">
        <input class="hp" type="text" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true">
        <div class="field-row">
          <label class="field">Name<input name="name" required autocomplete="name"></label>
          <label class="field">Email<input name="email" type="email" required autocomplete="email"></label>
        </div>
        <label class="field">Company<input name="company" autocomplete="organization"></label>
        <label class="field">Project details<textarea name="message" required rows="5"></textarea></label>
        <button type="submit" class="btn btn-lg btn-lime">Send message</button>
        <p class="form-error" hidden>Something went wrong. Please try again.</p>
      </div>
      <div class="modal-body form-thanks" data-step="sent" hidden>
        <p>Thanks, your message has been sent. I’ll get back to you soon.</p>
        <button type="button" class="btn btn-outline" data-close>Close</button>
      </div>
    </form>`;
  document.body.appendChild(formOverlay);

  const form = $('form', formOverlay);
  const stepForm = $('[data-step="form"]', form);
  const stepSent = $('[data-step="sent"]', form);
  const submitBtn = $('button[type="submit"]', form);
  const errorMsg = $('.form-error', form);
  let lastFocus = null;

  function openForm() {
    // The menu's own button disappears when the menu closes, so return focus to the menu toggle.
    lastFocus = menu.contains(document.activeElement) ? menuBtn : document.activeElement;
    setMenu(false);
    stepForm.hidden = false;
    stepSent.hidden = true;
    errorMsg.hidden = true;
    formOverlay.hidden = false;
    $('input[name="name"]', form).focus();
  }
  function closeForm() {
    formOverlay.hidden = true;
    if (lastFocus) lastFocus.focus();
  }

  $$('[data-open-form]').forEach(el => el.addEventListener('click', e => { e.preventDefault(); openForm(); }));
  formOverlay.addEventListener('click', e => { if (e.target === formOverlay) closeForm(); });
  $$('[data-close]', form).forEach(el => el.addEventListener('click', closeForm));

  form.addEventListener('submit', e => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const company = (data.get('company') || '').toString().trim();
    data.append('_subject', 'New inquiry' + (company ? ' from ' + company : '') + ' (portfolio)');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending…';
    errorMsg.hidden = true;
    fetch(FORM_ENDPOINT, { method: 'POST', body: data, headers: { Accept: 'application/json' } })
      .then(r => {
        if (!r.ok) throw new Error(r.status);
        form.reset();
        stepForm.hidden = true;
        stepSent.hidden = false;
        $('[data-close]', stepSent).focus();
      })
      .catch(() => { errorMsg.hidden = false; })
      .finally(() => { submitBtn.disabled = false; submitBtn.textContent = 'Send message'; });
  });

  /* ---------- Lightbox: click any screenshot to see it full size ---------- */
  const lightbox = document.createElement('div');
  lightbox.className = 'overlay lightbox';
  lightbox.hidden = true;
  lightbox.setAttribute('role', 'dialog');
  lightbox.setAttribute('aria-modal', 'true');
  lightbox.setAttribute('aria-label', 'Screenshot');
  lightbox.innerHTML = '<button type="button" class="icon-btn lightbox-close" aria-label="Close">✕</button><div class="lightbox-stage"></div><span></span>';
  document.body.appendChild(lightbox);
  // The <img> is added on first open, so crawlers never see an image without alt text.
  const lbImg = document.createElement('img'), lbCap = $('span', lightbox);

  function openLightbox(src, trigger) {
    lastFocus = trigger;
    lbImg.src = src.currentSrc || src.src;
    lbImg.alt = src.alt;
    if (!lbImg.isConnected) $('.lightbox-stage', lightbox).appendChild(lbImg);
    lbCap.textContent = src.alt;
    // On narrow screens a wide screenshot fitted to the width is too small to read,
    // so show it taller and let the visitor swipe sideways across it.
    const wide = src.naturalWidth > src.naturalHeight * 1.2;
    lightbox.classList.toggle('pan', wide && matchMedia('(max-width: 759px)').matches);
    lightbox.hidden = false;
    $('.lightbox-stage', lightbox).scrollLeft = 0;
    document.documentElement.style.overflow = 'hidden';
    $('.lightbox-close', lightbox).focus();
  }
  function closeLightbox() {
    lightbox.hidden = true;
    document.documentElement.style.overflow = '';
    if (lastFocus) lastFocus.focus();
  }
  lightbox.addEventListener('click', closeLightbox);

  // Gallery thumbnails are already buttons.
  $$('[data-lightbox]').forEach(t => t.addEventListener('click', () => openLightbox($('img', t), t)));
  // Screenshots elsewhere (carousels, case study) become keyboard-reachable zoom targets.
  $$('.shot img, .cs-hero-frame img, .phone-frame img').forEach(im => {
    if (im.closest('[data-lightbox]')) return;
    im.classList.add('zoomable');
    im.tabIndex = 0;
    im.setAttribute('role', 'button');
    im.setAttribute('aria-label', 'Enlarge: ' + im.alt);
    im.addEventListener('click', () => openLightbox(im, im));
    im.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openLightbox(im, im); }
    });
  });

  addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (!menu.hidden) setMenu(false);
    if (!formOverlay.hidden) closeForm();
    if (!lightbox.hidden) closeLightbox();
  });

  /* ---------- Copy page: Markdown for LLMs ---------- */
  // The deploy generates <page>.md for every page (tools/page_markdown.py).
  const ICONS = {
    copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>',
    check: '<path d="M5 12l5 5 9-10"/>',
    md: '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M6 15V9l3 3 3-3v6M16 9v6m-2-2 2 2 2-2"/>',
    file: '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/>',
    chat: '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12h5"/>',
    out: '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    chevron: '<path d="M6 9l6 6 6-6"/>',
  };
  const icon = name => '<svg viewBox="0 0 24 24" aria-hidden="true">' + ICONS[name] + '</svg>';

  $$('[data-copy-page]').forEach(root => {
    const canonical = ($('link[rel="canonical"]') || {}).href || location.href;
    const mdPath = (new URL(canonical).pathname.replace(/\/$/, '/index.html')).replace(/\.html$/, '.md');
    const mdAbs = new URL(mdPath, canonical).href;
    const ask = 'Read ' + mdAbs + ' so I can ask you questions about it.';
    const items = [
      ['copy', 'Copy page', 'Copy this page as Markdown for LLMs'],
      ['md', 'View as Markdown', 'View this page as plain text', mdPath],
      ['file', 'LLMs full', 'The whole site as Markdown for LLMs', '/llms-full.txt'],
      ['chat', 'Open in Claude', 'Ask questions about this page', 'https://claude.ai/new?q=' + encodeURIComponent(ask)],
      ['chat', 'Open in ChatGPT', 'Ask questions about this page', 'https://chatgpt.com/?hints=search&q=' + encodeURIComponent(ask)],
    ];
    const id = 'copy-page-menu-' + Math.random().toString(36).slice(2, 8);
    root.innerHTML =
      '<button type="button" class="cp-main">' + icon('copy') + '<span>Copy page</span></button>' +
      '<button type="button" class="cp-toggle" aria-label="More ways to use this page" aria-haspopup="menu" aria-expanded="false" aria-controls="' + id + '">' + icon('chevron') + '</button>' +
      '<div class="cp-menu" role="menu" id="' + id + '" hidden>' +
      items.map(([ic, title, sub, href]) => {
        const body = icon(ic) + '<span class="cp-text"><span class="cp-title">' + title + '</span><span class="cp-sub">' + sub + '</span></span>';
        return href
          ? '<a role="menuitem" href="' + href + '" target="_blank" rel="noopener">' + body + '<span class="cp-out">' + icon('out') + '</span></a>'
          : '<button type="button" role="menuitem" data-copy>' + body + '</button>';
      }).join('') +
      '</div>';

    const main = $('.cp-main', root), toggle = $('.cp-toggle', root), list = $('.cp-menu', root);
    const label = $('span', main);
    const entries = $$('[role="menuitem"]', list);

    // Fetch the Markdown up front so the copy happens inside the click (Safari drops
    // clipboard access once a click handler has awaited a network request).
    let markdown = null;
    const load = () => markdown || (markdown = fetch(mdPath).then(r => {
      if (!r.ok) throw new Error(r.status);
      return r.text();
    }));
    load().catch(() => { markdown = null; });

    function flash(text, ok) {
      label.textContent = text;
      main.innerHTML = icon(ok ? 'check' : 'copy');
      main.appendChild(label);
      main.classList.toggle('cp-done', ok);
      clearTimeout(main._t);
      main._t = setTimeout(() => {
        label.textContent = 'Copy page';
        main.innerHTML = icon('copy');
        main.appendChild(label);
        main.classList.remove('cp-done');
      }, 2000);
    }
    function copy() {
      const p = load();
      const write = window.ClipboardItem && navigator.clipboard.write
        ? navigator.clipboard.write([new ClipboardItem({ 'text/plain': p.then(t => new Blob([t], { type: 'text/plain' })) })])
        : p.then(t => navigator.clipboard.writeText(t));
      write.then(() => flash('Copied', true), () => { markdown = null; flash('Copy failed', false); });
    }
    function setOpen(open, focusFirst) {
      list.hidden = !open;
      toggle.setAttribute('aria-expanded', String(open));
      if (open && focusFirst) entries[0].focus();
    }

    main.addEventListener('click', copy);
    toggle.addEventListener('click', () => setOpen(list.hidden, false));
    toggle.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true, true); }
      if (e.key === 'Escape' && !list.hidden) { e.stopPropagation(); setOpen(false); }
    });
    $('[data-copy]', list).addEventListener('click', () => { copy(); setOpen(false); toggle.focus(); });
    $$('a', list).forEach(a => a.addEventListener('click', () => setOpen(false)));
    list.addEventListener('keydown', e => {
      const i = entries.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        entries[(i + (e.key === 'ArrowDown' ? 1 : -1) + entries.length) % entries.length].focus();
      } else if (e.key === 'Escape') {
        e.stopPropagation();
        setOpen(false);
        toggle.focus();
      } else if (e.key === 'Tab') {
        setOpen(false);
      }
    });
    document.addEventListener('click', e => { if (!root.contains(e.target)) setOpen(false); });
  });

  /* ---------- Carousels (home) ---------- */
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  $$('[data-carousel]').forEach(root => {
    const track = $('.carousel-track', root);
    const slides = $$('img', track);
    const caption = $('.carousel-caption', root);
    const dotsWrap = $('.carousel-dots', root);
    const n = slides.length;
    let i = 0, held = false;

    const dots = slides.map((s, j) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('aria-label', 'Show ' + s.alt);
      b.addEventListener('click', () => go(j));
      dotsWrap.appendChild(b);
      return b;
    });

    function go(k) {
      i = (k + n) % n;
      track.style.transform = 'translateX(-' + i * 100 + '%)';
      caption.textContent = slides[i].alt;
      dots.forEach((d, j) => d.setAttribute('aria-current', j === i ? 'true' : 'false'));
      slides.forEach((s, j) => {
        s.setAttribute('aria-hidden', j === i ? 'false' : 'true');
        s.tabIndex = j === i ? 0 : -1;
      });
    }

    $('[data-prev]', root).addEventListener('click', () => go(i - 1));
    $('[data-next]', root).addEventListener('click', () => go(i + 1));
    root.addEventListener('pointerenter', () => { held = true; });
    root.addEventListener('pointerleave', () => { held = false; });
    root.addEventListener('focusin', () => { held = true; });
    root.addEventListener('focusout', () => { held = false; });
    if (!reduceMotion) setInterval(() => { if (!held && !document.hidden) go(i + 1); }, 6000);
    go(0);
  });
})();
