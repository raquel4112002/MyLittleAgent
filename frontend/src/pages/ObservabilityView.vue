<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const apiBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:6400').replace(/\/$/, '')

const sessions = ref([])
const selectedSessionId = ref('')
const selectedSession = ref(null)
const events = ref([])
const loading = ref(false)
const error = ref('')
const socketState = ref('disconnected')
let ws = null

const selectedSessionLabel = computed(() => {
  if (!selectedSession.value) return 'No session selected'
  return `${selectedSession.value.workflow_id} · ${selectedSession.value.status}`
})

async function loadSessions() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch(`${apiBase}/api/observability/sessions`)
    if (!response.ok) throw new Error(`Failed to load sessions (${response.status})`)
    sessions.value = await response.json()
    if (!selectedSessionId.value && sessions.value.length > 0) {
      selectedSessionId.value = sessions.value[0].session_id
    }
  } catch (err) {
    error.value = err.message || 'Failed to load sessions'
  } finally {
    loading.value = false
  }
}

async function loadSessionDetail(sessionId) {
  if (!sessionId) return
  error.value = ''
  try {
    const [sessionRes, eventRes] = await Promise.all([
      fetch(`${apiBase}/api/observability/sessions/${sessionId}`),
      fetch(`${apiBase}/api/observability/sessions/${sessionId}/events`)
    ])
    if (!sessionRes.ok) throw new Error(`Failed to load session (${sessionRes.status})`)
    if (!eventRes.ok) throw new Error(`Failed to load events (${eventRes.status})`)
    selectedSession.value = await sessionRes.json()
    events.value = await eventRes.json()
  } catch (err) {
    error.value = err.message || 'Failed to load session details'
  }
}

function closeSocket() {
  if (ws) {
    ws.close()
    ws = null
  }
  socketState.value = 'disconnected'
}

function connectSocket(sessionId) {
  closeSocket()
  if (!sessionId) return
  const wsBase = apiBase.replace(/^http/, 'ws')
  ws = new WebSocket(`${wsBase}/ws/sessions/${sessionId}`)
  socketState.value = 'connecting'

  ws.onopen = () => {
    socketState.value = 'connected'
  }

  ws.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data)
      if (parsed.type === 'heartbeat') return
      const exists = events.value.some(item => item.event_id === parsed.event_id)
      if (!exists) {
        events.value = [...events.value, parsed]
      }
    } catch {
      // ignore malformed frames for now
    }
  }

  ws.onerror = () => {
    socketState.value = 'error'
  }

  ws.onclose = () => {
    socketState.value = 'disconnected'
  }
}

watch(selectedSessionId, async (sessionId) => {
  await loadSessionDetail(sessionId)
  connectSocket(sessionId)
})

onMounted(async () => {
  await loadSessions()
  if (selectedSessionId.value) {
    await loadSessionDetail(selectedSessionId.value)
    connectSocket(selectedSessionId.value)
  }
})

onBeforeUnmount(() => {
  closeSocket()
})
</script>

