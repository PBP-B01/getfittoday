document.addEventListener('DOMContentLoaded', () => {
  const btn  = document.getElementById('userMenuBtn');
  const menu = document.getElementById('userMenu');
  if (!btn || !menu) return;

  function close(e){
    if (!menu.contains(e.target) && !btn.contains(e.target)) {
      menu.classList.add('hidden');
      btn.setAttribute('aria-expanded', 'false');
      document.removeEventListener('click', close);
    }
  }

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = !menu.classList.contains('hidden');
    if (open) {
      menu.classList.add('hidden');
      btn.setAttribute('aria-expanded', 'false');
      document.removeEventListener('click', close);
    } else {
      menu.classList.remove('hidden');
      btn.setAttribute('aria-expanded', 'true');
      setTimeout(() => document.addEventListener('click', close), 0);
    }
  });
});
