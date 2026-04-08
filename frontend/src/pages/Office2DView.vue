<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { spriteFetcher } from '../utils/spriteFetcher.js'

const apiBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:6400').replace(/\/$/, '')

const sessions = ref([])
const selectedSessionId = ref('')
const selectedSession = ref(null)
const events = ref([])
const messages = ref([])
const error = ref('')
const loading = ref(false)
const replyText = ref('')
const replyBusy = ref(false)
const socketState = ref('disconnected')
let ws = null
let tickInterval = null

const now = ref(Date.now())

const world = {
  width: 1200,
  height: 760,
  rooms: {
    lobby: { id: 'lobby', label: 'Lobby', x: 40, y: 70, w: 150, h: 120, anchor: { x: 110, y: 135 } },
    desk_a: { id: 'desk_a', label: 'Desk A', x: 250, y: 90, w: 180, h: 130, anchor: { x: 320, y: 155 } },
    desk_b: { id: 'desk_b', label: 'Desk B', x: 470, y: 90, w: 180, h: 130, anchor: { x: 540, y: 155 } },
    desk_c: { id: 'desk_c', label: 'Desk C', x: 690, y: 90, w: 180, h: 130, anchor: { x: 760, y: 155 } },
    meeting: { id: 'meeting', label: 'Meeting Room', x: 260, y: 305, w: 280, h: 180, anchor: { x: 400, y: 390 } },
    human: { id: 'human', label: 'Human Desk', x: 610, y: 310, w: 220, h: 160, anchor: { x: 720, y: 390 } },
    coffee: { id: 'coffee', label: 'Coffee Time', x: 915, y: 520, w: 210, h: 150, anchor: { x: 1020, y: 595 } },
    ops: { id: 'ops', label: 'Mission Wall', x: 920, y: 85, w: 210, h: 170, anchor: { x: 1020, y: 170 } },
  }
}

const pendingRequest = computed(() => selectedSession.value?.pending_human_request || null)

const derivedAgents = computed(() => {
  const map = new Map()
  const deskPool = ['desk_a', 'desk_b', 'desk_c']

  const ensureAgent = (agentId) => {
    if (!map.has(agentId)) {
      const idx = map.size % deskPool.length
      map.set(agentId, {
        id: agentId,
        name: agentId,
        homeRoom: deskPool[idx],
        state: 'idle',
        room: 'lobby',
        lastMessage: '',
        lastEventType: '',
        activeAt: 0,
      })
    }
    return map.get(agentId)
  }

  for (const event of events.value) {
    const payload = event.payload || {}
    const agentId = payload.agent_id || payload.node_id || (event.source && !['session_manager', 'human'].includes(event.source) ? event.source : null)
    if (!agentId) continue
    const agent = ensureAgent(agentId)
    agent.lastEventType = event.type
    agent.activeAt = Date.parse(event.timestamp || '') || Date.now()
    if (event.type === 'agent_started') {
      agent.state = 'working'
      agent.room = agent.homeRoom
    } else if (event.type === 'agent_completed') {
      agent.state = 'idle'
      agent.room = 'coffee'
    } else if (event.type === 'agent_waiting_for_human') {
      agent.state = 'waiting'
      agent.room = 'human'
    } else if (event.type === 'agent_message') {
      agent.lastMessage = payload.text || ''
      if (payload.text) {
        agent.state = 'talking'
        agent.room = agent.homeRoom
      }
    }
  }

  for (const item of messages.value) {
    if (item.sender_type !== 'agent') continue
    const agent = ensureAgent(item.sender_id)
    agent.lastMessage = item.message?.content || agent.lastMessage
  }

  return [...map.values()].sort((a, b) => a.name.localeCompare(b.name))
})

