(() => {
  const form = document.getElementById('login-form');
  const status = document.getElementById('status');
  const tokenKey = 'storyscape_token';

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(form).entries());

    try {
      const response = await fetch('/api/auth/token/', {
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
      status.textContent = `Login failed: ${error.message}`;
      status.classList.add('err');
    }
  });
})();
