<template>
  <div class="workflow-list">
    <div class="header-container">
      <div class="search-container">
        <span class="search-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        <input type="text" v-model="searchQuery" placeholder="Search workflows" class="search-input" />
      </div>

      <button class="btn create-btn" @click="openFormGenerator" title="Create New Workflow">
        <span>Create Workflow</span>
        <span class="plus-icon">+</span>
      </button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading workflows...</p>
    </div>

    <div v-else-if="error" class="error-message">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
      <button @click="loadWorkflows()" class="retry-button">Retry</button>
    </div>

    <div v-else class="file-list">
      <transition-group name="file-fade" tag="div" class="file-list-inner">
        <div
          v-for="file in filteredFiles"
          :key="file.name"
          :class="['file-item', { active: isSelected(file) }]"
          @click="goToWorkflowView(file.name)"
        >
          <div class="file-info">
            <div class="file-name">{{ file.name }}</div>
            <div class="file-description">{{ file.description }}</div>
          </div>
          <div class="file-arrow">→</div>
        </div>
      </transition-group>

      <div v-if="filteredFiles.length === 0" class="empty-state">
        <div class="empty-title">🌸 Nothing here yet</div>
        <p>No workflow files found</p>
      </div>
    </div>

    <Teleport to="body">
      <FormGenerator
        v-if="showFormGenerator"
        :breadcrumbs="[{node: 'DesignConfig', field: 'graph'}]"
        :recursive="false"
        @close="closeFormGenerator"
        @submit="handleFormGeneratorSubmit"
      />
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { fetchWorkflowsWithDesc } from '../utils/apiFunctions.js'
import FormGenerator from '../components/FormGenerator.vue'

const router = useRouter()
const props = defineProps({
  selected: {
    type: String,
    default: ''
  },
  useRouting: {
    type: Boolean,
    default: true
  }
})
const emit = defineEmits(['select'])
const yamlFiles = ref([])
const loading = ref(false)
const error = ref(null)

const showFormGenerator = ref(false)
const searchQuery = ref('')

const loadWorkflows = async () => {
  loading.value = true
  error.value = null

  const result = await fetchWorkflowsWithDesc()
  if (result.success) {
    yamlFiles.value = result.workflows
  } else {
    error.value = result.error
  }

  loading.value = false
}

defineExpose({
  loadWorkflows
})

const filteredFiles = computed(() => {
  const rawList = Array.isArray(yamlFiles.value) ? [...yamlFiles.value] : []
  const query = searchQuery.value.toLowerCase().trim()
  let result = rawList

  if (query) {
    result = rawList.filter(file => {
      const name = (file?.name ?? '').toString().toLowerCase()
      const desc = (file?.description ?? '').toString().toLowerCase()
      if (!name && !desc) return false
      return name.includes(query) || desc.includes(query)
    })
  }

  return result.sort((a, b) => {
    const nameA = a?.name ?? ''
    const nameB = b?.name ?? ''
    return nameA.localeCompare(nameB, 'zh')
  })
})

onMounted(() => {
  loadWorkflows()
})

const normalizeName = (fileName) => fileName?.replace?.('.yaml', '') ?? ''

const goToWorkflowView = (fileName) => {
  const workflowName = normalizeName(fileName)
  if (props.useRouting) {
    router.push(`/workflows/${workflowName}`)
  }
  emit('select', workflowName)
}

const isSelected = (file) => {
  const name = normalizeName(file?.name)
  return props.selected && props.selected === name
}

const extractGraphIdFromPayload = (payload) => {
  if (!payload) return null
  const graphId = payload.fullYaml?.graph?.id
  if (!graphId) return null
  return String(graphId).trim()
}

const openFormGenerator = () => {
  showFormGenerator.value = true
}

const closeFormGenerator = () => {
  showFormGenerator.value = false
}

const handleFormGeneratorSubmit = async (payload) => {
  await loadWorkflows()
  showFormGenerator.value = false

  const graphId = extractGraphIdFromPayload(payload)
  if (!graphId) return

  const fileName = graphId.endsWith('.yaml') ? graphId : `${graphId}.yaml`
  goToWorkflowView(fileName)
}
</script>

