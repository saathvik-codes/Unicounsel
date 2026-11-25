// Sign-in and sign-up behaviour. Everything degrades: without JS the form still posts, both sign-up steps show,
// the first slide is visible and the password stays masked.
(() => {
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // password reveal
  $$('.reveal').forEach((btn) => {
    btn.addEventListener('click', () => {
      const input = btn.parentElement.querySelector('input');
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.setAttribute('aria-pressed', String(show));
      btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
    });
  });

  // confirm password must match
  const pw = document.querySelector('input[name="password"]');
  const confirm = document.querySelector('input[name="confirm_password"]');
  if (pw && confirm) {
    const check = () => confirm.setCustomValidity(confirm.value && confirm.value !== pw.value ? 'The passwords do not match' : '');
    pw.addEventListener('input', check); confirm.addEventListener('input', check);
  }

  // two-step sign-up
  const steps = $$('.step');
  if (steps.length > 1) {
    let i = 0;
    const bars = $$('.steps i'), label = document.querySelector('.steps span');
    const show = (n) => {
      i = n;
      steps.forEach((s, k) => { s.hidden = k !== i; });
      bars.forEach((b, k) => b.toggleAttribute('data-on', k <= i));
      if (label) label.textContent = `Step ${i + 1} of ${steps.length}`;
      steps[i].querySelector('input')?.focus({ preventScroll: true });
    };
    $$('[data-next]').forEach((b) => b.addEventListener('click', () => {
      const bad = $$('input', steps[i]).find((x) => !x.checkValidity());
      if (bad) { bad.reportValidity(); return; }
      show(i + 1);
    }));
    $$('[data-back]').forEach((b) => b.addEventListener('click', () => show(i - 1)));
    // if the server sent the form back with an error, start on the first step
    show(0);
  }

  // illustration carousel
  let slides = $$('.slide');
  if (slides.length) {
    let dots = $$('.dots button');
    const caption = document.querySelector('.caption');
    let cur = 0, timer;
    const go = (n) => {
      cur = (n + slides.length) % slides.length;
      slides.forEach((s, k) => s.toggleAttribute('data-active', k === cur));
      dots.forEach((d, k) => d.setAttribute('aria-current', String(k === cur)));
      if (caption) caption.textContent = slides[cur].dataset.caption || '';
    };
    const play = () => {
      clearInterval(timer);
      if (slides.length > 1 && !matchMedia('(prefers-reduced-motion: reduce)').matches) timer = setInterval(() => go(cur + 1), 6000);
    };
    dots.forEach((d, k) => d.addEventListener('click', () => { go(k); play(); }));
    const stage = document.querySelector('.auth-stage');
    stage?.addEventListener('mouseenter', () => clearInterval(timer));
    stage?.addEventListener('mouseleave', play);
    // a missing image is dropped instead of leaving a hole
    slides.slice().forEach((s) => s.querySelector('img')?.addEventListener('error', () => {
      const k = slides.indexOf(s); if (k < 0) return;
      slides.splice(k, 1); s.hidden = true; dots[k]?.setAttribute('hidden', ''); dots.splice(k, 1);
      if (slides.length) go(Math.min(cur, slides.length - 1));
    }));
    go(0); play();
  }
})();