const agentEntities = computed(() => {
  const meetingParticipants = new Set(
    [...events.value]
      .filter(event => event.type === 'agent_message')
      .slice(-4)
      .map(event => event.payload?.agent_id || event.source)
      .filter(Boolean)
  )

  return derivedAgents.value.map((agent, index) => {
    let roomId = agent.room || agent.homeRoom
    if (meetingParticipants.has(agent.id) && agent.state !== 'waiting') {
      roomId = 'meeting'
    }
    const isCoffeeIdle = agent.state === 'idle' && Date.now() - agent.activeAt > 8000
    if (isCoffeeIdle) {
      roomId = 'coffee'
    }

    const room = world.rooms[roomId] || world.rooms.lobby
    const baseOffsetX = ((index % 3) - 1) * 26
    const baseOffsetY = (Math.floor(index / 3) % 2) * 30 - 12
    const walking = !isCoffeeIdle && ['working', 'talking', 'waiting'].includes(agent.state)
    const bob = walking ? Math.sin((now.value / 260) + index) * 3 : 0
    const phase = walking ? (Math.floor((now.value / 180) % 3) + 1) : 1

    let stance = 'D'
    if (roomId === 'meeting') stance = 'R'
    else if (roomId === 'human') stance = 'U'
    else if (roomId === 'coffee') stance = 'D'
    else if (roomId.startsWith('desk')) stance = 'D'

    return {
      ...agent,
      x: room.anchor.x + baseOffsetX,
      y: room.anchor.y + baseOffsetY + bob,
      roomId,
      bubble: agent.lastMessage ? agent.lastMessage.slice(0, 48) : '',
      sprite: spriteFetcher.fetchSprite(agent.id, stance, phase),
      walking,
      isCoffeeIdle,
    }
  })
})

