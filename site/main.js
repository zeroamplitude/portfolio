(() => {
  const FORM_ENDPOINT = 'https://formspree.io/f/xgavyroa';
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

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
    lastFocus = document.activeElement;
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

  /* ---------- Lightbox (gallery) ---------- */
  let lightbox = null;
  const thumbs = $$('[data-lightbox]');
  if (thumbs.length) {
    lightbox = document.createElement('div');
    lightbox.className = 'overlay lightbox';
    lightbox.hidden = true;
    lightbox.setAttribute('role', 'dialog');
    lightbox.setAttribute('aria-label', 'Screenshot');
    lightbox.innerHTML = '<img alt=""><span></span>';
    document.body.appendChild(lightbox);
    const img = $('img', lightbox), cap = $('span', lightbox);
    thumbs.forEach(t => t.addEventListener('click', () => {
      const src = $('img', t);
      lastFocus = t;
      img.src = src.src;
      img.alt = src.alt;
      cap.textContent = src.alt;
      lightbox.hidden = false;
    }));
    lightbox.addEventListener('click', () => { lightbox.hidden = true; if (lastFocus) lastFocus.focus(); });
  }

  addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (!formOverlay.hidden) closeForm();
    if (lightbox && !lightbox.hidden) { lightbox.hidden = true; if (lastFocus) lastFocus.focus(); }
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
      slides.forEach((s, j) => s.setAttribute('aria-hidden', j === i ? 'false' : 'true'));
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
