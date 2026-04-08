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
const selectedRoomId = ref('')
const replyText = ref('')
const replyBusy = ref(false)
let ws = null

const pendingRequest = computed(() => selectedSession.value?.pending_human_request || null)

const sessionSummary = computed(() => {
  if (!selectedSession.value) return 'No live mission selected'
  return `${selectedSession.value.workflow_id} · ${selectedSession.value.status}`
})

const derivedAgents = computed(() => {
  const map = new Map()

  for (const event of events.value) {
    const payload = event.payload || {}
    const agentId = payload.agent_id || payload.node_id || (event.source && event.source !== 'session_manager' && event.source !== 'human' ? event.source : null)
    if (!agentId) continue
    if (!map.has(agentId)) {
      map.set(agentId, {
        id: agentId,
        name: agentId,
        status: 'idle',
        lastEventType: '',
        lastMessage: '',
        waiting: false,
      })
    }
    const agent = map.get(agentId)
    agent.lastEventType = event.type
    if (event.type === 'agent_started') agent.status = 'working'
    if (event.type === 'agent_completed') agent.status = 'idle'
    if (event.type === 'agent_waiting_for_human') {
      agent.status = 'waiting'
      agent.waiting = true
    }
    if (event.type === 'agent_message') {
      agent.lastMessage = payload.text || ''
    }
  }

  for (const item of messages.value) {
    if (item.sender_type !== 'agent') continue
    const agentId = item.sender_id
    if (!map.has(agentId)) {
      map.set(agentId, {
        id: agentId,
        name: agentId,
        status: 'idle',
        lastEventType: '',
        lastMessage: '',
        waiting: false,
      })
    }
    const agent = map.get(agentId)
    agent.lastMessage = item.message?.content || agent.lastMessage
  }

  const agents = [...map.values()]
  agents.sort((a, b) => a.name.localeCompare(b.name))
  return agents
})

const selectedRoom = computed(() => {
  if (!selectedRoomId.value) return derivedAgents.value[0] || null
  return derivedAgents.value.find(agent => agent.id === selectedRoomId.value) || derivedAgents.value[0] || null
})

const roomMessages = computed(() => {
  if (!selectedRoom.value) return []
  return messages.value.filter(item => item.sender_id === selectedRoom.value.id || item.sender_type === 'human')
})

