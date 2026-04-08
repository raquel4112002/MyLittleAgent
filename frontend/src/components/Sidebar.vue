<template>
    <div class="sidebar" :class="{ 'is-hidden': isHidden }" @mouseenter="isHidden = false">
        <div class="brand-mark">🌸 MyLittleAgent</div>

        <nav class="sidebar-nav">
            <router-link to="/">Home</router-link>
            <router-link to="/tutorial">Guide</router-link>
            <router-link
                to="/workflows"
                :class="{ active: isWorkflowsActive }"
            >Workflows</router-link>
            <router-link to="/observability">Monitor</router-link>
            <router-link to="/launch" target="_blank" rel="noopener">Launch</router-link>
            <router-link to="/batch-run" target="_blank" rel="noopener">Lab</router-link>
        </nav>
        <div class="sidebar-actions">
            <button class="settings-nav-btn" @click="showSettingsModal = true" title="Settings">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
            </button>
        </div>
    </div>
    <div class="sidebar-hit-area" v-if="isHidden" @mouseenter="isHidden = false"></div>
    <SettingsModal
      :is-visible="showSettingsModal"
      @update:is-visible="showSettingsModal = $event"
    />
</template>

<script setup>
import { useRoute } from 'vue-router'
import { computed, ref, onUnmounted, watch } from 'vue'
import SettingsModal from './SettingsModal.vue'

const showSettingsModal = ref(false)
const isHidden = ref(false)

watch(isHidden, (val) => {
    if (val) {
        document.body.classList.add('nav-hidden')
    } else {
        document.body.classList.remove('nav-hidden')
    }
})

const route = useRoute()
const isWorkflowsActive = computed(() => route.path.startsWith('/workflows'))

let lastScrollY = 0
const handleScroll = (e) => {
    const currentScrollY = e.target.scrollTop || window.scrollY || 0
    if (Math.abs(currentScrollY - lastScrollY) < 5) return

    if (currentScrollY > lastScrollY && currentScrollY > 10) {
        isHidden.value = true
    } else if (currentScrollY < lastScrollY) {
        isHidden.value = false
    }
    lastScrollY = currentScrollY <= 0 ? 0 : currentScrollY
}

const toggleScrollListener = (shouldListen) => {
    if (shouldListen) {
        window.addEventListener('scroll', handleScroll, true)
    } else {
        window.removeEventListener('scroll', handleScroll, true)
        isHidden.value = false
    }
}

watch(() => route.path, () => {
    toggleScrollListener(!!route.meta.hideNavOnScroll)
}, { immediate: true })

onUnmounted(() => {
    toggleScrollListener(false)
    document.body.classList.remove('nav-hidden')
})
</script>

<style scoped>
.sidebar {
    width: 100%;
    background: rgba(255, 249, 252, 0.78);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    padding: 0 24px;
    box-sizing: border-box;
    display: flex;
    align-items: center;
    height: 62px;
    position: sticky;
    top: 0;
    z-index: 100;
    border-bottom: 1px solid rgba(223, 156, 185, 0.22);
    justify-content: center;
    transition: margin-top 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-top: 0;
    transform: translateY(0);
    box-shadow: 0 10px 28px rgba(211, 143, 176, 0.12);
}

.sidebar.is-hidden {
    margin-top: -62px;
    transform: translateY(-100%);
}

.sidebar-hit-area {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 25px;
    z-index: 99;
}

.brand-mark {
    position: absolute;
    left: 24px;
    top: 50%;
    transform: translateY(-50%);
    font-weight: 800;
    font-size: 15px;
    letter-spacing: 0.02em;
    color: #a14d73;
}

.brand-mark::after {
    content: ' ✨';
}

.sidebar-actions {
    position: absolute;
    right: 24px;
    top: 50%;
    transform: translateY(-50%);
}

.sidebar-nav {
    display: flex;
    flex-direction: row;
    gap: 24px;
    align-items: center;
    margin-left: auto;
    margin-right: auto;
}

.sidebar-nav a {
    text-decoration: none;
    color: #8e6374;
    font-weight: 600;
    font-size: 14px;
    font-family: 'Inter', sans-serif;
    transition: color 0.2s ease, transform 0.18s ease;
}

.sidebar-nav a:hover {
    color: #b85f88;
    transform: translateY(-1px);
}

.sidebar-nav a.router-link-active,
.sidebar-nav a.active {
    background: linear-gradient(
      90deg,
      #e78fb3,
      #d39ef8,
      #ffb7d5
    );
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.settings-nav-btn {
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(223, 156, 185, 0.24);
  color: #9d5c79;
  cursor: pointer;
  padding: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s ease, background 0.2s ease;
}

.settings-nav-btn:hover {
  color: #c35a8b;
  background: rgba(255, 245, 249, 0.95);
}

@media (max-width: 900px) {
  .brand-mark {
    display: none;
  }

  .sidebar-nav {
    gap: 16px;
  }
}

@media (max-width: 720px) {
  .sidebar {
    justify-content: flex-start;
    padding-right: 68px;
  }

  .sidebar-nav {
    overflow-x: auto;
    width: 100%;
    justify-content: flex-start;
    margin-left: 0;
    margin-right: 0;
  }
}
</style>
