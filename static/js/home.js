(() => {
  const storageKey = 'storyscape_token';
  const statusElement = document.getElementById('status');
  const registerForm = document.getElementById('register-form');
  const loginForm = document.getElementById('login-form');
  const storyForm = document.getElementById('story-form');
  const loadStoriesButton = document.getElementById('load-stories');
  const clearTokenButton = document.getElementById('clear-token');
  const storyList = document.getElementById('story-list');
  const graphPreview = document.getElementById('graph-preview');

  function getToken() {
    return localStorage.getItem(storageKey);
  }

  function setStatus(message, isError = false) {
    statusElement.textContent = message;
    statusElement.style.color = isError ? '#fca5a5' : '';
  }

  async function apiRequest(url, options = {}) {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };
    if (token) {
      headers.Authorization = `Token ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = data.detail || JSON.stringify(data) || response.statusText;
      throw new Error(detail);
    }
    return data;
  }

  function renderStories(stories) {
    storyList.innerHTML = '';
    stories.forEach((story) => {
      const item = document.createElement('li');
      item.className = 'story-item';
      item.innerHTML = `
        <strong>${story.title}</strong>
        <p class="muted">${story.initial_prompt}</p>
        <button type="button" data-story-id="${story.id}">View Graph</button>
      `;
      storyList.appendChild(item);
    });
  }

  async function loadStories() {
    try {
      const data = await apiRequest('/api/stories/');
      renderStories(data.results || []);
      setStatus('Stories loaded successfully.');
    } catch (error) {
      setStatus(`Load stories failed: ${error.message}`, true);
    }
  }

  registerForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(registerForm);
    const payload = Object.fromEntries(formData.entries());
    payload.bio = '';

    try {
      const data = await apiRequest('/api/auth/register/', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      localStorage.setItem(storageKey, data.token);
      setStatus('Registered and logged in successfully.');
      registerForm.reset();
      await loadStories();
    } catch (error) {
      setStatus(`Register failed: ${error.message}`, true);
    }
  });

  loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(loginForm);
    const payload = Object.fromEntries(formData.entries());

    try {
      const data = await apiRequest('/api/auth/token/', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      localStorage.setItem(storageKey, data.token);
      setStatus('Login successful.');
      loginForm.reset();
      await loadStories();
    } catch (error) {
      setStatus(`Login failed: ${error.message}`, true);
    }
  });

  storyForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(storyForm);
    const payload = Object.fromEntries(formData.entries());

    try {
      await apiRequest('/api/stories/', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setStatus('Story created successfully.');
      storyForm.reset();
      await loadStories();
    } catch (error) {
      setStatus(`Create story failed: ${error.message}`, true);
    }
  });

  storyList.addEventListener('click', async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    const storyId = target.getAttribute('data-story-id');
    if (!storyId) {
      return;
    }

    try {
      const data = await apiRequest(`/api/stories/${storyId}/graph/`);
      graphPreview.textContent = JSON.stringify(data, null, 2);
      setStatus('Graph loaded.');
    } catch (error) {
      setStatus(`Load graph failed: ${error.message}`, true);
    }
  });

  loadStoriesButton.addEventListener('click', loadStories);

  clearTokenButton.addEventListener('click', () => {
    localStorage.removeItem(storageKey);
    storyList.innerHTML = '';
    graphPreview.textContent = '';
    setStatus('Logged out.');
  });

  if (getToken()) {
    loadStories();
  } else {
    setStatus('Login or register to access stories API.');
  }
})();
