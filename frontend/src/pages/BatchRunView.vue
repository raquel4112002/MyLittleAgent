<template>
  <div class="launch-view">
    <div class="launch-bg"></div>
    <div class="header sakura-panel">
      <div>
        <div class="eyebrow">🌸 Batch Garden</div>
        <h1>MyLittleAgent Lab</h1>
      </div>
      <button class="settings-button" @click="showBatchSettingsModal()" title="Batch Settings">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
      </button>
    </div>
    <div class="content">
      <div class="left-panel">
        <div v-if="viewMode === 'terminal'" class="log-box sakura-panel">
          <div class="log-messages" ref="logMessagesRef">
            <div v-for="(logMessage, index) in logMessages" :key="index" class="log-message">
              <span :class="`log-timestamp log-timestamp-${logMessage.type}`">{{ logMessage.timestamp }}</span> : {{ logMessage.message }}
            </div>
            <div v-if="logMessages.length === 0" class="log-placeholder">Batch processing logs will bloom here...</div>
          </div>
        </div>

        <div v-if="viewMode === 'dashboard'" class="dashboard-box sakura-panel">
          <div class="dashboard-content">
            <div class="metrics-grid">
              <div class="metric-card" :class="{ 'status-active': status === 'In Progress' }">
                <div class="metric-title">Rows Completed</div>
                <div class="metric-value">{{ completedRows }}</div>
              </div>
              <div class="metric-card" :class="{ 'status-active': status === 'In Progress' }">
                <div class="metric-title">Total Time</div>
                <div class="metric-value">{{ totalTime }}</div>
              </div>
              <div class="metric-card" :class="{ 'status-active': status === 'In Progress' }">
                <div class="metric-title">Success Rate</div>
                <div class="metric-value">{{ successRate }}</div>
              </div>
              <div class="metric-card" :class="{ 'status-active': status === 'In Progress' }">
                <div class="metric-title">Current Status</div>
                <div class="metric-value" :class="{ 'status-active': status === 'In Progress' }">{{ computedStatus }}</div>
              </div>
            </div>

            <div class="progress-section">
              <div class="progress-label">Overall Progress</div>
              <div class="progress-bar" :style="{ '--process-width': progressPercentage + '%'}">
                <div class="progress-fill" :class="{ 'processing': status === 'In Progress' }" :style="{ width: progressPercentage + '%' }"></div>
              </div>
              <div class="progress-text">{{ progressPercentage }}%</div>
            </div>
          </div>
        </div>
      </div>

      <div class="right-panel">
        <div class="control-section sakura-panel">
          <label class="section-label">Workflow Selection</label>
          <div class="select-wrapper custom-file-selector" ref="fileSelectorWrapperRef">
            <input
              ref="fileSelectorInputRef"
              v-model="fileSearchQuery"
              type="text"
              class="file-selector-input"
              :placeholder="loading ? 'Loading...' : 'Select YAML file...'"
              :disabled="loading || isWorkflowRunning"
              @focus="handleFileInputFocus"
              @input="handleFileInputChange"
              @keydown.enter.prevent="handleFileInputEnter"
              @blur="handleFileInputBlur"
            />
            <div class="select-arrow">▼</div>
            <Transition name="file-dropdown">
              <ul v-if="isFileDropdownOpen" class="file-dropdown">
                <li v-for="workflow in filteredWorkflowFiles" :key="workflow.name" class="file-option" @mousedown.prevent="selectWorkflow(workflow.name)">
                  <span class="file-name">{{ workflow.name }}</span>
                  <span v-if="workflow.description" class="file-desc">{{ workflow.description }}</span>
                </li>
                <li v-if="!filteredWorkflowFiles.length" class="file-empty">No results</li>
              </ul>
            </Transition>
          </div>

          <label class="section-label">Input File Selection</label>
          <div class="input-file-section">
            <div class="file-upload-wrapper">
              <input ref="inputFileInputRef" type="file" accept=".xlsx,.csv" class="hidden-file-input" @change="onInputFileSelected" />
              <button type="button" class="file-upload-button" :disabled="loading || isWorkflowRunning" @click="handleInputFileButtonClick">
                {{ selectedInputFile ? selectedInputFile.name : 'Select input file...' }}
              </button>
            </div>
          </div>

          <div class="input-manual">
            <div class="manual-title" @click="showColumnGuideModal = true">
              Input File Format
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="info-icon">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                <path d="M12 17h.01"></path>
              </svg>
            </div>
          </div>

          <label class="section-label">View</label>
          <div class="view-toggle">
            <button class="toggle-button" :class="{ active: viewMode === 'dashboard' }" @click="switchToDashboard">Dashboard</button>
            <button class="toggle-button" :class="{ active: viewMode === 'terminal' }" @click="viewMode = 'terminal'">Terminal</button>
          </div>

          <div class="button-section">
            <button class="launch-button" :class="{ glow: shouldGlow, 'is-sending': isWorkflowRunning }" @click="handleButtonClick" :disabled="isLaunchButtonDisabled">
              {{ buttonLabel }}
            </button>
            <button class="cancel-button" :disabled="status !== 'In Progress'" @click="cancelBatchWorkflow">Cancel</button>
            <button class="download-button" :disabled="status !== 'Batch completed' && status !== 'Batch cancelled'" @click="downloadLogs">Download Logs</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <Transition name="image-modal">
    <div v-if="selectedArtifactImage" class="image-modal" @click.self="closeImageModal">
      <div class="image-modal-content sakura-panel">
        <img :src="selectedArtifactImage.src" :alt="selectedArtifactImage.name" :click="closeImageModal" />
      </div>
    </div>
  </Transition>

  <SettingsModal :is-visible="showSettingsModal" @update:is-visible="showSettingsModal = $event" />

  <Transition name="modal">
    <div v-if="showColumnGuideModal" class="column-guide-modal-overlay" @click.self="showColumnGuideModal = false">
      <div class="column-guide-modal sakura-panel">
        <div class="modal-content">
          <div class="manual-content">
            <div class="manual-item">Input file should contain at least <code>task</code> and/or <code>attachments</code> columns</div>
            <div class="manual-item"><code>id</code> - Must be unique, auto-generated if column not found</div>
            <div class="manual-item"><code>task</code> - Holds user input</div>
            <div class="manual-item">
              <code>vars</code> - JSON object containing key-value pairs of global variables
              <div class="manual-example"><pre>{{ JSON.stringify({"BASE_URL": "openai.com","API_KEY": "123"}, null, 2) }}</pre></div>
            </div>
            <div class="manual-item">
              <code>attachments</code> - JSON array containing absolute file paths of attachments for workflow
              <div class="manual-example"><pre>{{ JSON.stringify(["C:\\a_sheep.png"], null, 2) }}</pre></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>

  <Transition name="modal">
    <div v-if="isBatchSettingsModalVisible" class="batch-settings-modal-overlay" @click.self="isBatchSettingsModalVisible = false">
      <div class="batch-settings-modal sakura-panel">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <div class="eyebrow">🌸 Batch Preferences</div>
              <h3>Lab Settings</h3>
            </div>
            <button class="close-button" @click="isBatchSettingsModalVisible = false">×</button>
          </div>
          <div class="modal-body">
            <div class="settings-item">
              <label class="setting-label">Max. Parallel Launches</label>
              <input type="number" v-model.number="maxParallel" class="setting-input" min="1" max="50" step="1" />
              <p class="setting-desc">Maximum number of parallel workflow launches</p>
            </div>
            <div class="settings-item">
              <label class="setting-label">Log Level</label>
              <select v-model="logLevel" class="setting-select">
                <option v-for="level in logLevelOptions" :key="level" :value="level">{{ level }}</option>
              </select>
              <p class="setting-desc">Logging verbosity level</p>
            </div>
          </div>
          <div class="modal-footer">
            <button class="cancel-button" @click="isBatchSettingsModalVisible = false">Cancel</button>
            <button class="confirm-button" @click="isBatchSettingsModalVisible = false">Save</button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { fetchWorkflowsWithDesc, fetchLogsZip, postBatchWorkflow } from '../utils/apiFunctions.js'
