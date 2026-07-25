// Dark mode toggle with localStorage persistence
(function () {
  const toggleBtn = document.getElementById('themeToggle');
  const body = document.body;

  const saved = localStorage.getItem('theme');
  if (saved === 'dark') {
    body.classList.add('dark');
    if (toggleBtn) toggleBtn.textContent = '☀️';
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      body.classList.toggle('dark');
      const isDark = body.classList.contains('dark');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
      toggleBtn.textContent = isDark ? '☀️' : '🌙';
      // Reload so Chart.js re-renders with correct text color
      if (window.location.pathname === '/dashboard') {
        location.reload();
      }
    });
  }
})();
