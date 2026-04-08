<template>
  <div class="launch-view">
    <div class="launch-bg"></div>
    <div class="header sakura-panel">
      <div class="header-copy">
        <div class="eyebrow">🌸 Mission Launch</div>
        <h1>MyLittleAgent Launch Console</h1>
      </div>
      <button class="settings-button" @click="showSettingsModal = true" title="Settings">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
      </button>
    </div>
    <div class="content">
      <div class="left-panel">
        <div
          class="chat-panel sakura-panel"
          :class="{
            'chat-panel-fullscreen': viewMode === 'chat',
            'chat-panel-collapsed': viewMode !== 'chat' && !isChatPanelOpen
          }"
          v-show="viewMode === 'chat' || true"
        >
          <button v-show="viewMode !== 'chat'" class="chat-panel-toggle" @click="isChatPanelOpen = !isChatPanelOpen" :title="isChatPanelOpen ? 'Collapse chat' : 'Expand chat'">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="{ 'chevron-collapsed': !isChatPanelOpen }">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>
          <div v-show="viewMode === 'chat' || isChatPanelOpen" class="chat-panel-content">
            <div class="chat-box">
              <div class="chat-messages" ref="chatMessagesRef">
                <div v-for="(message, index) in chatMessages" :key="`message-${index}`">
                  <div
                    v-if="['notification', 'warning', 'error'].includes(message.type)"
                    class="chat-notification"
                    :class="{
                      'chat-notification-warning': message.type === 'warning',
                      'chat-notification-error': message.type === 'error'
                    }"
                  >
                    <div class="notification-content">
                      <div class="notification-text">{{ message.message }}</div>
                      <div class="message-timestamp">{{ formatTime(message.timestamp) }}</div>
                    </div>
                  </div>

                  <div
                    v-else-if="message.type === 'dialogue'"
                    class="dialogue"
                    :class="{ 'dialogue-right': message.isRight }"
                  >
                    <div class="profile-picture">
                      <img :src="message.avatar" :alt="`Avatar ${index + 1}`" />
                    </div>
                    <div class="message-content">
                      <div class="user-name">
                        {{ message.name }}
                        <span class="message-timestamp">{{ formatTime(message.timestamp) }}</span>
                      </div>
                      <div class="message-bubble" :class="{ 'loading-bubble': message.isLoading }">
                        <CollapsibleMessage
                          v-if="message.text"
                          :html-content="message.htmlContent || renderMarkdown(message.text)"
                          :raw-content="message.text"
                          :default-expanded="configStore.AUTO_EXPAND_MESSAGES"
                        />
                        <TransitionGroup
                          v-if="message.loadingEntries && message.loadingEntries.length"
                          name="loading-entry"
                          tag="div"
                          class="loading-entries"
                        >
                          <div
                            v-for="entry in message.loadingEntries"
                            :key="entry.key"
                            class="loading-entry"
                            :class="{
                              'entry-running': entry.status === 'running',
                              'entry-done': entry.status === 'done'
                            }"
                          >
                            <span class="loading-entry-label">{{ entry.label }}</span>
                            <span class="loading-entry-duration">
                              {{ formatDuration(entry.startedAt, entry.endedAt || null) }}
                            </span>
                          </div>
                        </TransitionGroup>

                        <div v-if="message.isArtifact && message.isImage" class="artifact-image-wrapper">
                          <div v-if="message.loading" class="artifact-status">Loading image...</div>
                          <div v-else-if="message.error" class="artifact-status artifact-error">{{ message.error }}</div>
                          <div v-else>
                            <img
                              :src="message.dataUri"
                              :alt="message.fileName || 'image artifact'"
                              class="artifact-image"
                              role="button"
                              tabindex="0"
                              @click="openImageModal(message)"
                              @keydown.enter.prevent="openImageModal(message)"
                              @keydown.space.prevent="openImageModal(message)"
                            />
                            <div class="artifact-filename">
                              <img
                                v-if="getFilePreviewSrc(message)"
                                :src="getFilePreviewSrc(message)"
                                :alt="`${message.fileName} preview`"
                                class="artifact-filename-icon"
                              />
                              <span class="artifact-filename-text">{{ message.fileName }}</span>
                            </div>
                            <button class="artifact-download-button" type="button" :disabled="message.loading" @click="downloadArtifact(message)">
                              Download
                            </button>
                          </div>
                        </div>

                        <div v-else-if="message.isArtifact && !message.isImage" class="artifact-file-wrapper">
                          <div class="artifact-filename">
                            <img
                              v-if="getFilePreviewSrc(message)"
                              :src="getFilePreviewSrc(message)"
                              :alt="`${message.fileName} preview`"
                              class="artifact-filename-icon"
                            />
                            <span class="artifact-filename-text">{{ message.fileName }}</span>
                          </div>
                          <button class="artifact-download-button" type="button" :disabled="message.loading" @click="downloadArtifact(message)">
                            {{ message.loading ? 'Preparing...' : 'Download' }}
                          </button>
                        </div>

                        <div v-if="message.isLoading || message.duration" class="loading-timer">
                          {{ message.isLoading ? formatDuration(message.startedAt) : message.duration }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="input-area">
              <div
                :class="['input-shell', { glow: shouldGlow, 'drag-active': isDragActive }]"
                @dragenter="handleDragEnter"
                @dragover="handleDragOver"
                @dragleave="handleDragLeave"
                @drop="handleDrop"
              >
                <textarea
                  v-model="taskPrompt"
                  class="task-input"
                  :disabled="!isConnectionReady || (isWorkflowRunning && status !== 'Waiting for input...')"
                  placeholder="Describe the mission gently..."
                  ref="taskInputRef"
                  @keydown.enter="handleEnterKey"
                  @paste="handlePaste"
                ></textarea>
                <div class="input-footer">
                  <div class="input-footer-buttons">
                    <div class="attachment-upload" @mouseenter="handleAttachmentHover(true)" @mouseleave="handleAttachmentHover(false)">
                      <div class="attachment-button-wrapper">
                        <button
                          type="button"
                          class="attachment-button"
                          :disabled="!isConnectionReady || !sessionId || isUploadingAttachment || (isWorkflowRunning && status !== 'Waiting for input...')"
                          @click="handleAttachmentButtonClick"
                        >
                          {{ isUploadingAttachment ? 'Uploading...' : 'Upload File' }}
                        </button>
                        <span v-if="uploadedAttachments.length" class="attachment-count">{{ uploadedAttachments.length }}</span>
                      </div>
                      <input ref="attachmentInputRef" type="file" class="hidden-file-input" @change="onAttachmentSelected" />
                      <Transition name="attachment-popover">
                        <div v-if="showAttachmentPopover" class="attachment-modal" @mouseenter="handleAttachmentHover(true)" @mouseleave="handleAttachmentHover(false)">
                          <div v-for="attachment in uploadedAttachments" :key="attachment.attachmentId" class="attachment-item">
                            <span class="attachment-name">{{ attachment.name }}</span>
                            <button type="button" class="remove-attachment" @click.stop="removeAttachment(attachment.attachmentId)">×</button>
                          </div>
                          <div v-if="!uploadedAttachments.length" class="attachment-empty">No files uploaded</div>
                        </div>
                      </Transition>
                    </div>
                  </div>
                </div>
                <div v-if="isDragActive" class="drag-overlay">
                  <div class="drag-overlay-content">Drop files to upload</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-show="viewMode === 'graph'" class="graph-panel sakura-panel">
          <VueFlow class="vueflow-graph">
            <template #node-workflow-node="props">
              <WorkflowNode
                :id="props.id"
                :data="props.data"
                :is-active="activeNodes.includes(props.id)"
                :sprite="nodeSpriteMap.get(props.id) || ''"
                @hover="onNodeHover"
                @leave="onNodeLeave"
              />
            </template>
            <template #node-start-node="props">
              <StartNode :id="props.id" :data="props.data" />
            </template>
            <template #edge-workflow-edge="props">
              <WorkflowEdge
                :id="props.id"
                :source="props.source"
                :target="props.target"
                :source-x="props.sourceX"
                :source-y="props.sourceY"
                :target-x="props.targetX"
                :target-y="props.targetY"
                :source-position="props.sourcePosition"
                :target-position="props.targetPosition"
                :data="props.data"
                :marker-end="props.markerEnd"
                :animated="props.animated"
                :hovered-node-id="hoveredNodeId"
              />
            </template>
            <Background pattern-color="#e9b3ca"/>
            <Controls position="bottom-left"/>
          </VueFlow>
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

          <label class="section-label">Status</label>
          <div class="status-display" :class="{ 'status-active': status === 'Running...' }">{{ status }}</div>

          <label class="section-label">View</label>
          <div class="view-toggle">
            <button class="toggle-button" :class="{ active: viewMode === 'chat' }" @click="viewMode = 'chat'">Chat</button>
            <button class="toggle-button" :class="{ active: viewMode === 'graph' }" @click="switchToGraph">Graph</button>
          </div>

          <div class="button-section">
            <button
              class="launch-button"
              :class="{ glow: shouldGlow, 'is-sending': isWorkflowRunning }"
              @click="handleButtonClick"
              :disabled="loading || (isWorkflowRunning && !taskPrompt.trim()) || (!isWorkflowRunning && status !== 'Completed' && status !== 'Cancelled' && !isConnectionReady)">
              {{ buttonLabel }}
            </button>

            <button class="cancel-button" :disabled="status !== 'Running...'" @click="cancelWorkflow">Cancel</button>
            <button class="download-button" :disabled="status !== 'Completed' && status !== 'Cancelled'" @click="downloadLogs">Download Logs</button>
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
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { fetchWorkflowsWithDesc, fetchLogsZip, fetchWorkflowYAML, postFile, getAttachment, fetchVueGraph } from '../utils/apiFunctions.js'
import { configStore } from '../utils/configStore.js'
import { spriteFetcher } from '../utils/spriteFetcher.js'
import yaml from 'js-yaml'
import MarkdownIt from 'markdown-it'
import SettingsModal from '../components/SettingsModal.vue'
const md = new MarkdownIt({ html: false, linkify: true, typographer: true })
const renderMarkdown = (text) => md.render(text || '')
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-GB', { hour12: false })
}
import { VueFlow, useVueFlow, MarkerType } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/controls/dist/style.css'
import '../utils/vueflow.css'
import WorkflowNode from '../components/WorkflowNode.vue'
import WorkflowEdge from '../components/WorkflowEdge.vue'
import StartNode from '../components/StartNode.vue'
import CollapsibleMessage from '../components/CollapsibleMessage.vue'