import SettingsModal from '../components/SettingsModal.vue'

const router = useRouter()
const route = useRoute()
const logMessages = ref([])
const logMessagesRef = ref(null)
const LOG_TYPES = { COMPLETED: 'completed', FAILED: 'failed', DEFAULT: 'default' }
const taskPrompt = ref('')
const workflowFiles = ref([])
const selectedYamlFile = ref('')
const fileSearchQuery = ref('')
const isFileSearchDirty = ref(false)
const isFileDropdownOpen = ref(false)
const fileSelectorWrapperRef = ref(null)
const fileSelectorInputRef = ref(null)
const status = ref('Idle')
const loading = ref(false)
const computedStatus = computed(() => {
  if (loading.value) return 'Loading...'
  if (status.value === 'Pending workflow selection') return status.value
  if (!selectedYamlFile.value) return 'Pending workflow selection'
  if (!selectedInputFile.value) return 'Pending file selection'
  return status.value
})
let sessionIdToDownload = null
const shouldGlow = ref(false)
const attachmentInputRef = ref(null)
const uploadedAttachments = ref([])
const selectedArtifactImage = ref(null)
const selectedInputFile = ref(null)
const inputFileInputRef = ref(null)
const isConnectionReady = ref(false)
const showSettingsModal = ref(false)
const isBatchSettingsModalVisible = ref(false)
const showColumnGuideModal = ref(false)
const maxParallel = ref(5)
const logLevel = ref('INFO')
const logLevelOptions = ['INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL']
const viewMode = ref('dashboard')
const totalRowsCount = ref(0)
const completedRowsCount = ref(0)
const successfulTasks = ref(0)
const failedTasks = ref(0)
const batchStartTime = ref(null)
const batchEndTime = ref(null)
let timerInterval = null
const currentTime = ref(Date.now())
const startTimer = () => {
  if (timerInterval) return
  timerInterval = setInterval(() => { currentTime.value = Date.now() }, 10)
}
const stopTimer = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}
const completedRows = computed(() => totalRowsCount.value === 0 ? '-' : `${completedRowsCount.value}/${totalRowsCount.value}`)
const totalTime = computed(() => {
  if (!batchStartTime.value) return '00:00:00:00'
  const endTime = batchEndTime.value || currentTime.value
  const duration = endTime - batchStartTime.value
  const hours = Math.floor(duration / (1000 * 60 * 60))
  const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((duration % (1000 * 60)) / 1000)
  const centiseconds = Math.floor((duration % 1000) / 10)
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}:${centiseconds.toString().padStart(2, '0')}`
})
const successRate = computed(() => {
  const totalProcessed = successfulTasks.value + failedTasks.value
  if (totalProcessed === 0) return '0%'
  const rate = (successfulTasks.value / totalProcessed) * 100
  return `${Math.round(rate)}%`
})
const progressPercentage = computed(() => totalRowsCount.value === 0 ? 0 : Math.round((completedRowsCount.value / totalRowsCount.value) * 100))
let ws = null
let sessionId = null
const filteredWorkflowFiles = computed(() => {
  if (!isFileSearchDirty.value) return workflowFiles.value
  const query = fileSearchQuery.value.trim().toLowerCase()
  if (!query) return workflowFiles.value
  return workflowFiles.value.filter((workflow) => workflow.name?.toLowerCase().includes(query))
})
const buttonLabel = computed(() => (status.value === 'Batch completed' || status.value === 'Batch cancelled') ? 'Relaunch' : 'Launch')
const isLaunchButtonDisabled = computed(() => {
  if (loading.value) return true
  if (status.value === 'Batch completed' || status.value === 'Batch cancelled') return false
  if (!isConnectionReady.value) return true
  if (!selectedYamlFile.value || !selectedInputFile.value) return true
  return false
})
const clearUploadedAttachments = () => {
  uploadedAttachments.value = []
  if (attachmentInputRef.value) attachmentInputRef.value.value = ''
}
const resetConnectionState = ({ closeSocket = true, clearInputFile = true } = {}) => {
  if (closeSocket && ws) {
    try { ws.close() } catch (closeError) { console.warn('Failed to close WebSocket:', closeError) }
  }
  ws = null
  sessionId = null
  isConnectionReady.value = false
  shouldGlow.value = false
  isWorkflowRunning.value = false
  stopTimer()
  totalRowsCount.value = 0
  completedRowsCount.value = 0
  successfulTasks.value = 0
  failedTasks.value = 0
  batchStartTime.value = null
  batchEndTime.value = null
  if (clearInputFile) removeInputFile()
}
const isWorkflowRunning = ref(false)
const applyWorkflowFromRoute = () => {
  let workflowParam = route.query?.workflow || route.query?.file || route.query?.name
  if (Array.isArray(workflowParam)) workflowParam = workflowParam[0]
  if (!workflowParam || typeof workflowParam !== 'string') return
  let fileName = workflowParam.trim()
  if (!fileName) return
  if (!fileName.toLowerCase().endsWith('.yaml')) fileName = `${fileName}.yaml`
  selectedYamlFile.value = fileName
  fileSearchQuery.value = fileName
  isFileSearchDirty.value = false
}
const loadWorkflows = async () => {
  loading.value = true
  const result = await fetchWorkflowsWithDesc()
  loading.value = false
  if (result.success) {
    workflowFiles.value = result.workflows
    applyWorkflowFromRoute()
  } else {
    console.error('Failed to load workflows:', result.error)
  }
}
const openFileDropdown = () => {
  if (loading.value || isWorkflowRunning.value) return
  isFileDropdownOpen.value = true
}
const handleFileInputFocus = () => {
  isFileSearchDirty.value = false
  openFileDropdown()
  if (fileSearchQuery.value?.trim()) nextTick(() => fileSelectorInputRef.value?.select())
}
const handleFileInputChange = () => {
  if (loading.value || isWorkflowRunning.value) return
  isFileSearchDirty.value = true
  openFileDropdown()
}
const closeFileDropdown = () => { isFileDropdownOpen.value = false }
const selectWorkflow = (fileName) => {
  if (!fileName) return
  selectedYamlFile.value = fileName
  fileSearchQuery.value = fileName
  isFileSearchDirty.value = false
  closeFileDropdown()
  fileSelectorInputRef.value?.blur()
  router.push({ query: { ...route.query, workflow: fileName } })
}
const handleFileInputEnter = () => {
  const [firstMatch] = filteredWorkflowFiles.value
  if (firstMatch) selectWorkflow(firstMatch.name)
}
const resetFileSearchQuery = () => {
  fileSearchQuery.value = selectedYamlFile.value || ''
  isFileSearchDirty.value = false
}
const handleFileInputBlur = () => {
  setTimeout(() => {
    if (!isFileDropdownOpen.value) resetFileSearchQuery()
  }, 120)
}
const handleClickOutside = (event) => {
  if (isFileDropdownOpen.value && fileSelectorWrapperRef.value && !fileSelectorWrapperRef.value.contains(event.target)) {
    closeFileDropdown()
    resetFileSearchQuery()
  }
}
const formatLogTimestamp = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  const milliseconds = String(date.getMilliseconds()).padStart(3, '0')
  return `${month}/${day} - ${hours}:${minutes}:${seconds}.${milliseconds}`
}
const addLogMessage = (message, type = LOG_TYPES.DEFAULT) => {
  const timestamp = formatLogTimestamp(Date.now())
  logMessages.value.push({ timestamp, message, type })
}
const handleInputFileButtonClick = () => {
  if (loading.value || isWorkflowRunning.value) return
  inputFileInputRef.value?.click()
}
const onInputFileSelected = (event) => {
  const file = event.target?.files?.[0]
  if (event.target) event.target.value = ''
  if (!file) return
  const allowedExtensions = ['.xlsx', '.csv']
  const fileName = file.name.toLowerCase()
  const isValidType = allowedExtensions.some(ext => fileName.endsWith(ext))
  if (!isValidType) {
    alert('Please select a valid file (.xlsx or .csv)')
    return
  }
  selectedInputFile.value = file
}
const removeInputFile = () => {
  selectedInputFile.value = null
  if (inputFileInputRef.value) inputFileInputRef.value.value = ''
}
const lockBodyScroll = () => { if (typeof document !== 'undefined') document.body.style.overflow = 'hidden' }
const unlockBodyScroll = () => { if (typeof document !== 'undefined') document.body.style.overflow = '' }
const closeImageModal = () => {
  if (!selectedArtifactImage.value) return
  selectedArtifactImage.value = null
  unlockBodyScroll()
}
const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    if (selectedArtifactImage.value) closeImageModal()
    else if (showColumnGuideModal.value) showColumnGuideModal.value = false
    else if (isBatchSettingsModalVisible.value) isBatchSettingsModalVisible.value = false
  }
}
const showBatchSettingsModal = () => { isBatchSettingsModalVisible.value = true }
const handleYAMLSelection = async (fileName) => {
  if (!fileName) {
    logMessages.value = []
    totalRowsCount.value = 0
    completedRowsCount.value = 0
    successfulTasks.value = 0
    failedTasks.value = 0
    batchStartTime.value = null
    batchEndTime.value = null
    return
  }
  logMessages.value = []
}
const handleButtonClick = () => {
  if (status.value === 'Batch completed' || status.value === 'Batch cancelled') {
    if (!selectedYamlFile.value) { alert('Please choose a workflow file!'); return }
    if (!selectedInputFile.value) { alert('Please select an input file (.xlsx or .csv)'); return }
    resetConnectionState()
    status.value = 'Connecting...'
    handleYAMLSelection(selectedYamlFile.value)
    establishWebSocketConnection()
  } else {
    launchBatchWorkflow()
  }
}
const establishWebSocketConnection = () => {
  resetConnectionState()
  if (!selectedYamlFile.value) return
  const apiBase = import.meta.env.VITE_API_BASE_URL || ''
  const defaultScheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  let scheme = defaultScheme
  let host = window.location.host
  if (!import.meta.env.DEV && apiBase) {
    try {
      const api = new URL(apiBase, window.location.origin)
      scheme = api.protocol === 'https:' ? 'wss:' : 'ws:'
      host = api.host
    } catch {}
  }
  const wsUrl = `${scheme}//${host}/ws`
  const socket = new WebSocket(wsUrl)
  ws = socket
  socket.onopen = () => { if (ws !== socket) return }
  socket.onmessage = (event) => {
    if (ws !== socket) return
    const msg = JSON.parse(event.data)
    if (msg.type === 'connection') {
      sessionId = msg.data?.session_id || null
      if (!sessionId) {
        status.value = 'Connection error'
        alert('Missing session information from server.')
        resetConnectionState()
        return
      }
      isConnectionReady.value = true
      shouldGlow.value = true
      status.value = 'Pending launch'
    } else {
      processBatchMessage(msg)
    }
  }
  socket.onerror = () => {
    if (ws !== socket) return
    status.value = 'Connection error'
    alert('WebSocket connection error!')
    resetConnectionState({ closeSocket: false })
  }
  socket.onclose = () => {
    if (ws !== socket) return
    if (status.value === 'In Progress') status.value = 'Disconnected'
    else if (status.value === 'Connecting...' || status.value === 'Pending launch') status.value = 'Disconnected'
    resetConnectionState({ closeSocket: false, clearInputFile: false })
  }
}
watch(selectedYamlFile, (newFile) => {
  taskPrompt.value = ''
  fileSearchQuery.value = newFile || ''
  isFileSearchDirty.value = false
  if (!newFile) {
    resetConnectionState()
    status.value = 'Pending file selection'
    handleYAMLSelection(newFile)
    return
  }
  resetConnectionState()
  status.value = 'Connecting...'
  handleYAMLSelection(newFile)
  establishWebSocketConnection()
})
watch(() => route.query?.workflow, () => { applyWorkflowFromRoute() })
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
  loadWorkflows()
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
  unlockBodyScroll()
  resetConnectionState()
  stopTimer()
})
const switchToDashboard = async () => {
  viewMode.value = 'dashboard'
  await nextTick()
}
const launchBatchWorkflow = async () => {
  if (!selectedYamlFile.value) { alert('Please choose a workflow file!'); return }
  if (!selectedInputFile.value) { alert('Please select an input file (.xlsx or .csv)'); return }
  if (!ws || !isConnectionReady.value || !sessionId) { alert('WebSocket connection is not ready yet.'); return }
  shouldGlow.value = false
  status.value = 'Launching...'
  try {
    const result = await postBatchWorkflow({ file: selectedInputFile.value, sessionId: sessionId, yamlFile: selectedYamlFile.value, maxParallel: maxParallel.value, logLevel: logLevel.value })
    if (result.success) {
      status.value = 'In Progress'
      isWorkflowRunning.value = true
    } else {
      status.value = 'Failed'
      alert(`Failed to launch batch workflow: ${result.detail || result.message || 'Unknown error'}`)
      shouldGlow.value = true
      if (isConnectionReady.value) status.value = 'Pending launch'
    }
  } catch (error) {
    status.value = 'Error'
    alert(`Failed to call batch workflow API: ${error.message}`)
    shouldGlow.value = true
    if (isConnectionReady.value) status.value = 'Pending launch'
  }
}
watch(status, (newStatus) => {
  if (newStatus === 'Batch completed' || newStatus === 'Batch cancelled') shouldGlow.value = true
})
const processBatchMessage = async (msg) => {
  if (msg.type === 'batch_completed') {
    const message = `Batch processing finished, ${msg.data.succeeded} tasks succeeded, ${msg.data.failed} tasks failed`
    addLogMessage(message, LOG_TYPES.DEFAULT)
    successfulTasks.value = msg.data.succeeded
    failedTasks.value = msg.data.failed
    completedRowsCount.value = msg.data.succeeded + msg.data.failed
    batchEndTime.value = Date.now()
    stopTimer()
    status.value = 'Batch completed'
    isWorkflowRunning.value = false
    sessionIdToDownload = sessionId
  }
  if (msg.type === 'batch_started') {
    const message = `Batch processing started with total of ${msg.data.total} rows...`
    addLogMessage(message, LOG_TYPES.DEFAULT)
    totalRowsCount.value = msg.data.total
    completedRowsCount.value = 0
    successfulTasks.value = 0
    failedTasks.value = 0
    batchStartTime.value = Date.now()
    batchEndTime.value = null
    startTimer()
  }
  if (msg.type === 'batch_task_started') addLogMessage(`[ID ${msg.data.task_id}, Row ${msg.data.row_index}] launched`, LOG_TYPES.DEFAULT)
  if (msg.type === 'batch_task_completed') {
    addLogMessage(`[ID ${msg.data.task_id}, Row ${msg.data.row_index}] completed, ${msg.data.duration_ms}ms spent, total ${msg.data.token_usage.total_usage.total_tokens} tokens used`, LOG_TYPES.COMPLETED)
    completedRowsCount.value++
    successfulTasks.value++
  }
  if (msg.type === 'batch_task_failed') {
    addLogMessage(`[ID ${msg.data.task_id}, Row ${msg.data.row_index}] failed, Error: ${msg.data.error}`, LOG_TYPES.FAILED)
    completedRowsCount.value++
    failedTasks.value++
  }
}
const cancelBatchWorkflow = () => {
  if (!isWorkflowRunning.value || !ws) return
  addLogMessage('Batch cancelled', LOG_TYPES.DEFAULT)
  batchEndTime.value = Date.now()
  stopTimer()
  status.value = 'Batch cancelled'
  isWorkflowRunning.value = false
  sessionIdToDownload = sessionId
  try { ws.close() } catch (closeError) { console.warn('Failed to close WebSocket:', closeError) }
}
const downloadLogs = async () => {
  if (!sessionIdToDownload) return
  try { await fetchLogsZip(sessionIdToDownload) } catch (error) { alert('Download failed, please try again later') }
}
watch(() => logMessages.value.length, async () => {
  await nextTick()
  if (logMessagesRef.value) logMessagesRef.value.scrollTop = logMessagesRef.value.scrollHeight
})
</script>