const meetingFeed = computed(() => {
  return [...events.value]
    .filter(event => ['agent_message', 'human_message', 'agent_waiting_for_human', 'workflow_started', 'workflow_completed', 'workflow_failed'].includes(event.type))
    .slice()
    .reverse()
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
    if (!selectedRoomId.value && derivedAgents.value.length > 0) {
      selectedRoomId.value = derivedAgents.value[0].id
    }
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
  ws.onopen = () => { socketState.value = 'connected' }
  ws.onmessage = async (event) => {
    try {
      const parsed = JSON.parse(event.data)
      if (parsed.type === 'heartbeat') return
      const exists = events.value.some(item => item.event_id === parsed.event_id)
      if (!exists) events.value = [...events.value, parsed]
      if (['agent_message', 'human_message', 'agent_waiting_for_human', 'workflow_started', 'workflow_completed', 'workflow_failed', 'agent_started', 'agent_completed'].includes(parsed.type)) {
        await loadSessionDetail(selectedSessionId.value)
      }
    } catch {}
  }
  ws.onerror = () => { socketState.value = 'error' }
  ws.onclose = () => { socketState.value = 'disconnected' }
}

watch(selectedSessionId, async (sessionId) => {
  await loadSessionDetail(sessionId)
  connectSocket(sessionId)
})

watch(derivedAgents, (agents) => {
  if (!selectedRoomId.value && agents.length > 0) selectedRoomId.value = agents[0].id
  if (selectedRoomId.value && !agents.some(agent => agent.id === selectedRoomId.value) && agents.length > 0) {
    selectedRoomId.value = agents[0].id
  }
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
  <div class="office-page">
    <header class="office-header sakura-panel">
      <div>
        <div class="eyebrow">🌸 Agent Office</div>
        <h1>Cherry Operations Floor</h1>
        <p>Watch agents work in their rooms, follow meetings, and step in from the human desk.</p>
      </div>
      <div class="header-right">
        <div class="mission-chip">{{ sessionSummary }}</div>
        <button class="refresh-btn" @click="loadSessions">Refresh</button>
      </div>
    </header>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="office-layout">
      <aside class="left-column">
        <section class="panel sakura-panel session-panel">
          <div class="panel-title-row">
            <h2>Missions</h2>
            <span class="pill">{{ sessions.length }}</span>
          </div>
          <div v-if="loading" class="empty-state">Loading sessions...</div>
          <div v-else-if="sessions.length === 0" class="empty-state">No active missions.</div>
          <button v-for="session in sessions" :key="session.session_id" class="session-item" :class="{ active: session.session_id === selectedSessionId }" @click="selectedSessionId = session.session_id">
            <div class="session-main">{{ session.workflow_id }}</div>
            <div class="session-meta">
              <span>{{ session.status }}</span>
              <span>{{ session.session_id.slice(0, 8) }}</span>
            </div>
          </button>
        </section>

        <section class="panel sakura-panel rooms-panel">
          <div class="panel-title-row">
            <h2>Rooms</h2>
            <span class="pill">{{ derivedAgents.length }}</span>
          </div>
          <div v-if="derivedAgents.length === 0" class="empty-state">No agent rooms yet.</div>
          <button v-for="agent in derivedAgents" :key="agent.id" class="room-card" :class="{ active: selectedRoom?.id === agent.id }" @click="selectedRoomId = agent.id">
            <div class="room-top">
              <span class="room-name">{{ agent.name }}</span>
              <span class="room-status" :class="`status-${agent.status}`">{{ agent.status }}</span>
            </div>
            <div class="room-last">{{ agent.lastMessage || 'No message yet' }}</div>
          </button>
        </section>
      </aside>

      <main class="center-column">
        <section class="panel sakura-panel room-panel">
          <div class="panel-title-row">
            <h2>{{ selectedRoom ? `${selectedRoom.name}'s Room` : 'Room' }}</h2>
            <span class="pill">{{ socketState }}</span>
          </div>
          <div v-if="selectedRoom" class="room-stage">
            <div class="agent-avatar">🌸</div>
            <div class="room-summary-card sakura-soft-block">
              <div class="summary-label">Current mood</div>
              <div class="summary-value">{{ selectedRoom.status }}</div>
            </div>
            <div class="room-summary-card sakura-soft-block">
              <div class="summary-label">Last event</div>
              <div class="summary-value">{{ selectedRoom.lastEventType || '—' }}</div>
            </div>
          </div>
          <div v-else class="empty-state">Pick a room to inspect the agent.</div>

          <div class="room-conversation">
            <div class="subheading">Room Conversation</div>
            <div v-if="roomMessages.length === 0" class="empty-state">No room conversation yet.</div>
            <div v-else class="message-list">
              <div v-for="(item, idx) in [...roomMessages].reverse()" :key="idx" class="message-item sakura-soft-block">
                <div class="message-meta">{{ item.sender_type }} · {{ item.sender_id }}</div>
                <div class="message-text">{{ item.message?.content }}</div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <aside class="right-column">
        <section class="panel sakura-panel meeting-panel">
          <div class="panel-title-row">
            <h2>Meeting Room</h2>
            <span class="pill">{{ meetingFeed.length }}</span>
          </div>
          <div v-if="meetingFeed.length === 0" class="empty-state">No meetings yet.</div>
          <div v-else class="event-list">
            <div v-for="event in meetingFeed" :key="event.event_id" class="event-item sakura-soft-block">
              <div class="event-type-row">
                <span class="event-type">{{ event.type }}</span>
                <span class="event-source">{{ event.source }}</span>
              </div>
              <div class="event-time">{{ event.timestamp }}</div>
              <div class="meeting-payload">{{ event.payload?.text || event.payload?.task_description || JSON.stringify(event.payload) }}</div>
            </div>
          </div>
        </section>

        <section class="panel sakura-panel human-panel">
          <div class="panel-title-row">
            <h2>Human Desk</h2>
            <span class="pill" v-if="pendingRequest">waiting</span>
          </div>
          <div v-if="pendingRequest" class="pending-box sakura-soft-block">
            <div class="pending-title">{{ pendingRequest.node_id }} is asking for you</div>
            <div class="pending-text">{{ pendingRequest.task_description }}</div>
            <pre v-if="pendingRequest.inputs" class="pending-inputs">{{ pendingRequest.inputs }}</pre>
            <textarea v-model="replyText" class="reply-box" placeholder="Reply to the agent from your desk..."></textarea>
            <button class="reply-btn" :disabled="replyBusy || !replyText.trim()" @click="sendReply">
              {{ replyBusy ? 'Sending...' : 'Send Reply' }}
            </button>
          </div>
          <div v-else class="pending-box sakura-soft-block">
            <div class="pending-title">Open desk channel</div>
            <div class="pending-text">Send a message into the session even when no agent is currently waiting.</div>
            <textarea v-model="replyText" class="reply-box" placeholder="Write to the session from your desk..."></textarea>
            <button class="reply-btn" :disabled="replyBusy || !replyText.trim()" @click="sendReply">
              {{ replyBusy ? 'Sending...' : 'Send Message' }}
            </button>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.office-page {
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
.office-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  padding: 22px;
  border-radius: 22px;
  margin-bottom: 20px;
}
.eyebrow { color: #b25c82; font-size: 13px; font-weight: 700; margin-bottom: 10px; }
.office-header h1 { margin: 0 0 8px; font-size: 32px; color: #5b3041; }
.office-header p { margin: 0; color: #876473; }
.header-right { display: flex; align-items: center; gap: 12px; }
.mission-chip, .pill {
  background: rgba(255, 239, 246, 0.92);
  color: #af6287;
  border: 1px solid rgba(223, 156, 185, 0.26);
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
}
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
.office-layout {
  display: grid;
  grid-template-columns: 280px minmax(420px, 1fr) 360px;
  gap: 16px;
}
.left-column, .right-column { display: flex; flex-direction: column; gap: 16px; }
.center-column { min-width: 0; }
.panel { border-radius: 20px; padding: 16px; }
.panel-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.panel-title-row h2 { margin: 0; font-size: 18px; color: #6f4054; }
.empty-state { color: #8f7080; font-size: 14px; padding: 16px 0; }
.session-item, .room-card {
  width: 100%; text-align: left; background: rgba(255, 245, 249, 0.8); border: 1px solid rgba(223, 156, 185, 0.16); border-radius: 16px;
  padding: 12px; color: #5e3446; cursor: pointer; margin-bottom: 10px;
}
.session-item.active, .room-card.active { border-color: rgba(212, 126, 165, 0.5); box-shadow: 0 0 0 1px rgba(212, 126, 165, 0.18); }
.session-main, .room-name { font-weight: 700; }
.session-meta, .room-top { display: flex; justify-content: space-between; gap: 10px; color: #9b7485; font-size: 12px; }
.room-last { margin-top: 8px; color: #7d6170; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.room-status { border-radius: 999px; padding: 2px 8px; font-size: 11px; text-transform: capitalize; }
.status-working { background: rgba(255, 225, 236, 0.9); color: #b65580; }
.status-waiting { background: rgba(245, 220, 255, 0.9); color: #8d58b1; }
.status-idle { background: rgba(255, 245, 249, 0.9); color: #8d7080; }
.room-stage {
  display: grid;
  grid-template-columns: 90px 1fr 1fr;
  gap: 12px;
  align-items: stretch;
  margin-bottom: 18px;
}
.agent-avatar {
  display: flex; align-items: center; justify-content: center; font-size: 44px;
  background: rgba(255, 244, 249, 0.9); border: 1px solid rgba(223, 156, 185, 0.16); border-radius: 18px;
}
.room-summary-card { border-radius: 16px; padding: 14px; }
.summary-label { font-size: 12px; color: #9d7484; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.summary-value { color: #5b3041; font-weight: 700; }
.room-conversation .subheading { color: #b25c82; font-weight: 700; margin-bottom: 12px; }
.message-list, .event-list { display: flex; flex-direction: column; gap: 12px; max-height: 520px; overflow: auto; }
.message-item, .event-item, .pending-box { border-radius: 16px; padding: 12px; }
.message-meta, .event-source, .event-time { color: #9b7485; font-size: 12px; }
.message-text, .meeting-payload { margin-top: 6px; color: #5c3948; white-space: pre-wrap; word-break: break-word; }
.event-type-row { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.event-type { font-weight: 700; color: #c0678f; }
.pending-title { font-weight: 700; margin-bottom: 8px; color: #b25c82; }
.pending-text { color: #6d4857; margin-bottom: 10px; }
.pending-inputs { color: #8d6e7c; white-space: pre-wrap; word-break: break-word; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.reply-box {
  width: 100%; min-height: 110px; margin-top: 10px; border-radius: 14px; border: 1px solid rgba(223, 156, 185, 0.22);
  background: rgba(255, 255, 255, 0.7); color: #4a2a37; padding: 12px; box-sizing: border-box;
}
.reply-btn {
  margin-top: 12px; background: linear-gradient(90deg, #ffd5e6, #f2d6ff, #ffc5df); color: #6b3046; border: none;
  padding: 10px 16px; border-radius: 999px; font-weight: 700; cursor: pointer;
}
.reply-btn:disabled { opacity: 0.5; cursor: not-allowed; }
@media (max-width: 1350px) { .office-layout { grid-template-columns: 1fr; } }
</style>