const router = useRouter()
const route = useRoute()
const taskPrompt = ref('')
const workflowFiles = ref([])
const selectedFile = ref('')
const fileSearchQuery = ref('')
const isFileSearchDirty = ref(false)
const isFileDropdownOpen = ref(false)
const fileSelectorWrapperRef = ref(null)
const fileSelectorInputRef = ref(null)
const status = ref('Waiting for workflow selection...')
const loading = ref(false)
let sessionIdToDownload = null
const chatMessages = ref([])
const chatMessagesRef = ref(null)
const nodesLoadingMessagesMap = new Map()
const addTotalLoadingMessage = (nodeId) => {
  if (!nodeId) return null
  let nodeState = nodesLoadingMessagesMap.get(nodeId)
  if (nodeState) return nodeState
  let avatar
  if (nameToSpriteMap.value.has(nodeId)) {
    avatar = nameToSpriteMap.value.get(nodeId)
  } else {
    avatar = spriteFetcher.fetchSprite(nodeId, 'D', 1)
    nameToSpriteMap.value.set(nodeId, avatar)
  }
  const message = { type: 'dialogue', name: nodeId, text: '', htmlContent: '', avatar, isRight: false, isLoading: true, startedAt: Date.now(), timestamp: Date.now(), loadingEntries: [] }
  chatMessages.value.push(message)
  nodeState = { message, entryMap: new Map(), baseKeyToKey: new Map(), counters: new Map() }
  nodesLoadingMessagesMap.set(nodeId, nodeState)
  return nodeState
}
const addLoadingEntry = (nodeId, baseKey, label) => {
  const nodeState = addTotalLoadingMessage(nodeId)
  if (!nodeState || !baseKey) return null
  const count = (nodeState.counters.get(baseKey) || 0) + 1
  nodeState.counters.set(baseKey, count)
  const key = `${baseKey}-${count}`
  const entry = { key, baseKey, label, status: 'running', startedAt: Date.now(), endedAt: null }
  nodeState.entryMap.set(key, entry)
  nodeState.baseKeyToKey.set(baseKey, key)
  nodeState.message.loadingEntries.push(entry)
  runningLoadingEntries.value += 1
  if (runningLoadingEntries.value === 1) startLoadingTimer()
  return entry
}
const finishLoadingEntry = (nodeId, baseKey) => {
  const nodeState = nodesLoadingMessagesMap.get(nodeId)
  if (!nodeState || !baseKey) return null
  const key = nodeState.baseKeyToKey.get(baseKey)
  const entry = key ? nodeState.entryMap.get(key) : null
  if (!entry) return null
  const wasRunning = entry.status === 'running'
  entry.status = 'done'
  entry.endedAt = Date.now()
  nodeState.baseKeyToKey.delete(baseKey)
  if (wasRunning) {
    runningLoadingEntries.value = Math.max(0, runningLoadingEntries.value - 1)
    if (runningLoadingEntries.value === 0) stopLoadingTimer()
  }
  return entry
}
const finalizeAllLoadingEntries = (nodeState, endedAt = Date.now()) => {
  if (!nodeState) return
  let finishedCount = 0
  for (const entry of nodeState.entryMap.values()) {
    if (entry.status === 'running') {
      entry.status = 'done'
      entry.endedAt = endedAt
      finishedCount += 1
    }
  }
  nodeState.baseKeyToKey.clear()
  if (finishedCount) {
    runningLoadingEntries.value = Math.max(0, runningLoadingEntries.value - finishedCount)
    if (runningLoadingEntries.value === 0) stopLoadingTimer()
  }
}
const now = ref(Date.now())
let loadingTimerInterval = null
const runningLoadingEntries = ref(0)
const startLoadingTimer = () => {
  if (loadingTimerInterval) return
  loadingTimerInterval = setInterval(() => { now.value = Date.now() }, 1000)
}
const stopLoadingTimer = () => {
  if (!loadingTimerInterval) return
  clearInterval(loadingTimerInterval)
  loadingTimerInterval = null
}
const nameToSpriteMap = ref(new Map())
const nodeSpriteMap = ref(new Map())
const shouldGlow = ref(false)
const taskInputRef = ref(null)
const attachmentInputRef = ref(null)
const uploadedAttachments = ref([])
const isDragActive = ref(false)
const showAttachmentPopover = ref(false)
const isUploadingAttachment = ref(false)
let attachmentHoverTimeout = null
const selectedArtifactImage = ref(null)
let dragDepth = 0
const isRecording = ref(false)
let mediaRecorder = null
let audioChunks = []
let audioStream = null
const isConnectionReady = ref(false)
const showSettingsModal = ref(false)
const viewMode = ref('chat')
const isChatPanelOpen = ref(true)
let ws = null
let sessionId = null
const filteredWorkflowFiles = computed(() => {
  if (!isFileSearchDirty.value) return workflowFiles.value
  const query = fileSearchQuery.value.trim().toLowerCase()
  if (!query) return workflowFiles.value
  return workflowFiles.value.filter((workflow) => workflow.name?.toLowerCase().includes(query))
})
const buttonLabel = computed(() => {
  if (isWorkflowRunning.value) return 'Send'
  if (status.value === 'Completed' || status.value === 'Cancelled') return 'Relaunch'
  return 'Launch'
})
const clearUploadedAttachments = () => {
  uploadedAttachments.value = []
  showAttachmentPopover.value = false
  if (attachmentInputRef.value) attachmentInputRef.value.value = ''
}
const resetConnectionState = ({ closeSocket = true } = {}) => {
  if (closeSocket && ws) {
    try { ws.close() } catch (closeError) { console.warn('Failed to close WebSocket:', closeError) }
  }
  ws = null
  sessionId = null
  isConnectionReady.value = false
  shouldGlow.value = false
  isWorkflowRunning.value = false
  activeNodes.value = []
  if (attachmentHoverTimeout) {
    clearTimeout(attachmentHoverTimeout)
    attachmentHoverTimeout = null
  }
  clearUploadedAttachments()
}
const isWorkflowRunning = ref(false)
const activeNodes = ref([])
const hoveredNodeId = ref(null)
const onNodeHover = (nodeId) => { hoveredNodeId.value = nodeId || null }
const onNodeLeave = () => { hoveredNodeId.value = null }
const workflowYaml = ref({})
const applyWorkflowFromRoute = () => {
  let workflowParam = route.query?.workflow || route.query?.file || route.query?.name
  if (Array.isArray(workflowParam)) workflowParam = workflowParam[0]
  if (!workflowParam || typeof workflowParam !== 'string') return
  let fileName = workflowParam.trim()
  if (!fileName) return
  if (!fileName.toLowerCase().endsWith('.yaml')) fileName = `${fileName}.yaml`
  selectedFile.value = fileName
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
  selectedFile.value = fileName
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
  fileSearchQuery.value = selectedFile.value || ''
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
const addDialogue = (name, message) => {
  if (message === null || message === undefined) return
  const text = typeof message === 'string' ? message : String(message)
  if (!text.trim()) return
  let avatar
  if (nameToSpriteMap.value.has(name)) {
    avatar = nameToSpriteMap.value.get(name)
  } else {
    avatar = spriteFetcher.fetchSprite()
    nameToSpriteMap.value.set(name, avatar)
  }
  const isRight = name === 'User'
  const htmlContent = renderMarkdown(text)
  chatMessages.value.push({ type: 'dialogue', name, text, htmlContent, avatar, isRight, timestamp: Date.now() })
}
const addChatNotification = (message, { type = 'notification' } = {}) => {
  chatMessages.value.push({ type, message, timestamp: Date.now() })
}
const formatDuration = (startedAt, endedAt = null) => {
  if (!startedAt) return ''
  const end = endedAt ?? now.value
  const totalSeconds = Math.max(0, Math.floor((end - startedAt) / 1000))
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0')
  const seconds = String(totalSeconds % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
}
const isAttachmentUploadAllowed = () => {
  if (!isConnectionReady.value || !sessionId || isUploadingAttachment.value) return false
  if (isWorkflowRunning.value && status.value !== 'Waiting for input...') return false
  return true
}
const handleAttachmentButtonClick = () => {
  if (!isAttachmentUploadAllowed()) return
  attachmentInputRef.value?.click()
}
const uploadFiles = async (files) => {
  if (!files || files.length === 0) return
  if (!sessionId) { alert('Session is not ready yet. Please wait for connection.'); return }
  isUploadingAttachment.value = true
  try {
    for (const file of files) {
      try {
        const result = await postFile(sessionId, file)
        if (result?.success && result?.attachmentId) {
          uploadedAttachments.value.push(result)
        } else {
          alert(result?.message || 'Failed to upload file')
        }
      } catch (error) {
        console.error('Failed to upload attachment:', error)
        alert('File upload failed, please try again.')
      }
    }
  } finally {
    isUploadingAttachment.value = false
  }
}
const onAttachmentSelected = async (event) => {
  const file = event.target?.files?.[0]
  if (event.target) event.target.value = ''
  if (!file) return
  await uploadFiles([file])
}
const removeAttachment = (attachmentId) => {
  uploadedAttachments.value = uploadedAttachments.value.filter((attachment) => attachment.attachmentId !== attachmentId)
}
const handleAttachmentHover = (isHovering) => {
  if (isHovering) {
    if (attachmentHoverTimeout) { clearTimeout(attachmentHoverTimeout); attachmentHoverTimeout = null }
    if (uploadedAttachments.value.length > 0) showAttachmentPopover.value = true
    return
  }
  if (attachmentHoverTimeout) clearTimeout(attachmentHoverTimeout)
  attachmentHoverTimeout = setTimeout(() => { showAttachmentPopover.value = false; attachmentHoverTimeout = null }, 140)
}
const lockBodyScroll = () => {
  if (typeof document !== 'undefined') document.body.style.overflow = 'hidden'
}
const unlockBodyScroll = () => {
  if (typeof document !== 'undefined') document.body.style.overflow = ''
}
const openImageModal = (message) => {
  if (!message || message.loading || !message.dataUri) return
  selectedArtifactImage.value = { src: message.dataUri, name: message.fileName || 'Artifact image' }
  lockBodyScroll()
}
const closeImageModal = () => {
  if (!selectedArtifactImage.value) return
  selectedArtifactImage.value = null
  unlockBodyScroll()
}
const handleKeydown = (event) => {
  if (event.key === 'Escape' && selectedArtifactImage.value) closeImageModal()
}
const handleEnterKey = (e) => {
  if (e.metaKey || e.ctrlKey) {
    if (loading.value || (isWorkflowRunning.value && !taskPrompt.value.trim()) || (!isWorkflowRunning.value && status.value !== 'Completed' && status.value !== 'Cancelled' && !isConnectionReady.value)) return
    handleButtonClick()
  }
}
const handlePaste = async (event) => {
  if (!isAttachmentUploadAllowed()) return
  const clipboardData = event.clipboardData
  if (!clipboardData) return
  const files = clipboardData.files
  if (!files || files.length === 0) return
  event.preventDefault()
  await uploadFiles(files)
}
const isFileDragEvent = (event) => {
  const types = event?.dataTransfer?.types
  if (!types) return false
  return Array.from(types).includes('Files')
}
const handleDragEnter = (event) => {
  if (!isFileDragEvent(event) || !isAttachmentUploadAllowed()) return
  dragDepth += 1
  isDragActive.value = true
  event.preventDefault()
}
const handleDragOver = (event) => {
  if (!isFileDragEvent(event) || !isAttachmentUploadAllowed()) return
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy'
}
const handleDragLeave = (event) => {
  if (!isFileDragEvent(event)) return
  dragDepth = Math.max(0, dragDepth - 1)
  if (dragDepth === 0) isDragActive.value = false
}
const handleDrop = async (event) => {
  if (!isFileDragEvent(event)) return
  event.preventDefault()
  dragDepth = 0
  isDragActive.value = false
  if (!isAttachmentUploadAllowed()) return
  const files = Array.from(event.dataTransfer?.files || [])
  if (files.length === 0) return
  await uploadFiles(files)
}
const handleYAMLSelection = async (fileName) => {
  if (!fileName) {
    workflowYaml.value = {}
    chatMessages.value = []
    setNodes([])
    setEdges([])
    nodeSpriteMap.value.clear()
    return
  }
  chatMessages.value = []
  try {
    const yamlContentString = await fetchWorkflowYAML(fileName)
    const parsedYaml = yaml.load(yamlContentString)
    workflowYaml.value = parsedYaml || {}
    const initialInstructions = workflowYaml.value?.graph?.initial_instruction || ''
    if (initialInstructions) addChatNotification(initialInstructions)
    else addChatNotification('No initial instructions provided')
    const yamlNodes = Array.isArray(workflowYaml.value?.graph?.nodes) ? workflowYaml.value.graph.nodes : []
    nodeSpriteMap.value.clear()
    for (const node of yamlNodes) {
      if (node.id) {
        const spritePath = spriteFetcher.fetchSprite(node.id, 'D', 1)
        nodeSpriteMap.value.set(node.id, spritePath)
      }
    }
  } catch (error) {
    console.error('Failed to load YAML file:', error)
    workflowYaml.value = {}
    addChatNotification('Failed to load YAML file')
    nodeSpriteMap.value.clear()
  }
  await loadVueFlowGraph({ fit: viewMode.value === 'graph' })
}
const handleButtonClick = () => {
  if (isWorkflowRunning.value) {
    sendHumanInput()
    status.value = 'Running...'
    shouldGlow.value = false
  } else if (status.value === 'Completed' || status.value === 'Cancelled') {
    if (!selectedFile.value) {
      alert('Please choose a workflow file!')
      return
    }
    resetConnectionState()
    status.value = 'Connecting...'
    handleYAMLSelection(selectedFile.value)
    establishWebSocketConnection()
  } else {
    launchWorkflow()
  }
}
const sendHumanInput = () => {
  if (!ws) return
  const trimmedInput = taskPrompt.value.trim()
  const attachmentIds = uploadedAttachments.value.map((attachment) => attachment.attachmentId)
  const attachmentNames = uploadedAttachments.value.map((attachment) => attachment.name || attachment.attachmentId)
  if (!trimmedInput && attachmentIds.length === 0) return
  const message = { type: 'human_input', data: { input: trimmedInput, attachments: attachmentIds } }
  clearUploadedAttachments()
  ws.send(JSON.stringify(message))
  const fullMessage = []
  if (trimmedInput) fullMessage.push(trimmedInput)
  if (attachmentNames.length) fullMessage.push(`[[Attachments]]:\n ${attachmentNames.join(', ')}`)
  if (fullMessage.length) addDialogue('User', fullMessage.join('\n\n'))
  taskPrompt.value = ''
}
const establishWebSocketConnection = () => {
  resetConnectionState()
  if (!selectedFile.value) return
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
  socket.onopen = () => { if (ws !== socket) return; console.log('WebSocket connected') }
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
      status.value = 'Waiting for launch...'
      nextTick(() => { taskInputRef.value?.focus() })
    } else {
      processMessage(msg)
    }
  }
  socket.onerror = (error) => {
    if (ws !== socket) return
    console.error('WebSocket error:', error)
    status.value = 'Connection error'
    alert('WebSocket connection error!')
    resetConnectionState({ closeSocket: false })
  }
  socket.onclose = () => {
    if (ws !== socket) return
    if (status.value === 'Running...') status.value = 'Disconnected'
    else if (status.value === 'Connecting...' || status.value === 'Waiting for launch...') status.value = 'Disconnected'
    resetConnectionState({ closeSocket: false })
  }
}
watch(selectedFile, (newFile) => {
  taskPrompt.value = ''
  fileSearchQuery.value = newFile || ''
  isFileSearchDirty.value = false
  if (!newFile) {
    resetConnectionState()
    status.value = 'Waiting for file selection...'
    handleYAMLSelection(newFile)
    return
  }
  resetConnectionState()
  status.value = 'Connecting...'
  handleYAMLSelection(newFile)
  establishWebSocketConnection()
})
watch(() => uploadedAttachments.value.length, (length) => {
  if (!length) showAttachmentPopover.value = false
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
  stopLoadingTimer()
  runningLoadingEntries.value = 0
})
const { fromObject, fitView, onPaneReady, onNodesInitialized, setNodes, setEdges, edges } = useVueFlow()
onPaneReady(() => { requestAnimationFrame(() => fitView?.({ padding: 0.1 })) })
onNodesInitialized(() => { requestAnimationFrame(() => fitView?.({ padding: 0.1 })) })
const syncNodeAndEdgeData = () => {
  try {
    const yamlNodes = workflowYaml.value?.graph?.nodes || []
    const yamlEdges = workflowYaml.value?.graph?.edges || []
    const yamlNodeById = new Map(Array.isArray(yamlNodes) ? yamlNodes.map(node => [node.id, node]) : [])
    const yamlEdgeByKey = new Map(Array.isArray(yamlEdges) ? yamlEdges.map(edge => [`${edge.from}-${edge.to}`, edge]) : [])
    setNodes(existingNodes => {
      if (!Array.isArray(existingNodes)) return existingNodes
      return existingNodes.map(node => {
        const yamlNode = yamlNodeById.get(node.id)
        if (yamlNode) return { ...node, data: yamlNode }
        return node
      })
    })
    setEdges(existingEdges => {
      if (!Array.isArray(existingEdges)) return existingEdges
      return existingEdges.map(edge => {
        const key = `${edge.source}-${edge.target}`
        const yamlEdge = yamlEdgeByKey.get(key)
        if (yamlEdge) {
          return {
            ...edge,
            data: yamlEdge,
            markerEnd: { type: MarkerType.Arrow, width: 18, height: 18, color: '#d58aaa', strokeWidth: 2 }
          }
        }
        return edge
      })
    })
  } catch (error) {
    console.error('Failed to sync graph data with YAML:', error)
  }
}
const generateNodesAndEdges = async ({ fit = false } = {}) => {
  try {
    const yamlNodes = Array.isArray(workflowYaml.value?.graph?.nodes) ? workflowYaml.value.graph.nodes : []
    const yamlEdges = Array.isArray(workflowYaml.value?.graph?.edges) ? workflowYaml.value.graph.edges : []
    const generatedNodes = yamlNodes.map((node, index) => ({ id: node.id, type: 'workflow-node', label: node.id, position: { x: 20 + (index % 5) * 200, y: 10 + Math.floor(index / 5) * 150 }, data: node }))
    const generatedEdges = yamlEdges.map(edge => ({ id: `${edge.from}-${edge.to}`, source: edge.from, target: edge.to, type: 'workflow-edge', markerEnd: { type: MarkerType.Arrow, width: 18, height: 18, color: '#d58aaa', strokeWidth: 2 }, data: edge }))
    setNodes(generatedNodes)
    setEdges(generatedEdges)
  } catch (error) {
    console.error('Error generating nodes and edges from YAML:', error)
  }
  if (fit && viewMode.value === 'graph') {
    await nextTick()
    fitView?.({ padding: 0.1 })
  }
}
const loadVueFlowGraph = async ({ fit = false } = {}) => {
  const selectionSnapshot = selectedFile.value
  const shouldFit = fit && viewMode.value === 'graph'
  const runFallback = async () => {
    if (selectedFile.value === selectionSnapshot) await generateNodesAndEdges({ fit: shouldFit })
    return false
  }
  if (!selectionSnapshot) return await runFallback()
  const key = selectionSnapshot.replace(/\.yaml$/i, '')
  if (!key) return await runFallback()
  try {
    const result = await fetchVueGraph(key)
    if (selectedFile.value !== selectionSnapshot) return false
    if (result?.status === 404) return await runFallback()
    if (!result?.success) return await runFallback()
    const content = result?.content
    if (!content) return await runFallback()
    let flow
    try { flow = JSON.parse(content) } catch (parseError) { return await runFallback() }
    fromObject?.(flow)
    await nextTick()
    if (selectedFile.value !== selectionSnapshot) return false
    syncNodeAndEdgeData()
    if (shouldFit) {
      await nextTick()
      if (selectedFile.value !== selectionSnapshot) return false
      fitView?.({ padding: 0.1 })
    }
    return true
  } catch (error) {
    console.error('Failed to load VueFlow graph:', error)
  }
  return await runFallback()
}
const switchToGraph = async () => {
  viewMode.value = 'graph'
  await nextTick()
  await loadVueFlowGraph({ fit: true })
}
const launchWorkflow = async () => {
  if (!selectedFile.value) {
    alert('Please choose a workflow file!')
    return
  }
  const trimmedPrompt = taskPrompt.value.trim()
  const attachmentIds = uploadedAttachments.value.map((attachment) => attachment.attachmentId)
  const attachmentNames = uploadedAttachments.value.map((attachment) => attachment.name || attachment.attachmentId)
  if (!trimmedPrompt && attachmentIds.length === 0) {
    alert('Please enter task prompt or upload files.')
    return
  }
  if (!ws || !isConnectionReady.value || !sessionId) {
    alert('WebSocket connection is not ready yet.')
    return
  }
  shouldGlow.value = false
  status.value = 'Launching...'
  try {
    const response = await fetch('/api/workflow/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ yaml_file: selectedFile.value, task_prompt: trimmedPrompt, session_id: sessionId, attachments: attachmentIds })
    })
    if (response.ok) {
      clearUploadedAttachments()
      await response.json()
      const fullMessage = []
      if (trimmedPrompt) fullMessage.push(trimmedPrompt)
      if (attachmentNames.length) fullMessage.push(`Attachments: ${attachmentNames.join(', ')}`)
      if (fullMessage.length) addDialogue('User', fullMessage.join('\n\n'))
      taskPrompt.value = ''
      status.value = 'Running...'
      isWorkflowRunning.value = true
    } else {
      const error = await response.json().catch(() => ({}))
      status.value = 'Failed'
      alert(`Failed to launch workflow: ${error.detail || 'Unknown error'}`)
      shouldGlow.value = true
      if (isConnectionReady.value) status.value = 'Waiting for launch...'
    }
  } catch (error) {
    status.value = 'Error'
    alert(`Failed to call execute API: ${error.message}`)
    shouldGlow.value = true
    if (isConnectionReady.value) status.value = 'Waiting for launch...'
  }
}
watch(status, (newStatus) => {
  if (newStatus === 'Completed' || newStatus === 'Cancelled') shouldGlow.value = true
})
const downloadArtifact = async (message) => {
  if (!sessionId || !message?.attachmentId) return
  try {
    let dataUri = message.dataUri
    if (!dataUri) {
      message.loading = true
      dataUri = await getAttachment(sessionId, message.attachmentId)
      if (!dataUri) throw new Error('Empty attachment data')
      message.dataUri = dataUri
    }
    const link = document.createElement('a')
    link.href = dataUri
    link.download = message.fileName || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    alert('Failed to download file, please try again.')
  } finally {
    if (message.loading) message.loading = false
  }
}
const handleEdgeConditionMessage = (message) => {
  const edgeMatch = message.match(/Edge condition met for (.+) -> (.+)/)
  if (!edgeMatch) return
  const sourceNode = edgeMatch[1].trim()
  const targetNode = edgeMatch[2].trim()
  const edge = edges.value.find(e => e.source === sourceNode && e.target === targetNode)
  if (!edge) return
  animateSpriteAlongEdge(edge)
}
const animateSpriteAlongEdge = (edge) => {
  let spriteSrc
  if (nameToSpriteMap.value.has(edge.source)) spriteSrc = nameToSpriteMap.value.get(edge.source)
  else {
    spriteSrc = spriteFetcher.fetchSprite(edge.source, 'D', 2)
    nameToSpriteMap.value.set(edge.source, spriteSrc)
  }
  const edgeId = `${edge.source}-${edge.target}`
  const edgeElement = document.querySelector(`[data-id="${edgeId}"]`)
  if (!edgeElement) return
  const pathElement = edgeElement.querySelector('path')
  if (!pathElement) return
  const svgElement = pathElement.closest('svg')
  if (!svgElement) return
  const pathLength = pathElement.getTotalLength()
  const spriteImage = document.createElementNS('http://www.w3.org/2000/svg', 'image')
  spriteImage.setAttribute('width', '32')
  spriteImage.setAttribute('height', '40')
  spriteImage.setAttribute('href', spriteSrc)
  spriteImage.setAttribute('x', '-16')
  spriteImage.setAttribute('y', '-20')
  spriteImage.style.pointerEvents = 'none'
  svgElement.appendChild(spriteImage)
  const startPoint = pathElement.getPointAtLength(0)
  const endPoint = pathElement.getPointAtLength(pathLength)
  const direction = endPoint.x >= startPoint.x ? 'R' : 'L'
  const duration = Math.min(Math.max(pathLength * 0.02, 2000), 4000)
  let startTime = null
  let frame = 1
  const animate = (timestamp) => {
    if (!startTime) startTime = timestamp
    const elapsed = timestamp - startTime
    const progress = Math.min(elapsed / duration, 1)
    const point = pathElement.getPointAtLength(progress * pathLength)
    spriteImage.setAttribute('transform', `translate(${point.x}, ${point.y})`)
    const frameIndex = Math.floor(elapsed / 250) % 4
    let targetFrame
    if (frameIndex === 0 || frameIndex === 2) targetFrame = 1
    else if (frameIndex === 1) targetFrame = 2
    else targetFrame = 3
    if (frame !== targetFrame) {
      frame = targetFrame
      const newSprite = spriteFetcher.fetchSprite(edge.source, direction, frame)
      spriteImage.setAttribute('href', newSprite)
    }
    if (progress < 1) requestAnimationFrame(animate)
    else svgElement.removeChild(spriteImage)
  }
  requestAnimationFrame(animate)
}
const processMessage = async (msg) => {
  if (msg.type === 'human_input_required') {
    const fullMessage = msg.data.task_description + '\n\n' + msg.data.input
    addDialogue(`${msg.data.node_id}`, `${fullMessage}`)
    status.value = 'Waiting for input...'
    shouldGlow.value = true
  }
  if (msg.type === 'artifact_created') {
    const events = msg?.data?.events
    if (Array.isArray(events)) {
      for (const event of events) {
        const nodeName = event?.node_id || 'Artifact'
        const fileName = event?.file_name || 'artifact'
        const mimeType = event?.mime_type || ''
        const attachmentId = event?.attachment_id
        let avatar
        if (nameToSpriteMap.value.has(nodeName)) avatar = nameToSpriteMap.value.get(nodeName)
        else {
          avatar = spriteFetcher.fetchSprite()
          nameToSpriteMap.value.set(nodeName, avatar)
        }
        const message = { type: 'dialogue', name: nodeName, text: '', avatar, isRight: false, isArtifact: true, fileName, mimeType, attachmentId, isImage: !!mimeType && mimeType.includes('image'), dataUri: null, loading: true, error: null, timestamp: Date.now() }
        chatMessages.value.push(message)
        if (message.isImage && sessionId && attachmentId) {
          try {
            const dataUri = await getAttachment(sessionId, attachmentId)
            message.dataUri = dataUri
          } catch (error) {
            message.error = 'Failed to load image'
          } finally {
            message.loading = false
          }
        } else {
          message.loading = false
        }
      }
    }
  }
  if (msg.type === 'log' && (msg.data.level === 'WARNING' || msg.data.level === 'ERROR')) {
    const notificationType = msg.data.level === 'WARNING' ? 'warning' : 'error'
    addChatNotification(msg.data.message, { type: notificationType })
  }
  if (msg.type === 'log' && msg.data.level === 'INFO') {
    const eventType = msg.data.event_type
    const nodeId = msg.data.node_id
    if (eventType === 'NODE_START') {
      if (nodeId && !activeNodes.value.includes(nodeId)) activeNodes.value.push(nodeId)
    } else if (eventType === 'MODEL_CALL') {
      if (msg.data.details.stage === 'before') addLoadingEntry(nodeId, `model-${msg.data.details.model_name || 'unknown'}`, `Model ${msg.data.details.model_name}`)
      if (msg.data.details.stage === 'after') finishLoadingEntry(nodeId, `model-${msg.data.details.model_name || 'unknown'}`)
    } else if (eventType === 'TOOL_CALL') {
      if (msg.data.details.stage === 'before') addLoadingEntry(nodeId, `tool-${msg.data.details.tool_name || 'unknown'}`, `Tool ${msg.data.details.tool_name}`)
      if (msg.data.details.stage === 'after') finishLoadingEntry(nodeId, `tool-${msg.data.details.tool_name || 'unknown'}`)
    } else if (eventType === 'NODE_END') {
      if (nodeId) {
        const index = activeNodes.value.indexOf(nodeId)
        if (index > -1) activeNodes.value.splice(index, 1)
        const nodeState = nodesLoadingMessagesMap.get(nodeId)
        if (nodeState) {
          const endedAt = Date.now()
          finalizeAllLoadingEntries(nodeState, endedAt)
          nodeState.message.isLoading = false
          nodeState.message.duration = formatDuration(nodeState.message.startedAt, endedAt)
          nodesLoadingMessagesMap.delete(nodeId)
        }
      }
      addDialogue(`${nodeId}`, `${msg.data.details.output}`)
    } else if (msg.data.message && msg.data.message.includes('Edge condition met for')) {
      handleEdgeConditionMessage(msg.data.message)
    } else {
      addChatNotification(msg.data.message)
    }
  }
  if (msg.type === 'workflow_completed') {
    addChatNotification(msg.data.summary)
    status.value = 'Completed'
    isWorkflowRunning.value = false
    sessionIdToDownload = sessionId
  }
  if (msg.type === 'error') {
    const errorMessage = msg.data?.message || 'Unknown error occurred'
    addChatNotification(errorMessage, { type: 'error' })
    status.value = 'Error'
    isWorkflowRunning.value = false
    sessionIdToDownload = sessionId
  }
}
const cancelWorkflow = () => {
  if (!isWorkflowRunning.value || !ws) return
  addChatNotification('Workflow cancelled')
  status.value = 'Cancelled'
  isWorkflowRunning.value = false
  sessionIdToDownload = sessionId
  const endedAt = Date.now()
  for (const [nodeId, nodeState] of nodesLoadingMessagesMap.entries()) {
    if (nodeState?.message) {
      finalizeAllLoadingEntries(nodeState, endedAt)
      nodeState.message.isLoading = false
      nodeState.message.duration = formatDuration(nodeState.message.startedAt, endedAt)
      nodesLoadingMessagesMap.delete(nodeId)
    }
  }
  try { ws.close() } catch (closeError) { console.warn('Failed to close WebSocket:', closeError) }
}
const downloadLogs = async () => {
  if (!sessionIdToDownload) return
  try {
    await fetchLogsZip(sessionIdToDownload)
  } catch (error) {
    alert('Download failed, please try again later')
  }
}
const getFilePreviewSrc = (message) => {
  try {
    const fileName = message?.fileName || ''
    const mimeType = message?.mimeType || ''
    if (message?.isImage && message?.dataUri) return message.dataUri
    return getPreviewIconByExt(fileName, mimeType)
  } catch (e) {
    return ''
  }
}
const getPreviewIconByExt = (fileName = '', mimeType = '') => {
  const ext = (fileName.split('.').pop() || '').toLowerCase()
  const isImg = mimeType.includes('image') || ['png','jpg','jpeg','gif','webp','svg','bmp','tiff','ico'].includes(ext)
  if (isImg) return svgIconDataUri('IMG', '#d78cab')
  const map = {
    pdf: ['PDF', '#e78aa0'], doc: ['DOC', '#c78ae7'], docx: ['DOC', '#c78ae7'], xls: ['XLS', '#d889b0'], xlsx: ['XLS', '#d889b0'], csv: ['CSV', '#ca78a2'],
    ppt: ['PPT', '#ef98b1'], pptx: ['PPT', '#ef98b1'], txt: ['TXT', '#b78597'], log: ['LOG', '#b78597'], md: ['MD', '#c08ea0'], json: ['JSON', '#d5a0b4'], yaml: ['YML', '#d59ab4'], yml: ['YML', '#d59ab4'],
    zip: ['ZIP', '#b992df'], rar: ['ZIP', '#b992df'], '7z': ['ZIP', '#b992df'], tar: ['ZIP', '#b992df'], gz: ['ZIP', '#b992df'], py: ['PY', '#d88daf'], js: ['JS', '#eaa3be'], ts: ['TS', '#cc8fd7'], jsx: ['JSX', '#c788cf'], tsx: ['TSX', '#c788cf'],
    html: ['HTML', '#e794b1'], css: ['CSS', '#d38dad'], scss: ['SCSS', '#cf8bc0'], mp3: ['AUD', '#c98cb7'], wav: ['AUD', '#c98cb7'], flac: ['AUD', '#c98cb7'], mp4: ['VID', '#c08ce0'], mov: ['VID', '#c08ce0'], avi: ['VID', '#c08ce0'], mkv: ['VID', '#c08ce0']
  }
  const [label, color] = map[ext] || ['FILE', '#c998af']
  return svgIconDataUri(label, color)
}
const svgIconDataUri = (label, bgColor) => {
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
  <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48'>
    <defs><style>.t{font: 700 16px \"Inter, Arial\"; fill: #fff8fb}</style></defs>
    <rect x='0' y='0' width='48' height='48' rx='8' ry='8' fill='${bgColor}' />
    <text x='50%' y='58%' text-anchor='middle' class='t'>${(label || '').toUpperCase().slice(0,4)}</text>
  </svg>`
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}
watch(() => chatMessages.value.length, async () => {
  await nextTick()
  if (chatMessagesRef.value) chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
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
  opacity: 0.32;
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

.left-panel { flex: 3; display: flex; flex-direction: column; gap: 20px; min-width: 0; position: relative; }
.right-panel { flex: 1; display: flex; flex-direction: column; gap: 20px; min-width: 250px; }

.chat-panel {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 380px;
  max-width: 50%;
  z-index: 10;
  display: flex;
  flex-direction: row;
  pointer-events: none;
  transition: width 0.3s ease;
}

.chat-panel-fullscreen {
  position: relative;
  width: 100%;
  max-width: 100%;
  flex: 1;
  flex-direction: column;
  pointer-events: auto;
  z-index: auto;
  min-height: 0;
}

.chat-panel-collapsed { width: 0; }

.chat-panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  min-height: 0;
  pointer-events: auto;
  border-radius: 18px;
  overflow: hidden;
  padding: 0;
}

.chat-panel-toggle {
  position: absolute;
  top: 12px;
  right: -32px;
  width: 28px;
  height: 28px;
  border-radius: 0 8px 8px 0;
  border: 1px solid rgba(223, 156, 185, 0.2);
  border-left: none;
  background: rgba(255, 250, 252, 0.92);
  color: #a45b7a;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
  padding: 0;
  z-index: 11;
}

.chat-panel-toggle svg { transition: transform 0.3s ease; }
.chat-panel-toggle .chevron-collapsed { transform: rotate(180deg); }
.chat-panel-collapsed .chat-panel-toggle { right: -32px; left: auto; }
.chat-box { flex: 1; overflow: hidden; display: flex; flex-direction: column; min-height: 0; }
.chat-messages::-webkit-scrollbar { width: 8px; height: 8px; }
.chat-messages::-webkit-scrollbar-track { background: transparent; }
.chat-messages::-webkit-scrollbar-thumb { background-color: rgba(210, 151, 177, 0.3); border-radius: 8px; border: 2px solid transparent; background-clip: padding-box; }
.chat-messages { flex: 1; padding: 20px; overflow-y: auto; color: #6a4654; display: flex; flex-direction: column; gap: 12px; }
.chat-notification { display: flex; justify-content: center; margin: 10px 0; }
.notification-content { background: rgba(255, 239, 246, 0.85); border: 1px solid rgba(223, 156, 185, 0.18); border-radius: 20px; padding: 8px 16px; max-width: 80%; display: flex; flex-direction: column; align-items: center; }
.notification-text { color: #8f6174; font-size: 13px; font-weight: 500; text-align: center; word-break: break-word; overflow-wrap: anywhere; }
.chat-notification-warning .notification-content { background: rgba(255, 233, 242, 0.95); border-color: rgba(238, 154, 184, 0.35); }
.chat-notification-warning .notification-text { color: #b05d83; }
.chat-notification-error .notification-content { background: rgba(255, 221, 231, 0.95); border-color: rgba(215, 101, 137, 0.35); color: #9a3f62; }
.message-timestamp { font-size: 0.75rem; color: #b08897; margin-left: 8px; flex-shrink: 0; }
.chat-notification .message-timestamp { margin-left: 0; margin-top: 4px; color: #b995a3; }
.dialogue { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 8px; }
.dialogue-right { flex-direction: row-reverse; }
.message-content { flex: 1; max-width: 85%; display: flex; flex-direction: column; gap: 4px; align-items: flex-start; }
.dialogue-right .message-content { align-items: flex-end; }
.user-name { display: flex; align-items: baseline; justify-content: flex-start; font-size: 12px; color: #9f7a89; font-weight: 600; margin: 0 4px; }
.dialogue-right .user-name { flex-direction: row-reverse; text-align: right; }
.profile-picture { flex-shrink: 0; width: 40px; height: 40px; border-radius: 50%; overflow: hidden; border: 1px solid rgba(223, 156, 185, 0.22); background: rgba(255, 248, 251, 0.7); }
.profile-picture img { width: 100%; height: 100%; object-fit: cover; object-position: 50% 20%; }
.message-bubble { background: rgba(255, 245, 249, 0.82); border: 1px solid rgba(223, 156, 185, 0.16); border-radius: 16px; border-top-left-radius: 4px; padding: 0 16px; position: relative; }
.dialogue-right .message-bubble { background: linear-gradient(135deg, rgba(255, 229, 240, 0.92), rgba(245, 222, 255, 0.9)); border-color: rgba(223, 156, 185, 0.2); border-top-left-radius: 16px; border-top-right-radius: 4px; }
.loading-bubble { border-color: rgba(223, 156, 185, 0.4); box-shadow: 0 0 12px rgba(226, 150, 182, 0.18); }
.loading-timer { margin-left: 8px; margin-bottom: 10px; font-size: 12px; color: #9f7a89; }
.loading-entries { display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0 4px; padding: 2px 0; border-radius: 10px; }
.loading-entry { display: flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 12px; background: rgba(255, 250, 252, 0.82); border: 1px solid rgba(223, 156, 185, 0.16); }
.loading-entry-label { font-size: 14px; color: #744c5f; }
.loading-entry-duration { font-size: 12px; color: #9f7a89; }
.entry-running { border-color: rgba(223, 156, 185, 0.32); box-shadow: 0 0 8px rgba(226, 150, 182, 0.14); }
.entry-done { border-color: rgba(223, 156, 185, 0.14); opacity: 0.85; }
.loading-entry-enter-active, .loading-entry-leave-active { transition: all 0.22s ease-out; }
.loading-entry-enter-from, .loading-entry-leave-to { opacity: 0; transform: translateY(4px); }
.loading-entry-enter-to, .loading-entry-leave-from { opacity: 1; transform: translateY(0); }
.message-text { color: #5f3b4b; font-size: 14px; line-height: 1.5; word-wrap: break-word; white-space: pre-wrap; }
.artifact-image-wrapper, .artifact-file-wrapper { padding: 10px 0; }
.artifact-image { max-width: 260px; max-height: 200px; display: block; cursor: zoom-in; border-radius: 10px; padding: 0 0 10px 0; }
.artifact-filename { margin-top: 4px; font-size: 12px; color: #9f7a89; display: flex; align-items: center; gap: 6px; }
.artifact-filename-icon { width: 18px; height: 18px; border-radius: 3px; object-fit: cover; flex-shrink: 0; }
.artifact-filename-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.artifact-download-button { margin-top: 15px; padding: 6px 12px; border-radius: 999px; border: 1px solid rgba(223, 156, 185, 0.24); background: rgba(255, 249, 252, 0.88); color: #a45b7a; font-size: 12px; cursor: pointer; }
.artifact-status { font-size: 12px; color: #9f7a89; }
.artifact-status.artifact-error { color: #c55f84; }
.input-area { flex: 0 0 auto; min-height: 120px; }
.input-shell { height: 100%; display: flex; flex-direction: row; background-color: rgba(255, 248, 251, 0.76); border: 1px solid rgba(223, 156, 185, 0.18); border-radius: 18px; transition: all 0.3s ease; position: relative; }
.input-shell:focus-within { border-color: rgba(223, 156, 185, 0.34); background-color: rgba(255, 250, 252, 0.92); }
.input-shell.glow { border-color: rgba(223, 156, 185, 0.42); box-shadow: 0 0 15px rgba(226, 150, 182, 0.18); }
.input-shell.drag-active { border-color: rgba(223, 156, 185, 0.52); background-color: rgba(255, 239, 246, 0.9); box-shadow: 0 0 20px rgba(226, 150, 182, 0.22); }
.drag-overlay { position: absolute; inset: 6px; border-radius: 14px; border: 1px dashed rgba(223, 156, 185, 0.6); background: rgba(255, 247, 251, 0.75); display: flex; align-items: center; justify-content: center; pointer-events: none; }
.drag-overlay-content { font-size: 12px; letter-spacing: 0.6px; text-transform: uppercase; color: #b25c82; }
.task-input { flex: 1; padding: 16px; border: none; font-family: 'Inter', sans-serif; font-size: 14px; resize: none; outline: none; background: transparent; color: #5f3b4b; line-height: 1.5; }
.task-input::placeholder { color: #b08a99; }
.input-footer { display: flex; justify-content: flex-end; padding: 10px 12px 10px 6px; border-top: 1px solid rgba(223, 156, 185, 0.12); }
.input-footer-buttons { display: flex; align-items: flex-end; justify-content: space-between; flex-direction: column; height: 100%; }
.attachment-upload { position: relative; }
.attachment-button-wrapper { position: relative; display: inline-block; }
.attachment-button { padding: 6px 16px; border-radius: 20px; border: 1px solid rgba(223, 156, 185, 0.22); background: rgba(255, 250, 252, 0.8); color: #9f5d7d; cursor: pointer; font-size: 12px; font-weight: 600; }
.attachment-button:hover:not(:disabled) { background: rgba(255, 245, 249, 0.96); color: #b25c82; }
.attachment-button:disabled { opacity: 0.5; cursor: not-allowed; }
.hidden-file-input { display: none; }
.attachment-count { position: absolute; top: -8px; right: -6px; background: #e9b4ca; color: #5b3041; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 10px; }
.attachment-modal { position: absolute; right: 0; bottom: calc(100% + 10px); width: 240px; background: rgba(255, 250, 252, 0.98); border: 1px solid rgba(223, 156, 185, 0.18); border-radius: 14px; padding: 8px; box-shadow: 0 14px 30px rgba(212, 142, 175, 0.18); display: flex; flex-direction: column; gap: 6px; z-index: 10; }
.attachment-item { display: flex; align-items: center; justify-content: space-between; padding: 6px 10px; background: rgba(255, 245, 249, 0.85); border-radius: 10px; }
.attachment-name { font-size: 12px; color: #6a4654; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.remove-attachment { border: none; background: transparent; color: #c0608b; cursor: pointer; padding: 0 4px; }
.control-section { flex: 1; display: flex; flex-direction: column; gap: 16px; border-radius: 20px; padding: 20px; }
.section-label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #9f7a89; font-weight: 700; margin-top: 4px; }
.select-wrapper { position: relative; }
.custom-file-selector { position: relative; }
.file-selector-input { width: 100%; box-sizing: border-box; padding: 10px 12px; padding-right: 30px; background-color: rgba(255, 248, 251, 0.92); border: 1px solid rgba(223, 156, 185, 0.18); border-radius: 12px; color: #5f3b4b; font-size: 14px; }
.file-selector-input:hover:not(:disabled), .file-selector-input:focus { background-color: rgba(255, 250, 252, 0.98); border-color: rgba(223, 156, 185, 0.32); }
.file-selector-input:disabled { opacity: 0.5; cursor: not-allowed; }
.select-arrow { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #b08a99; pointer-events: none; font-size: 10px; }
.file-dropdown { position: absolute; top: calc(100%); left: 0; right: 0; margin-top: 1px; background-color: rgba(255, 250, 252, 0.98); border: 1px solid rgba(223, 156, 185, 0.2); border-radius: 12px; box-shadow: 0 20px 40px rgba(212, 142, 175, 0.16); max-height: 260px; overflow-y: auto; z-index: 5; padding: 6px 0; }
.file-dropdown::-webkit-scrollbar { display: none; }
.file-option { display: flex; flex-direction: column; gap: 4px; padding: 8px 14px; cursor: pointer; transition: background 0.15s ease; }
.file-option:hover { background: rgba(255, 240, 247, 0.9); }
.file-name { color: #5f3b4b; font-size: 12px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-desc { color: #987181; font-size: 11px; }
.file-empty { padding: 12px 14px; color: #987181; font-size: 13px; text-align: center; }
.file-dropdown-enter-active, .file-dropdown-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.file-dropdown-enter-from, .file-dropdown-leave-to { opacity: 0; transform: translateY(-4px); }
.status-display { padding: 12px; background: rgba(255, 245, 249, 0.88); border-radius: 12px; color: #8f6c7c; font-size: 13px; text-align: center; }
.status-active { color: #b05c81; background: rgba(255, 230, 239, 0.92); }
.view-toggle { display: flex; background: rgba(255, 245, 249, 0.88); padding: 4px; border-radius: 12px; }
.toggle-button { flex: 1; padding: 8px; border: none; background: transparent; color: #9f7a89; cursor: pointer; border-radius: 10px; font-size: 13px; transition: all 0.2s ease; }
.toggle-button.active { background: rgba(255, 255, 255, 0.8); color: #5f3b4b; font-weight: 700; }
.button-section { display: flex; flex-direction: column; gap: 12px; }
.cancel-button, .launch-button, .download-button { padding: 13px 14px; border-radius: 16px; font-size: 14px; font-weight: 700; transition: all 0.2s ease; }
.cancel-button { border: none; color: #7f2f4d; background: linear-gradient(135deg, #ffc7da, #f5b9d0, #eba8c3); }
.cancel-button:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 10px 22px rgba(224, 132, 172, 0.2); }
.cancel-button:disabled { background: #eddbe3; color: #c5a8b4; cursor: not-allowed; }
.launch-button { border: none; color: #6b3046; background: linear-gradient(135deg, #ffd6e6, #f2d6ff, #ffc5df); }
.launch-button:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 10px 22px rgba(226, 150, 182, 0.2); }
.launch-button:disabled { background: #eddbe3; color: #c5a8b4; cursor: not-allowed; }
.launch-button.glow { box-shadow: 0 0 0 0 rgba(231, 143, 179, 0.25); animation: glowPulse 3s ease-in-out infinite; }
@keyframes glowPulse { 0% { box-shadow: 0 0 0 0 rgba(231, 143, 179, 0.25); } 50% { box-shadow: 0 0 0 7px rgba(231, 143, 179, 0); } 100% { box-shadow: 0 0 0 0 rgba(231, 143, 179, 0); } }
.download-button { background: rgba(255, 250, 252, 0.8); border: 1px solid rgba(223, 156, 185, 0.18); color: #8f5e77; cursor: pointer; }
.download-button:hover:not(:disabled) { background: rgba(255, 245, 249, 0.96); transform: translateY(-1px); }
.download-button:disabled { opacity: 0.5; cursor: not-allowed; }
.graph-panel { flex: 1; border-radius: 20px; overflow: hidden; }
.vueflow-graph { width: 100%; height: 100%; }
.image-modal { position: fixed; inset: 0; background: rgba(255, 243, 248, 0.62); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(3px); }
.image-modal-content { position: relative; max-width: 95vw; max-height: 95vh; display: flex; flex-direction: column; gap: 12px; align-items: center; padding: 20px; border-radius: 18px; }
.image-modal-content img { max-width: 70vw; max-height: 65vh; box-shadow: 0 20px 40px rgba(212, 142, 175, 0.18); }
.image-modal-enter-active, .image-modal-leave-active { transition: opacity 0.2s ease; }
.image-modal-enter-from, .image-modal-leave-to { opacity: 0; }
.settings-button { background: rgba(255, 255, 255, 0.65); border: 1px solid rgba(223, 156, 185, 0.22); color: #a35b79; cursor: pointer; padding: 8px; border-radius: 12px; display: flex; align-items: center; justify-content: center; transition: background-color 0.2s; }
.settings-button:hover { background-color: rgba(255, 245, 249, 0.95); }
</style>