<style scoped>
.launch-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #fff9fc 0%, #fff1f6 50%, #ffe8f1 100%);
  color: #5b3446;
  font-family: 'Inter', sans-serif;
  position: relative;
  overflow: hidden;
}

.sakura-panel {
  background: rgba(255, 250, 252, 0.76);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(223, 156, 185, 0.18);
  box-shadow: 0 18px 44px rgba(212, 142, 175, 0.12);
}

.launch-bg {
  position: fixed;
  top: -150px;
  left: 0;
  right: 0;
  height: 500px;
  background: linear-gradient(90deg, #ffd6e6, #f2d6ff, #ffc5df);
  filter: blur(120px);
  opacity: 0.28;
  z-index: 0;
  pointer-events: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 20px 20px 0;
  padding: 16px 20px;
  border-radius: 20px;
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}

.eyebrow {
  color: #b25c82;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 8px;
}

.header h1 {
  margin: 0;
  color: #5b3041;
  font-size: 20px;
  font-weight: 700;
}

.content {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 20px;
  gap: 20px;
  position: relative;
  z-index: 1;
}

.left-panel { flex: 3; display: flex; flex-direction: column; gap: 20px; min-width: 0; }
.right-panel { flex: 1; display: flex; flex-direction: column; gap: 20px; min-width: 250px; }

.log-box, .dashboard-box, .control-section {
  border-radius: 18px;
  overflow: hidden;
}

.log-box, .dashboard-box { flex: 1; display: flex; flex-direction: column; }

.dashboard-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  color: #6a4654;
  display: flex;
  flex-direction: column;
  gap: 20px;
  font-size: 14px;
  line-height: 1.4;
  justify-content: space-between;
}

