<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const apiBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:6400').replace(/\/$/, '')

const sessions = ref([])
const selectedSessionId = ref('')
const selectedSession = ref(null)
const events = ref([])
const messages = ref([])
const loading = ref(false)
const error = ref('')
const socketState = ref('disconnected')
const replyText = ref('')
const replyBusy = ref(false)
let ws = null

const selectedSessionLabel = computed(() => {
  if (!selectedSession.value) return 'No session selected'
  return `${selectedSession.value.workflow_id} · ${selectedSession.value.status}`
})

const pendingRequest = computed(() => selectedSession.value?.pending_human_request || null)

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
    const [sessionRes, eventRes, messageRes] = await Promise.all([
      fetch(`${apiBase}/api/observability/sessions/${sessionId}`),
      fetch(`${apiBase}/api/observability/sessions/${sessionId}/events`),
      fetch(`${apiBase}/api/observability/sessions/${sessionId}/messages`)
    ])
    if (!sessionRes.ok) throw new Error(`Failed to load session (${sessionRes.status})`)
    if (!eventRes.ok) throw new Error(`Failed to load events (${eventRes.status})`)
    if (!messageRes.ok) throw new Error(`Failed to load messages (${messageRes.status})`)
    selectedSession.value = await sessionRes.json()
    events.value = await eventRes.json()
    messages.value = await messageRes.json()
  } catch (err) {
    error.value = err.message || 'Failed to load session details'
  }
}

