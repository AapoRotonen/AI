const TOKEN_KEY = 'supportai.accessToken';
const ROLE_KEY = 'supportai.role';
let selectedTicketId = null;
let currentView = 'tickets';

const $ = (id) => document.getElementById(id);
const token = () => localStorage.getItem(TOKEN_KEY);
const escapeText = (value) => String(value ?? '');

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (token()) headers.set('Authorization', `Bearer ${token()}`);
  if (options.body) headers.set('Content-Type', 'application/json');
  const response = await fetch(path, { ...options, headers });
  if (response.status === 401) logout();
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { message = (await response.json()).message || message; } catch { /* Safe generic fallback. */ }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

function showApp(email, role) {
  $('login-panel').classList.add('hidden');
  $('app-panel').classList.remove('hidden');
  $('user-bar').classList.remove('hidden');
  $('whoami').textContent = `${email} · ${role.replaceAll('_', ' ')}`;
  if (role === 'SENIOR_SUPPORT' || role === 'ADMIN') $('reviews-view').dataset.reviewer = 'true';
  $('assistant-hint').textContent = 'Ask a question about a ticket, internal policy, or service status.';
  refreshTickets();
}

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  $('app-panel').classList.add('hidden');
  $('user-bar').classList.add('hidden');
  $('login-panel').classList.remove('hidden');
  $('login-error').classList.add('hidden');
}

function showToast(message) {
  $('toast').textContent = message;
  $('toast').classList.remove('hidden');
  setTimeout(() => $('toast').classList.add('hidden'), 3000);
}

function textNode(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = escapeText(text);
  return node;
}

async function refreshTickets() {
  try {
    const tickets = await api('/api/tickets');
    $('ticket-count').textContent = String(tickets.length);
    const list = $('ticket-list');
    list.replaceChildren();
    if (!tickets.length) list.append(textNode('p', 'empty-list', 'No tickets are assigned to you.'));
    tickets.forEach((ticket) => {
      const button = document.createElement('button');
      button.className = `ticket-card${selectedTicketId === ticket.id ? ' selected' : ''}`;
      button.type = 'button';
      button.addEventListener('click', () => selectTicket(ticket.id));
      const meta = document.createElement('div');
      meta.className = 'ticket-meta';
      meta.append(textNode('span', '', `#${ticket.id}`), textNode('span', `priority ${ticket.priority.toLowerCase()}`, ticket.priority));
      button.append(meta, textNode('h3', '', ticket.title), textNode('p', '', ticket.description), textNode('span', 'ticket-status', ticket.status.replaceAll('_', ' ')));
      list.append(button);
    });
    if (selectedTicketId && tickets.some((ticket) => ticket.id === selectedTicketId)) await selectTicket(selectedTicketId, false);
  } catch (error) { showToast(error.message); }
}

async function selectTicket(id, updateSelection = true) {
  selectedTicketId = id;
  if (updateSelection) $('ticket-list').querySelectorAll('.ticket-card').forEach((card) => card.classList.remove('selected'));
  $('ticket-empty').classList.add('hidden');
  const detail = $('ticket-detail');
  detail.classList.remove('hidden');
  detail.replaceChildren(textNode('span', 'ticket-id', `TICKET #${id}`), textNode('h2', 'ticket-title', 'Loading ticket…'));
  try {
    const [ticket, history] = await Promise.all([api(`/api/tickets/${id}`), api(`/api/tickets/${id}/history`)]);
    detail.replaceChildren();
    detail.append(textNode('span', 'ticket-id', `TICKET #${ticket.id}`), textNode('h2', 'ticket-title', ticket.title));
    const tags = document.createElement('div');
    tags.className = 'detail-tags';
    tags.append(textNode('span', 'tag', ticket.status.replaceAll('_', ' ')), textNode('span', `tag priority ${ticket.priority.toLowerCase()}`, `${ticket.priority} priority`), textNode('span', 'tag', `Customer · ${ticket.customerName}`));
    detail.append(tags, textNode('p', 'detail-label', 'CUSTOMER DESCRIPTION'), textNode('div', 'description-box', ticket.description), textNode('p', 'detail-label', 'TICKET HISTORY'));
    const timeline = document.createElement('div');
    timeline.className = 'history-list';
    history.forEach((event) => {
      const item = document.createElement('div');
      item.className = 'history-item';
      item.append(textNode('strong', '', event.eventType.replaceAll('_', ' ')), textNode('span', '', new Date(event.createdAt).toLocaleString()), textNode('p', '', event.description));
      timeline.append(item);
    });
    detail.append(timeline);
    $('assistant-hint').textContent = `Selected ticket #${id}. Try “Investigate ticket ${id} and suggest the next action.”`;
    $('assistant-message').placeholder = `Investigate ticket ${id}…`;
    $('ticket-list').querySelectorAll('.ticket-card').forEach((card) => {
      if (card.textContent.includes(`#${id}`)) card.classList.add('selected');
    });
  } catch (error) { showToast(error.message); }
}

