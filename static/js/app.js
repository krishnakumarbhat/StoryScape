(() => {
  const tokenKey = 'storyscape_token';
  const statusEl = document.getElementById('status');
  const storyForm = document.getElementById('story-form');
  const nodeForm = document.getElementById('node-form');
  const connectForm = document.getElementById('connect-form');
  const uploadForm = document.getElementById('upload-form');
  const generateForm = document.getElementById('generate-form');
  const loadStoriesButton = document.getElementById('load-stories');
  const logoutButton = document.getElementById('logout');
  const listEl = document.getElementById('story-list');
  const graphSvg = document.getElementById('graph-canvas');
  const graphJson = document.getElementById('graph-json');
  let activeStoryId = null;

  function token() {
    return localStorage.getItem(tokenKey);
  }

  function setStatus(message, isError = false) {
    statusEl.textContent = message;
    statusEl.classList.toggle('err', isError);
  }

  async function request(url, options = {}) {
    const isFormData = options.body instanceof FormData;
    const headers = { ...(options.headers || {}) };
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    if (token()) {
      headers.Authorization = `Token ${token()}`;
    }

    const response = await fetch(url, { ...options, headers });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || JSON.stringify(data) || response.statusText);
    }
    return data;
  }

  function drawGraph(graph) {
    graphSvg.innerHTML = '';
    const nodes = graph.nodes || [];
    const edges = graph.edges || [];
    if (!nodes.length) {
      return;
    }

    const points = new Map();
    nodes.forEach((node, index) => {
      const x = 120 + (index % 4) * 210;
      const y = 90 + Math.floor(index / 4) * 130;
      points.set(node.id, { x, y, label: node.content.slice(0, 34) + (node.content.length > 34 ? '…' : '') });
    });

    edges.forEach((edge) => {
      const from = points.get(edge.source);
      const to = points.get(edge.target);
      if (!from || !to) return;
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', from.x);
      line.setAttribute('y1', from.y);
      line.setAttribute('x2', to.x);
      line.setAttribute('y2', to.y);
      line.setAttribute('stroke', '#7fb8ff');
      line.setAttribute('stroke-width', '2');
      graphSvg.appendChild(line);
    });

    points.forEach((point) => {
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', point.x);
      circle.setAttribute('cy', point.y);
      circle.setAttribute('r', '24');
      circle.setAttribute('fill', '#2b6cb0');
      circle.setAttribute('stroke', '#c9e0ff');
      circle.setAttribute('stroke-width', '2');
      graphSvg.appendChild(circle);

      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', point.x);
      text.setAttribute('y', point.y + 44);
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('fill', '#dce8ff');
      text.setAttribute('font-size', '12');
      text.textContent = point.label;
      graphSvg.appendChild(text);
    });
  }

  async function loadGraph(storyId) {
    activeStoryId = Number(storyId);
    try {
      const graph = await request(`/api/stories/${storyId}/graph/`);
      graphJson.textContent = JSON.stringify(graph, null, 2);
      drawGraph(graph);
      setStatus(`Graph loaded for story ${storyId}.`);
    } catch (error) {
      setStatus(`Graph failed: ${error.message}`, true);
    }
  }

  function requireActiveStory() {
    if (!activeStoryId) {
      setStatus('Select a story first using "View Graph".', true);
      return false;
    }
    return true;
  }

  function renderStories(stories) {
    listEl.innerHTML = '';
    stories.forEach((story) => {
      const li = document.createElement('li');
      li.innerHTML = `
        <strong>${story.title}</strong>
        <p class="muted">${story.initial_prompt}</p>
        <div class="btn-row">
          <button class="btn" data-action="graph" data-id="${story.id}">View Graph</button>
          <button class="btn ghost" data-action="delete" data-id="${story.id}">Delete</button>
        </div>
      `;
      listEl.appendChild(li);
    });
  }

  async function loadStories() {
    try {
      const data = await request('/api/stories/');
      renderStories(data.results || []);
      setStatus(token() ? 'Authenticated mode active.' : 'Guest mode active: max 5 stories.');
    } catch (error) {
      setStatus(`Load failed: ${error.message}`, true);
    }
  }

  storyForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(storyForm).entries());
    try {
      await request('/api/stories/', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      storyForm.reset();
      await loadStories();
    } catch (error) {
      setStatus(`Create failed: ${error.message}`, true);
    }
  });

  listEl.addEventListener('click', async (event) => {
    const button = event.target;
    if (!(button instanceof HTMLElement)) return;
    const action = button.dataset.action;
    const storyId = button.dataset.id;
    if (!action || !storyId) return;

    if (action === 'graph') {
      await loadGraph(storyId);
      return;
    }

    if (action === 'delete') {
      try {
        await request(`/api/stories/${storyId}/delete/`, { method: 'DELETE' });
        if (Number(storyId) === activeStoryId) {
          activeStoryId = null;
          graphSvg.innerHTML = '';
          graphJson.textContent = '';
        }
        await loadStories();
      } catch (error) {
        setStatus(`Delete failed: ${error.message}`, true);
      }
    }
  });

  nodeForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!requireActiveStory()) return;

    const payload = Object.fromEntries(new FormData(nodeForm).entries());
    if (!payload.parent_card_id) {
      delete payload.parent_card_id;
    }

    try {
      await request(`/api/stories/${activeStoryId}/nodes/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      nodeForm.reset();
      await loadGraph(activeStoryId);
    } catch (error) {
      setStatus(`Add node failed: ${error.message}`, true);
    }
  });

  connectForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!requireActiveStory()) return;

    const payload = Object.fromEntries(new FormData(connectForm).entries());
    try {
      await request(`/api/stories/${activeStoryId}/connect/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      connectForm.reset();
      await loadGraph(activeStoryId);
    } catch (error) {
      setStatus(`Connect nodes failed: ${error.message}`, true);
    }
  });

  uploadForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(uploadForm);
    const nodeId = formData.get('node_id');
    if (!nodeId) {
      setStatus('Node id is required for image upload.', true);
      return;
    }
    formData.delete('node_id');

    try {
      await request(`/api/flashcards/${nodeId}/upload-image/`, {
        method: 'POST',
        body: formData,
      });
      uploadForm.reset();
      if (activeStoryId) {
        await loadGraph(activeStoryId);
      }
      setStatus(`Image uploaded for node ${nodeId}.`);
    } catch (error) {
      setStatus(`Image upload failed: ${error.message}`, true);
    }
  });

  generateForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!requireActiveStory()) return;

    const payload = Object.fromEntries(new FormData(generateForm).entries());
    if (!payload.parent_card_id) {
      delete payload.parent_card_id;
    }

    try {
      await request(`/api/stories/${activeStoryId}/generate-next/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      await loadGraph(activeStoryId);
      setStatus(`Generated one ${payload.mode} node.`);
    } catch (error) {
      setStatus(`Generate node failed: ${error.message}`, true);
    }
  });

  loadStoriesButton.addEventListener('click', loadStories);

  logoutButton.addEventListener('click', () => {
    localStorage.removeItem(tokenKey);
    setStatus('Logged out. Guest mode enabled.');
    activeStoryId = null;
    graphSvg.innerHTML = '';
    graphJson.textContent = '';
    loadStories();
  });

  loadStories();
})();
