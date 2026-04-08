<template>
  <div class="workflow-workbench">
    <div class="workflow-sidebar sakura-panel" :class="{ open: isSidebarOpen }">
      <WorkflowList
        ref="workflowListRef"
        :use-routing="false"
        :selected="selectedWorkflow"
        @select="handleSelect"
      />
    </div>
    <button
      class="sidebar-toggle-btn"
      :class="{ 'sidebar-open': isSidebarOpen }"
      @click="handleToggleSidebar"
      aria-label="Toggle sidebar"
    >
      <span v-if="isSidebarOpen">‹</span>
      <span v-else>›</span>
    </button>
    <div class="workflow-viewer" :class="{ 'sidebar-open': isSidebarOpen }">
      <WorkflowView
        v-if="selectedWorkflow"
        :workflow-name="selectedWorkflow"
        :key="selectedWorkflow"
        @refresh-workflows="handleRefreshWorkflows"
      />
      <div v-else class="placeholder sakura-panel">
        <div class="placeholder-eyebrow">🌸 Workflow Garden</div>
        <div class="placeholder-title">Select a workflow</div>
        <div class="placeholder-subtitle">Choose a workflow from the list to view, edit, and evolve it.</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WorkflowList from './WorkflowList.vue'
import WorkflowView from './WorkflowView.vue'

const route = useRoute()
const router = useRouter()
const workflowListRef = ref(null)

const normalizeName = (name) => name?.replace?.('.yaml', '') ?? ''
const selectedWorkflow = ref(normalizeName(route.params.name))
const isSidebarOpen = ref(true)

watch(
  () => route.params.name,
  (name) => {
    selectedWorkflow.value = normalizeName(name)
  },
  { immediate: true }
)

function handleToggleSidebar() {
  isSidebarOpen.value = !isSidebarOpen.value
  window.dispatchEvent(new CustomEvent('workflow-sidebar-state', { detail: { open: isSidebarOpen.value } }))
}

onMounted(() => {
  window.addEventListener('toggle-workflow-sidebar', handleToggleSidebar)
})

onBeforeUnmount(() => {
  window.removeEventListener('toggle-workflow-sidebar', handleToggleSidebar)
})

const handleSelect = (name) => {
  const normalized = normalizeName(name)
  selectedWorkflow.value = normalized
  isSidebarOpen.value = false
  window.dispatchEvent(new CustomEvent('workflow-sidebar-state', { detail: { open: isSidebarOpen.value } }))

  if (normalized) {
    router.push({ path: `/workflows/${normalized}` })
  } else {
    router.push({ path: '/workflows' })
  }
}

const handleRefreshWorkflows = async () => {
  if (workflowListRef.value?.loadWorkflows) {
    await workflowListRef.value.loadWorkflows()
  }
}
</script>

<style scoped>
.workflow-workbench {
  position: relative;
  display: flex;
  height: calc(100vh - 62px);
  background: transparent;
  color: #5b3446;
  overflow: hidden;
}

.sakura-panel {
  background: rgba(255, 250, 252, 0.76);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(223, 156, 185, 0.18);
  box-shadow: 0 18px 44px rgba(212, 142, 175, 0.12);
}

.workflow-sidebar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 400px;
  transform: translateX(calc(-100% + 10px));
  transition: transform 0.35s cubic-bezier(.77,.2,.05,1.0);
  z-index: 3;
  border-right: 1px solid rgba(223, 156, 185, 0.14);
  overflow-y: auto;
  overflow-x: hidden;
  border-radius: 0 22px 22px 0;
}

.workflow-sidebar.open {
  transform: translateX(0);
}

.sidebar-toggle-btn {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 72px;
  padding: 12px;
  background: linear-gradient(180deg, #fff8fb, #ffe9f3);
  border: 1px solid rgba(223, 156, 185, 0.25);
  border-left: none;
  border-radius: 0 12px 12px 0;
  color: #b05c81;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  transition: left 0.35s cubic-bezier(.77,.2,.05,1.0), background 0.2s, color 0.2s, border-color 0.2s;
  box-shadow: 4px 0 12px rgba(212, 142, 175, 0.16);
}

.sidebar-toggle-btn.sidebar-open {
  left: 400px;
}

.sidebar-toggle-btn:hover {
  background: linear-gradient(180deg, #ffdbe9, #ffe9f5);
  color: #9f456d;
  border-color: rgba(223, 156, 185, 0.45);
}

.sidebar-toggle-btn span {
  font-weight: 700;
  line-height: 1;
}

.workflow-viewer {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: margin-left 0.35s cubic-bezier(.77,.2,.05,1.0);
  margin-left: 10px;
}

.placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  color: #73515f;
  text-align: center;
  padding: 24px;
  margin: 20px;
  border-radius: 24px;
}

.placeholder-eyebrow {
  font-size: 13px;
  font-weight: 700;
  color: #b25c82;
  margin-bottom: 12px;
}

.placeholder-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #5b3041;
}

.placeholder-subtitle {
  font-size: 14px;
  color: #8b6877;
}
</style>