.metrics-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 8px; }
.metric-card {
  background: rgba(255, 245, 249, 0.78);
  border: 1px solid rgba(223, 156, 185, 0.16);
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.metric-card.status-active {
  border-color: rgba(212, 126, 165, 0.45);
  box-shadow: 0 0 15px rgba(226, 150, 182, 0.14);
}
.metric-title {
  font-size: 12px;
  color: #a07b8a;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 700;
}
.metric-value { font-size: 16px; font-weight: 700; color: #5f3b4b; }
.progress-section { margin-top: 8px; }
.progress-label {
  font-size: 12px;
  color: #a07b8a;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 700;
  margin-bottom: 8px;
}
.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(223, 156, 185, 0.12);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 8px;
  position: relative;
}
.progress-fill {
  position: relative;
  height: 100%;
  background: linear-gradient(90deg, #ffd6e6, #f0d7ff, #ffc4de);
  background-size: 200% 100%;
  animation: gradientShift 3s ease-in-out infinite;
  transition: width 0.3s ease;
  overflow: hidden;
}
.progress-fill.processing::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, rgba(255,255,255,0.85) 60%, rgba(255,255,255,0.4) 70%, transparent 100%);
  animation: wavePulse 1.8s ease-in-out infinite;
}
.progress-text { font-size: 13px; color: #8b6877; text-align: center; font-weight: 600; }
.log-messages::-webkit-scrollbar { width: 8px; height: 8px; }
.log-messages::-webkit-scrollbar-track { background: transparent; }
.log-messages::-webkit-scrollbar-thumb { background-color: rgba(210, 151, 177, 0.3); border-radius: 8px; border: 2px solid transparent; background-clip: padding-box; }
.log-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  color: #6a4654;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 14px;
  line-height: 1.4;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}
