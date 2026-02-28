(() => {
  const form = document.getElementById('register-form');
  const status = document.getElementById('status');
  const tokenKey = 'storyscape_token';

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(form).entries());
    payload.bio = '';

    try {
      const response = await fetch('/api/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || JSON.stringify(data));
      }
      localStorage.setItem(tokenKey, data.token);
      window.location.href = '/app/';
    } catch (error) {
      status.textContent = `Register failed: ${error.message}`;
      status.classList.add('err');
    }
  });
})();