<style scoped>
.workflow-list {
  width: 100%;
  height: 100%;
  background: transparent;
  padding: 12px;
  box-sizing: border-box;
  font-family: 'Inter', sans-serif;
  color: #5b3446;
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
}

.workflow-list::-webkit-scrollbar { display: none; }

.header-container,
.file-list,
.loading,
.error-message,
.empty-state {
  position: relative;
  z-index: 1;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  width: 100%;
}

.search-container {
  display: flex;
  align-items: center;
  background: rgba(255, 248, 251, 0.82);
  border: 1px solid rgba(223, 156, 185, 0.18);
  border-radius: 18px;
  padding: 10px 12px;
  width: 110px;
  min-height: 20px;
  transition: all 0.3s ease;
  backdrop-filter: blur(8px);
}

.search-container:hover,
.search-container:focus-within {
  background: rgba(255, 250, 252, 0.94);
  border-color: rgba(223, 156, 185, 0.34);
  width: 180px;
  box-shadow: 0 12px 24px rgba(212, 142, 175, 0.12);
}

.search-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  color: #b38a99;
  transition: color 0.3s ease;
}

.search-container:focus-within .search-icon {
  color: #c0618c;
}

.search-input {
  background: transparent;
  border: none;
  color: #5f3b4b;
  font-size: 14px;
  font-weight: 600;
  width: 100%;
  outline: none;
  font-family: 'Inter', sans-serif;
}

.search-input::placeholder {
  color: #c19baa;
}

.create-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  border: none;
  padding: 10px 16px;
  min-height: 40px;
  font-size: 14px;
  font-weight: 700;
  border-radius: 18px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  color: #6a2f47;
  background: linear-gradient(90deg, #ffd6e6, #f2d6ff, #ffc4de);
  background-size: 200% 100%;
  animation: gradientShift 4s ease-in-out infinite;
  box-shadow: 0 12px 24px rgba(226, 150, 182, 0.18);
  position: relative;
  overflow: hidden;
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 28px rgba(226, 150, 182, 0.24);
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 0%; }
  50% { background-position: 100% 0%; }
}

.plus-icon {
  font-size: 16px;
  font-weight: 700;
  line-height: 1;
}

.file-list {
  display: flex;
  flex-direction: column;
  max-width: 1000px;
  margin: 0 auto;
}

.file-list-inner {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-fade-enter-active,
.file-fade-leave-active {
  transition: all 0.2s ease;
}

.file-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.file-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.file-fade-leave-active {
  position: absolute;
  width: 100%;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  background: rgba(255, 250, 252, 0.76);
  border: 1px solid rgba(223, 156, 185, 0.16);
  border-radius: 18px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
  box-shadow: 0 12px 26px rgba(212, 142, 175, 0.08);
}

.file-item:hover {
  background: rgba(255, 246, 250, 0.96);
  transform: translateY(-2px);
  border-color: rgba(223, 156, 185, 0.3);
}

.file-item.active {
  border-color: rgba(212, 126, 165, 0.5);
  box-shadow: 0 0 0 1px rgba(212, 126, 165, 0.18), 0 14px 30px rgba(212, 142, 175, 0.14);
}

.file-item.active .file-arrow {
  color: #c0618c;
}

.file-info {
  flex: 1;
}

.file-name {
  font-size: 13px;
  font-weight: 700;
  color: #5f3b4b;
  margin-bottom: 4px;
}

.file-description {
  color: #92707e;
  font-size: 12px;
  line-height: 1.4;
}

.file-arrow {
  color: #c29aaa;
  font-size: 20px;
  font-weight: 300;
  transition: transform 0.3s ease, color 0.3s ease;
  margin-left: 16px;
}

.file-item:hover .file-arrow {
  color: #c0618c;
  transform: translateX(4px);
}

.loading, .error-message, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #92707e;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(223, 156, 185, 0.18);
  border-top-color: #c0618c;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.retry-button {
  margin-top: 16px;
  padding: 10px 24px;
  background: linear-gradient(90deg, #fff8fb, #ffe8f3);
  color: #b05c81;
  border: 1px solid rgba(223, 156, 185, 0.22);
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 600;
}

.retry-button:hover {
  background: linear-gradient(90deg, #ffd6e6, #f0d7ff, #ffc4de);
}

.empty-title {
  font-weight: 700;
  color: #b25c82;
  margin-bottom: 8px;
}
</style>