const missionLabel = computed(() => {
  if (!selectedSession.value) return 'No mission selected'
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

onMounted(async () => {
  tickInterval = window.setInterval(() => { now.value = Date.now() }, 120)
  await loadSessions()
  if (selectedSessionId.value) {
    await loadSessionDetail(selectedSessionId.value)
    connectSocket(selectedSessionId.value)
  }
})

onBeforeUnmount(() => {
  closeSocket()
  if (tickInterval) window.clearInterval(tickInterval)
})
</script>

<template>
  <div class="office2d-page">
    <header class="office-header sakura-panel">
      <div>
        <div class="eyebrow">🌸 Pixel Office Simulation</div>
        <h1>MyLittleAgent Office 2D</h1>
        <p>Watch the team work, meet, ask for help, and drift to coffee time like a tiny pixel world.</p>
      </div>
      <div class="header-right">
        <div class="mission-chip">{{ missionLabel }}</div>
        <div class="mission-chip">socket: {{ socketState }}</div>
        <button class="refresh-btn" @click="loadSessions">Refresh</button>
      </div>
    </header>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="layout">
      <aside class="sidebar-panel sakura-panel">
        <div class="panel-title-row">
          <h2>Missions</h2>
          <span class="pill">{{ sessions.length }}</span>
        </div>
        <div v-if="loading" class="empty-state">Loading sessions...</div>
        <div v-else-if="sessions.length === 0" class="empty-state">No missions yet.</div>
        <button v-for="session in sessions" :key="session.session_id" class="session-item" :class="{ active: session.session_id === selectedSessionId }" @click="selectedSessionId = session.session_id">
          <div class="session-main">{{ session.workflow_id }}</div>
          <div class="session-meta">
            <span>{{ session.status }}</span>
            <span>{{ session.session_id.slice(0, 8) }}</span>
          </div>
        </button>

        <div class="panel-subsection">
          <div class="panel-title-row compact">
            <h3>Human Desk</h3>
            <span class="pill" v-if="pendingRequest">waiting</span>
          </div>
          <div v-if="pendingRequest" class="pending-box sakura-soft-block">
            <div class="pending-title">{{ pendingRequest.node_id }} needs you</div>
            <div class="pending-text">{{ pendingRequest.task_description }}</div>
            <textarea v-model="replyText" class="reply-box" placeholder="Reply to the agent..."></textarea>
            <button class="reply-btn" :disabled="replyBusy || !replyText.trim()" @click="sendReply">
              {{ replyBusy ? 'Sending...' : 'Send Reply' }}
            </button>
          </div>
          <div v-else class="pending-box sakura-soft-block">
            <div class="pending-title">Open channel</div>
            <div class="pending-text">Send a message into the live session whenever you want.</div>
            <textarea v-model="replyText" class="reply-box" placeholder="Talk to the team from the office..."></textarea>
            <button class="reply-btn" :disabled="replyBusy || !replyText.trim()" @click="sendReply">
              {{ replyBusy ? 'Sending...' : 'Send Message' }}
            </button>
          </div>
        </div>
      </aside>

      <main class="sim-panel sakura-panel">
        <div class="sim-world" :style="{ width: `${world.width}px`, height: `${world.height}px` }">
          <div v-for="room in Object.values(world.rooms)" :key="room.id" class="room" :class="`room-${room.id}`" :style="{ left: `${room.x}px`, top: `${room.y}px`, width: `${room.w}px`, height: `${room.h}px` }">
            <div class="room-label">{{ room.label }}</div>
            <div v-if="room.id.startsWith('desk')" class="desk-computer">🖥️</div>
            <div v-if="room.id === 'meeting'" class="meeting-table">◯</div>
            <div v-if="room.id === 'coffee'" class="coffee-machine">☕</div>
            <div v-if="room.id === 'human'" class="human-computer">💻</div>
            <div v-if="room.id === 'ops'" class="ops-board">📋</div>
          </div>

          <div class="hallway horizontal" style="left: 180px; top: 245px; width: 760px;"></div>
          <div class="hallway vertical" style="left: 880px; top: 240px; height: 320px;"></div>

          <div class="human-avatar" :style="{ left: `${world.rooms.human.anchor.x - 18}px`, top: `${world.rooms.human.anchor.y + 32}px` }">
            <img class="human-sprite" :src="spriteFetcher.fetchSprite('human-desk', 'D', 1)" alt="Human sprite" />
            <div class="name-tag">You</div>
          </div>

          <div v-for="agent in agentEntities" :key="agent.id" class="agent" :style="{ left: `${agent.x}px`, top: `${agent.y}px` }">
            <div class="speech-bubble" v-if="agent.state === 'talking' || agent.state === 'waiting'">{{ agent.state === 'waiting' ? 'Need input!' : agent.bubble || '...' }}</div>
            <img class="agent-sprite" :class="{ 'sprite-walking': agent.walking, 'sprite-resting': agent.isCoffeeIdle }" :src="agent.sprite" :alt="`${agent.name} sprite`" />
            <div class="name-tag">{{ agent.name }}</div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.office2d-page {
  min-height: 100vh;
  background: transparent;
  color: #4a2a37;
  padding: 24px;
  box-sizing: border-box;
}
.sakura-panel {
  background: rgba(255, 250, 252, 0.74);
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
.header-right { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; justify-content: flex-end; }
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
.layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 16px;
}
.sidebar-panel {
  border-radius: 20px;
  padding: 16px;
}
.panel-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.panel-title-row h2, .panel-title-row h3 { margin: 0; color: #6f4054; }
.panel-title-row h2 { font-size: 18px; }
.panel-title-row h3 { font-size: 16px; }
.empty-state { color: #8f7080; font-size: 14px; padding: 16px 0; }
.session-item {
  width: 100%; text-align: left; background: rgba(255, 245, 249, 0.8); border: 1px solid rgba(223, 156, 185, 0.16); border-radius: 16px;
  padding: 12px; color: #5e3446; cursor: pointer; margin-bottom: 10px;
}
.session-item.active { border-color: rgba(212, 126, 165, 0.5); box-shadow: 0 0 0 1px rgba(212, 126, 165, 0.18); }
.session-main { font-weight: 700; margin-bottom: 6px; }
.session-meta { display: flex; justify-content: space-between; gap: 10px; color: #9b7485; font-size: 12px; }
.panel-subsection { margin-top: 18px; border-top: 1px solid rgba(223, 156, 185, 0.16); padding-top: 18px; }
.pending-box { border-radius: 16px; padding: 12px; }
.pending-title { font-weight: 700; margin-bottom: 8px; color: #b25c82; }
.pending-text { color: #6d4857; margin-bottom: 10px; }
.reply-box {
  width: 100%; min-height: 110px; margin-top: 10px; border-radius: 14px; border: 1px solid rgba(223, 156, 185, 0.22);
  background: rgba(255, 255, 255, 0.7); color: #4a2a37; padding: 12px; box-sizing: border-box;
}
.reply-btn {
  margin-top: 12px; background: linear-gradient(90deg, #ffd5e6, #f2d6ff, #ffc5df); color: #6b3046; border: none;
  padding: 10px 16px; border-radius: 999px; font-weight: 700; cursor: pointer;
}
.reply-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.sim-panel {
  border-radius: 20px;
  padding: 16px;
  overflow: auto;
}
.sim-world {
  position: relative;
  margin: 0 auto;
  background:
    linear-gradient(0deg, rgba(255,255,255,0.28) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.28) 1px, transparent 1px),
    linear-gradient(180deg, #fffdfd 0%, #fff6fa 100%);
  background-size: 24px 24px, 24px 24px, auto;
  border-radius: 22px;
  border: 1px solid rgba(223, 156, 185, 0.18);
  overflow: hidden;
}
.room {
  position: absolute;
  border-radius: 12px;
  border: 2px solid rgba(213, 132, 169, 0.32);
  background: rgba(255, 241, 246, 0.7);
  box-shadow: inset 0 0 0 2px rgba(255,255,255,0.26);
}
.room-label {
  position: absolute;
  top: 8px;
  left: 10px;
  font-size: 12px;
  font-weight: 700;
  color: #a35b79;
}
.desk-computer, .coffee-machine, .human-computer, .ops-board, .meeting-table {
  position: absolute;
  font-size: 34px;
}
.desk-computer { right: 14px; bottom: 12px; }
.meeting-table { left: 50%; top: 50%; transform: translate(-50%, -50%); font-size: 70px; color: #d28da8; }
.coffee-machine { right: 20px; bottom: 16px; }
.human-computer { right: 18px; bottom: 16px; }
.ops-board { right: 22px; bottom: 18px; }
.hallway {
  position: absolute;
  background: rgba(247, 223, 234, 0.7);
  border-radius: 999px;
}
.hallway.horizontal { height: 34px; }
.hallway.vertical { width: 34px; }
.agent, .human-avatar {
  position: absolute;
  transform: translate(-50%, -50%);
}
.agent-sprite, .human-sprite {
  width: 42px;
  height: 52px;
  image-rendering: pixelated;
  filter: drop-shadow(0 4px 0 rgba(143, 93, 111, 0.14));
}
.sprite-walking {
  animation: spriteHop 0.28s ease-in-out infinite alternate;
}
.sprite-resting {
  animation: none;
}
@keyframes spriteHop {
  0% { transform: translateY(0); }
  100% { transform: translateY(-2px); }
}
.name-tag {
  margin-top: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(223, 156, 185, 0.18);
  font-size: 11px;
  font-weight: 700;
  color: #8d5570;
  white-space: nowrap;
  transform: translateX(-12%);
}
.speech-bubble {
  position: absolute;
  bottom: 58px;
  left: 50%;
  transform: translateX(-50%);
  min-width: 72px;
  max-width: 160px;
  background: rgba(255,255,255,0.95);
  border: 1px solid rgba(223, 156, 185, 0.22);
  color: #6a4654;
  padding: 6px 10px;
  border-radius: 12px;
  font-size: 11px;
  line-height: 1.35;
  box-shadow: 0 10px 20px rgba(212, 142, 175, 0.12);
}
.speech-bubble::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -6px;
  width: 10px;
  height: 10px;
  background: rgba(255,255,255,0.95);
  border-right: 1px solid rgba(223, 156, 185, 0.22);
  border-bottom: 1px solid rgba(223, 156, 185, 0.22);
  transform: translateX(-50%) rotate(45deg);
}
@media (max-width: 1380px) {
  .layout { grid-template-columns: 1fr; }
  .sim-panel { overflow: auto; }
}
</style>