function addBubble(kind, message, sources = []) {
  const bubble = textNode('div', `bubble ${kind}`, message);
  if (sources.length) bubble.append(textNode('span', 'sources', `Sources: ${sources.join(', ')}`));
  $('chat-transcript').append(bubble);
  bubble.scrollIntoView({ block: 'nearest' });
}

async function sendMessage(message) {
  const button = $('assistant-form').querySelector('button');
  button.disabled = true;
  $('ai-state').textContent = 'Working…';
  addBubble('user', message);
  try {
    const response = await api('/api/assistant/chat', { method: 'POST', body: JSON.stringify({ message }) });
    $('ai-state').textContent = response.aiEnabled ? 'AI active' : 'AI offline';
    addBubble('assistant', response.answer);
  } catch (error) {
    $('ai-state').textContent = 'Needs attention';
    addBubble('assistant', error.message);
  } finally { button.disabled = false; }
}

async function refreshReviews() {
  try {
    const reviews = await api('/api/reviews');
    $('review-count').textContent = String(reviews.filter((review) => review.status === 'PENDING').length);
    const list = $('review-list');
    list.replaceChildren();
    if (!reviews.length) list.append(textNode('p', 'empty-list', 'No action proposals yet.'));
    reviews.forEach((review) => {
      const card = document.createElement('article');
      card.className = 'review-card';
      const main = document.createElement('div');
      main.append(textNode('h3', '', `${review.proposedAction.replaceAll('_', ' ')} · ticket #${review.ticketId}`), textNode('p', '', review.reason), textNode('div', 'review-meta', `Proposed by ${review.createdBy} · ${new Date(review.createdAt).toLocaleString()}`));
      if (review.reviewNote) main.append(textNode('p', 'review-meta', `Review note: ${review.reviewNote}`));
      card.append(main);
      if (review.status === 'PENDING' && (localStorage.getItem(ROLE_KEY) === 'SENIOR_SUPPORT' || localStorage.getItem(ROLE_KEY) === 'ADMIN')) {
        const actions = document.createElement('div');
        actions.className = 'review-actions';
        const approve = textNode('button', 'button button-primary', 'Approve');
        approve.type = 'button';
        approve.addEventListener('click', () => decideReview(review.id, 'approve'));
        const reject = textNode('button', 'button button-secondary', 'Reject');
        reject.type = 'button';
        reject.addEventListener('click', () => decideReview(review.id, 'reject'));
        actions.append(approve, reject);
        card.append(actions);
      } else card.append(textNode('span', `review-status ${review.status.toLowerCase()}`, review.status));
      list.append(card);
    });
  } catch (error) { showToast(error.message); }
}

async function decideReview(id, decision) {
  const note = prompt(`Optional note for ${decision}ing this action:`, '');
  if (note === null) return;
  try {
    await api(`/api/reviews/${id}/${decision}`, { method: 'POST', body: JSON.stringify({ note }) });
    showToast(`Review ${decision}d.`);
    await refreshReviews();
    await refreshTickets();
  } catch (error) { showToast(error.message); }
}

document.addEventListener('DOMContentLoaded', () => {
  $('login-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    $('login-error').classList.add('hidden');
    try {
      const result = await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: $('email').value, password: $('password').value }) });
      if (!result.ok) throw new Error('Sign-in failed. Check the demo account and try again.');
      const session = await result.json();
      localStorage.setItem(TOKEN_KEY, session.accessToken);
      localStorage.setItem(ROLE_KEY, session.role);
      showApp(session.email, session.role);
    } catch (error) { $('login-error').textContent = error.message; $('login-error').classList.remove('hidden'); }
  });
  $('logout').addEventListener('click', logout);
  $('refresh-tickets').addEventListener('click', refreshTickets);
  $('refresh-reviews').addEventListener('click', refreshReviews);
  $('assistant-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const message = $('assistant-message').value.trim();
    if (message) { $('assistant-message').value = ''; sendMessage(message); }
  });
  document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => {
    currentView = tab.dataset.view;
    document.querySelectorAll('.tab').forEach((item) => item.classList.toggle('active', item === tab));
    $('tickets-view').classList.toggle('hidden', currentView !== 'tickets');
    $('reviews-view').classList.toggle('hidden', currentView !== 'reviews');
    if (currentView === 'reviews') refreshReviews();
  }));
  if (token() && localStorage.getItem(ROLE_KEY)) showApp('Signed in', localStorage.getItem(ROLE_KEY));
});