<template>
  <div class="observability-page">
    <header class="page-header">
      <div>
        <h1>Session Monitor</h1>
        <p>Live view of workflow sessions, agent activity, and event streams.</p>
      </div>
      <button class="refresh-btn" @click="loadSessions">Refresh</button>
    </header>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="monitor-layout">
      <aside class="panel sessions-panel">
        <div class="panel-title-row">
          <h2>Sessions</h2>
          <span class="pill">{{ sessions.length }}</span>
        </div>

        <div v-if="loading" class="empty-state">Loading sessions...</div>
        <div v-else-if="sessions.length === 0" class="empty-state">No sessions yet.</div>

        <button
          v-for="session in sessions"
          :key="session.session_id"
          class="session-item"
          :class="{ active: session.session_id === selectedSessionId }"
          @click="selectedSessionId = session.session_id"
        >
          <div class="session-main">{{ session.workflow_id }}</div>
          <div class="session-meta">
            <span>{{ session.status }}</span>
            <span class="session-id">{{ session.session_id.slice(0, 8) }}</span>
          </div>
        </button>
      </aside>

      <section class="panel details-panel">
        <div class="panel-title-row">
          <h2>Session Detail</h2>
          <span class="pill status-pill">{{ socketState }}</span>
        </div>

        <div v-if="selectedSession" class="detail-grid">
          <div class="detail-card">
            <label>Workflow</label>
            <div>{{ selectedSession.workflow_id }}</div>
          </div>
          <div class="detail-card">
            <label>Status</label>
            <div>{{ selectedSession.status }}</div>
          </div>
          <div class="detail-card">
            <label>Current Agent</label>
            <div>{{ selectedSession.current_agent_id || '—' }}</div>
          </div>
          <div class="detail-card">
            <label>Current Node</label>
            <div>{{ selectedSession.current_node_id || '—' }}</div>
          </div>
          <div class="detail-card wide">
            <label>Session</label>
            <div>{{ selectedSessionLabel }}</div>
          </div>
        </div>
        <div v-else class="empty-state">Select a session to inspect.</div>
      </section>

      <section class="panel events-panel">
        <div class="panel-title-row">
          <h2>Event Stream</h2>
          <span class="pill">{{ events.length }}</span>
        </div>

        <div v-if="events.length === 0" class="empty-state">No events yet.</div>

        <div v-else class="event-list">
          <div v-for="item in [...events].reverse()" :key="item.event_id" class="event-item">
            <div class="event-type-row">
              <span class="event-type">{{ item.type }}</span>
              <span class="event-source">{{ item.source }}</span>
            </div>
            <div class="event-time">{{ item.timestamp }}</div>
            <pre class="event-payload">{{ JSON.stringify(item.payload, null, 2) }}</pre>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.observability-page {
  min-height: 100vh;
  background: #0e1116;
  color: #e8ecf3;
  padding: 24px;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px;
  font-size: 32px;
}

.page-header p {
  margin: 0;
  color: #9aa4b2;
}

.refresh-btn {
  background: linear-gradient(90deg, #7ee7c7, #7ab6ff);
  color: #091018;
  border: none;
  padding: 10px 18px;
  border-radius: 999px;
  font-weight: 700;
  cursor: pointer;
}

.error-banner {
  margin-bottom: 16px;
  background: rgba(255, 90, 90, 0.15);
  border: 1px solid rgba(255, 90, 90, 0.35);
  color: #ffb4b4;
  padding: 12px 14px;
  border-radius: 12px;
}

.monitor-layout {
  display: grid;
  grid-template-columns: 280px minmax(320px, 1fr) minmax(420px, 1.2fr);
  gap: 16px;
}

.panel {
  background: #151a22;
  border: 1px solid #222a36;
  border-radius: 18px;
  padding: 16px;
  min-height: 640px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
}

.panel-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.panel-title-row h2 {
  margin: 0;
  font-size: 18px;
}

.pill {
  background: #202938;
  color: #9ed4ff;
  border: 1px solid #2f3a4d;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
}

.status-pill {
  text-transform: capitalize;
}

.empty-state {
  color: #7f8b99;
  font-size: 14px;
  padding: 16px 0;
}

.session-item {
  width: 100%;
  text-align: left;
  background: #11161d;
  border: 1px solid #232d3a;
  border-radius: 14px;
  padding: 12px;
  color: #e8ecf3;
  cursor: pointer;
  margin-bottom: 10px;
}

.session-item.active {
  border-color: #7ab6ff;
  box-shadow: 0 0 0 1px rgba(122, 182, 255, 0.3);
}

.session-main {
  font-weight: 700;
  margin-bottom: 6px;
}

.session-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #9aa4b2;
  font-size: 12px;
}

.session-id {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-card {
  background: #10151c;
  border: 1px solid #222b37;
  border-radius: 14px;
  padding: 14px;
}

.detail-card.wide {
  grid-column: span 2;
}

.detail-card label {
  display: block;
  font-size: 12px;
  color: #8b97a6;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 760px;
  overflow: auto;
}

.event-item {
  background: #0f141a;
  border: 1px solid #202a35;
  border-radius: 14px;
  padding: 12px;
}

.event-type-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.event-type {
  font-weight: 700;
  color: #7ee7c7;
}

.event-source, .event-time {
  color: #8b97a6;
  font-size: 12px;
}

.event-payload {
  margin: 10px 0 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: #dbe4f0;
  font-size: 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

@media (max-width: 1200px) {
  .monitor-layout {
    grid-template-columns: 1fr;
  }

  .panel {
    min-height: auto;
  }
}
</style>