async function sendReply() {
  if (!selectedSessionId.value || !replyText.value.trim()) return
  replyBusy.value = true
  error.value = ''
  try {
    const endpoint = pendingRequest.value
      ? `${apiBase}/api/observability/sessions/${selectedSessionId.value}/reply`
      : `${apiBase}/api/observability/sessions/${selectedSessionId.value}/human-message`
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: replyText.value })
    })
    if (!response.ok) throw new Error(`Failed to send message (${response.status})`)
    replyText.value = ''
    await loadSessionDetail(selectedSessionId.value)
    await loadSessions()
  } catch (err) {
    error.value = err.message || 'Failed to send message'
  } finally {
    replyBusy.value = false
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

  ws.onmessage = async (event) => {
    try {
      const parsed = JSON.parse(event.data)
      if (parsed.type === 'heartbeat') return
      const exists = events.value.some(item => item.event_id === parsed.event_id)
      if (!exists) {
        events.value = [...events.value, parsed]
      }
      if (['agent_message', 'human_message', 'agent_waiting_for_human', 'workflow_started', 'workflow_completed', 'workflow_failed'].includes(parsed.type)) {
        await loadSessionDetail(selectedSessionId.value)
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
    <header class="page-header sakura-panel">
      <div>
        <div class="eyebrow">🌸 MyLittleAgent Monitor</div>
        <h1>Cherry Bloom Session Console</h1>
        <p>Watch sessions, follow agent activity, and gently step in when they need you.</p>
      </div>
      <button class="refresh-btn" @click="loadSessions">Refresh</button>
    </header>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="monitor-layout">
      <aside class="panel sessions-panel sakura-panel">
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

      <section class="panel details-panel sakura-panel">
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

        <div class="panel-subsection">
          <div class="panel-title-row compact">
            <h3>Human Console</h3>
            <span class="pill" v-if="pendingRequest">waiting</span>
          </div>
          <div v-if="pendingRequest" class="pending-box sakura-soft-block">
            <div class="pending-title">{{ pendingRequest.node_id }} needs input</div>
            <div class="pending-text">{{ pendingRequest.task_description }}</div>
            <pre v-if="pendingRequest.inputs" class="pending-inputs">{{ pendingRequest.inputs }}</pre>
            <textarea v-model="replyText" class="reply-box" placeholder="Type your reply to the agent here..."></textarea>
            <button class="reply-btn" :disabled="replyBusy || !replyText.trim()" @click="sendReply">
              {{ replyBusy ? 'Sending...' : 'Send Reply' }}
            </button>
          </div>
          <div v-else class="pending-box sakura-soft-block">
            <div class="pending-title">Open session chat</div>
            <div class="pending-text">Send a free-form message into the live session whenever you want.</div>
            <textarea v-model="replyText" class="reply-box" placeholder="Send a free-form message to the session..."></textarea>
            <button class="reply-btn" :disabled="replyBusy || !replyText.trim()" @click="sendReply">
              {{ replyBusy ? 'Sending...' : 'Send Message' }}
            </button>
          </div>
        </div>

        <div class="panel-subsection">
          <div class="panel-title-row compact">
            <h3>Messages</h3>
            <span class="pill">{{ messages.length }}</span>
          </div>
          <div v-if="messages.length === 0" class="empty-state">No messages yet.</div>
          <div v-else class="message-list">
            <div v-for="(item, idx) in [...messages].reverse()" :key="idx" class="message-item sakura-soft-block">
              <div class="message-meta">{{ item.sender_type }} · {{ item.sender_id }}</div>
              <div class="message-text">{{ item.message?.content }}</div>
            </div>
          </div>
        </div>
      </section>

      <section class="panel events-panel sakura-panel">
        <div class="panel-title-row">
          <h2>Event Stream</h2>
          <span class="pill">{{ events.length }}</span>
        </div>

        <div v-if="events.length === 0" class="empty-state">No events yet.</div>

        <div v-else class="event-list">
          <div v-for="item in [...events].reverse()" :key="item.event_id" class="event-item sakura-soft-block">
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
  background: transparent;
  color: #4a2a37;
  padding: 24px;
  box-sizing: border-box;
}

.sakura-panel {
  background: rgba(255, 250, 252, 0.72);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(223, 156, 185, 0.18);
  box-shadow: 0 20px 45px rgba(212, 142, 175, 0.14);
}

.sakura-soft-block {
  background: rgba(255, 246, 250, 0.76);
  border: 1px solid rgba(223, 156, 185, 0.15);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
  padding: 22px;
  border-radius: 22px;
}

.eyebrow {
  color: #b25c82;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 10px;
}

.page-header h1 { margin: 0 0 8px; font-size: 32px; color: #5b3041; }
.page-header p { margin: 0; color: #876473; }

.refresh-btn {
  background: linear-gradient(90deg, #ffd5e6, #f2d6ff, #ffc5df);
  color: #6b3046;
  border: none;
  padding: 10px 18px;
  border-radius: 999px;
  font-weight: 700;
  cursor: pointer;
}

.error-banner {
  margin-bottom: 16px;
  background: rgba(255, 132, 162, 0.14);
  border: 1px solid rgba(220, 102, 140, 0.28);
  color: #9e385d;
  padding: 12px 14px;
  border-radius: 12px;
}

.monitor-layout {
  display: grid;
  grid-template-columns: 280px minmax(420px, 1fr) minmax(420px, 1.1fr);
  gap: 16px;
}

.panel {
  border-radius: 20px;
  padding: 16px;
  min-height: 640px;
}

.panel-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.panel-title-row.compact h3 { margin: 0; font-size: 16px; color: #6f4054; }
.panel-title-row h2 { margin: 0; font-size: 18px; color: #6f4054; }
.pill {
  background: rgba(255, 239, 246, 0.92);
  color: #af6287;
  border: 1px solid rgba(223, 156, 185, 0.26);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
}
.status-pill { text-transform: capitalize; }
.empty-state { color: #8f7080; font-size: 14px; padding: 16px 0; }
.session-item {
  width: 100%; text-align: left; background: rgba(255, 245, 249, 0.8); border: 1px solid rgba(223, 156, 185, 0.16); border-radius: 16px;
  padding: 12px; color: #5e3446; cursor: pointer; margin-bottom: 10px;
}
.session-item.active { border-color: rgba(212, 126, 165, 0.5); box-shadow: 0 0 0 1px rgba(212, 126, 165, 0.18); }
.session-main { font-weight: 700; margin-bottom: 6px; }
.session-meta { display: flex; justify-content: space-between; gap: 10px; color: #9b7485; font-size: 12px; }
.session-id, .event-payload, .pending-inputs { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.detail-card { background: rgba(255, 247, 250, 0.82); border: 1px solid rgba(223, 156, 185, 0.14); border-radius: 16px; padding: 14px; }
.detail-card.wide { grid-column: span 2; }
.detail-card label { display: block; font-size: 12px; color: #9d7484; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.08em; }
.panel-subsection { margin-top: 18px; border-top: 1px solid rgba(223, 156, 185, 0.16); padding-top: 18px; }
.pending-box, .message-item, .event-item { border-radius: 16px; padding: 12px; }
.pending-title { font-weight: 700; margin-bottom: 8px; color: #b25c82; }
.pending-text { color: #6d4857; margin-bottom: 10px; }
.pending-inputs { color: #8d6e7c; white-space: pre-wrap; word-break: break-word; }
.reply-box {
  width: 100%; min-height: 110px; margin-top: 10px; border-radius: 14px; border: 1px solid rgba(223, 156, 185, 0.22);
  background: rgba(255, 255, 255, 0.7); color: #4a2a37; padding: 12px; box-sizing: border-box;
}
.reply-btn {
  margin-top: 12px; background: linear-gradient(90deg, #ffd5e6, #f2d6ff, #ffc5df); color: #6b3046; border: none;
  padding: 10px 16px; border-radius: 999px; font-weight: 700; cursor: pointer;
}
.reply-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.message-list, .event-list { display: flex; flex-direction: column; gap: 12px; max-height: 420px; overflow: auto; }
.message-meta, .event-source, .event-time { color: #9b7485; font-size: 12px; }
.message-text { margin-top: 6px; color: #5c3948; white-space: pre-wrap; word-break: break-word; }
.event-type-row { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.event-type { font-weight: 700; color: #c0678f; }
.event-payload { margin: 10px 0 0; white-space: pre-wrap; word-break: break-word; color: #694454; font-size: 12px; }
@media (max-width: 1200px) {
  .monitor-layout { grid-template-columns: 1fr; }
  .panel { min-height: auto; }
}
</style>