.log-message { white-space: pre-wrap; word-break: break-word; }
.log-timestamp { font-weight: 600; }
.log-timestamp-completed { color: #b45d82; }
.log-timestamp-failed { color: #d05b82; }
.log-timestamp-default { color: #9c6f80; }
.log-placeholder { color: #9f7a89; font-style: italic; text-align: center; margin-top: 20px; }
.control-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
}
.section-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #a07b8a;
  font-weight: 700;
  margin-top: 4px;
}
.select-wrapper { position: relative; }
.file-selector-input {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  padding-right: 30px;
  background: rgba(255, 248, 251, 0.9);
  border: 1px solid rgba(223, 156, 185, 0.18);
  border-radius: 12px;
  color: #5f3b4b;
  font-size: 14px;
}
.file-selector-input:hover:not(:disabled), .file-selector-input:focus {
  background: rgba(255, 250, 252, 0.98);
  border-color: rgba(223, 156, 185, 0.34);
}
.file-selector-input:disabled { opacity: 0.5; cursor: not-allowed; }
.select-arrow {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #b08a99;
  pointer-events: none;
  font-size: 10px;
}
.file-dropdown {
  position: absolute;
  top: calc(100%);
  left: 0;
  right: 0;
  margin-top: 1px;
  background: rgba(255, 250, 252, 0.98);
  border: 1px solid rgba(223, 156, 185, 0.18);
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(212, 142, 175, 0.16);
  max-height: 260px;
  overflow-y: auto;
  z-index: 5;
  padding: 6px 0;
}
.file-dropdown::-webkit-scrollbar { display: none; }
.file-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 14px;
  cursor: pointer;
  transition: background 0.15s ease;
}
.file-option:hover { background: rgba(255, 241, 246, 0.82); }
.file-name { color: #5f3b4b; font-size: 12px; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-desc { color: #9b7485; font-size: 11px; }
.file-empty { padding: 12px 14px; color: #9b7485; font-size: 13px; text-align: center; }
.file-dropdown-enter-active, .file-dropdown-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.file-dropdown-enter-from, .file-dropdown-leave-to { opacity: 0; transform: translateY(-4px); }
.file-upload-button {
  width: 100%;
  padding: 10px 12px;
  background: rgba(255, 248, 251, 0.9);
  border: 1px solid rgba(223, 156, 185, 0.18);
  border-radius: 12px;
  color: #8d6174;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-upload-button:hover:not(:disabled) { background: rgba(255, 250, 252, 0.98); border-color: rgba(223, 156, 185, 0.34); }
.file-upload-button:disabled { opacity: 0.5; cursor: not-allowed; }
.hidden-file-input { display: none; }
.manual-title {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #a07b8a;
  font-weight: 700;
  margin-bottom: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.manual-title:hover { color: #b05c81; }
.info-icon { opacity: 0.65; }
.view-toggle {
  display: flex;
  background: rgba(255, 245, 249, 0.84);
  padding: 4px;
  border-radius: 12px;
}
.toggle-button {
  flex: 1;
  padding: 8px;
  border: none;
  background: transparent;
  color: #9f7a89;
  cursor: pointer;
  border-radius: 10px;
  font-size: 13px;
  transition: all 0.2s ease;
}
.toggle-button.active { background: rgba(255, 255, 255, 0.85); color: #5f3b4b; font-weight: 700; }
.button-section { display: flex; flex-direction: column; gap: 12px; }
.cancel-button, .launch-button, .download-button, .confirm-button {
  padding: 12px 14px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 700;
  transition: all 0.3s ease;
}
.cancel-button {
  border: none;
  cursor: pointer;
  color: #7f2f4d;
  background: linear-gradient(135deg, #ffc7da, #f5b9d0, #eba8c3);
}
.cancel-button:hover:not(:disabled), .launch-button:hover:not(:disabled), .download-button:hover:not(:disabled), .confirm-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(226, 150, 182, 0.16);
}
.cancel-button:disabled, .launch-button:disabled, .download-button:disabled { opacity: 0.5; cursor: not-allowed; }
.launch-button, .confirm-button {
  border: none;
  color: #6b3046;
  background: linear-gradient(135deg, #ffd6e6, #f2d6ff, #ffc5df);
  background-size: 200% 100%;
  animation: gradientShift 6s ease-in-out infinite;
}
.launch-button.glow { animation: glowPulse 3s ease-in-out infinite, gradientShift 6s ease-in-out infinite; }
.download-button {
  background: rgba(255, 250, 252, 0.8);
  border: 1px solid rgba(223, 156, 185, 0.18);
  color: #8f5e77;
  cursor: pointer;
}
.image-modal {
  position: fixed;
  inset: 0;
  background: rgba(255, 240, 246, 0.42);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(3px);
}
.image-modal-content {
  position: relative;
  max-width: 95vw;
  max-height: 95vh;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  padding: 20px;
  border-radius: 18px;
}
.image-modal-content img { max-width: 70vw; max-height: 65vh; box-shadow: 0 20px 40px rgba(212, 142, 175, 0.18); }
.image-modal-enter-active, .image-modal-leave-active { transition: opacity 0.2s ease; }
.image-modal-enter-from, .image-modal-leave-to { opacity: 0; }
.settings-button {
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(223, 156, 185, 0.22);
  color: #a35b79;
  cursor: pointer;
  padding: 8px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}
.settings-button:hover { background-color: rgba(255, 245, 249, 0.95); }
.column-guide-modal-overlay, .batch-settings-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 240, 246, 0.38);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}
.column-guide-modal, .batch-settings-modal {
  max-width: 550px;
  width: 90vw;
  max-height: 80vh;
  overflow: hidden;
  border-radius: 20px;
}
.batch-settings-modal { max-width: 500px; }
.modal-content { padding: 24px; max-height: calc(80vh - 48px); overflow-y: auto; }
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; transform: scale(0.95); }
.batch-settings-modal .modal-content { padding: 0; }
.batch-settings-modal .modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(223, 156, 185, 0.14);
}
.batch-settings-modal .modal-header h3 { margin: 0; font-size: 20px; font-weight: 700; color: #5b3041; }
.batch-settings-modal .close-button {
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(223,156,185,0.18);
  color: #a35b79;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  width: 34px;
  height: 34px;
  border-radius: 12px;
}
.batch-settings-modal .modal-body { padding: 24px; flex: 1; overflow-y: auto; }
.batch-settings-modal .settings-item { margin-bottom: 24px; }
.batch-settings-modal .setting-label {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #6a4654;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.batch-settings-modal .setting-input, .batch-settings-modal .setting-select {
  padding: 10px 12px;
  background: rgba(255, 248, 251, 0.9);
  border: 1px solid rgba(223, 156, 185, 0.18);
  border-radius: 12px;
  color: #5f3b4b;
  font-size: 14px;
}
.batch-settings-modal .setting-input { width: 86px; }
.batch-settings-modal .setting-desc { margin-top: 6px; color: #8d6e7c; font-size: 12px; line-height: 1.4; }
.batch-settings-modal .modal-footer {
  padding: 16px 24px;
  border-top: 1px solid rgba(223, 156, 185, 0.14);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
.batch-settings-modal .cancel-button {
  background: rgba(255, 255, 255, 0.72);
  color: #8d6174;
  border: 1px solid rgba(223, 156, 185, 0.18);
}
.manual-content {
  background: rgba(255, 245, 249, 0.74);
  border: 1px solid rgba(223, 156, 185, 0.16);
  border-radius: 14px;
  padding: 12px;
  font-size: 13px;
  line-height: 1.4;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.manual-item { margin-bottom: 8px; color: #6a4654; }
.manual-item:last-child { margin-bottom: 0; }
.manual-item code {
  background: rgba(255, 255, 255, 0.78);
  padding: 2px 6px;
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: #b05c81;
  font-weight: 600;
}
.manual-example { margin-top: 6px; margin-left: 16px; }
.manual-example pre {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(223, 156, 185, 0.14);
  border-radius: 10px;
  padding: 8px;
  font-size: 11px;
  color: #6a4654;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  overflow-x: auto;
  margin: 4px 0 0 0;
}
@keyframes gradientShift { 0%, 100% { background-position: 0% 0%; } 50% { background-position: 100% 0%; } }
@keyframes glowPulse { 0% { box-shadow: 0 0 0 0 rgba(231, 143, 179, 0.25); } 50% { box-shadow: 0 0 0 5px rgba(231, 143, 179, 0); } 100% { box-shadow: 0 0 0 0 rgba(231, 143, 179, 0); } }
@keyframes wavePulse { 0% { left: -100%; opacity: 0; } 50% { opacity: 1; } 100% { left: 100%; opacity: 0; } }
</style>
