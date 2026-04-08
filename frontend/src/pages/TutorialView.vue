<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownIt from 'markdown-it'
import markdownItAnchor from 'markdown-it-anchor'

const route = useRoute()

const renderedContent = ref('')
const currentLang = ref('en')
const markdownBody = ref(null)
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})
md.use(markdownItAnchor, {
  permalink: markdownItAnchor.permalink.ariaHidden({
    placement: 'before',
    symbol: '#',
    space: true,
    class: 'header-anchor'
  }),
  slugify: s =>
    s
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fa5\s-]/g, '')
      .replace(/\s+/g, '-')
})

const getTutorialFile = () => (currentLang.value === 'en' ? '/tutorial-en.md' : '/tutorial-zh.md')

const scrollToHash = () => {
  nextTick(() => {
    if (route.hash) {
      const targetId = route.hash.slice(1)
      const targetElement = document.getElementById(targetId)
      if (targetElement) {
        setTimeout(() => {
          targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }, 100)
      }
    }
  })
}

const addCopyButtons = () => {
  nextTick(() => {
    const container = markdownBody.value
    if (!container) return
    const blocks = container.querySelectorAll('pre')
    blocks.forEach((block) => {
      if (block.querySelector('.copy-code-btn')) return
      const button = document.createElement('button')
      button.type = 'button'
      button.className = 'copy-code-btn'
      button.textContent = 'Copy'
      button.addEventListener('click', async () => {
        const code = block.querySelector('code')
        const text = code ? code.innerText : block.innerText
        try {
          await navigator.clipboard.writeText(text)
          button.textContent = 'Copied'
          setTimeout(() => {
            button.textContent = 'Copy'
          }, 1200)
        } catch (error) {
          console.error('Failed to copy code: ', error)
        }
      })
      block.classList.add('has-copy-button')
      block.appendChild(button)
    })
  })
}

const loadTutorial = async () => {
  try {
    const response = await fetch(getTutorialFile())
    if (response.ok) {
      let text = await response.text()
      text = text.replace(/\]\(media\//g, '](/media/')
      text = text.replace(/src="media\//g, 'src="/media/')
      renderedContent.value = md.render(text)
      addCopyButtons()
      scrollToHash()
    } else {
      console.error('Failed to fetch tutorial markdown')
    }
  } catch (error) {
    console.error('Failed to load tutorial:', error)
  }
}

const switchLang = (lang) => {
  if (currentLang.value !== lang) {
    currentLang.value = lang
    loadTutorial()
  }
}

onMounted(() => {
  loadTutorial()
})
</script>

<template>
  <div class="tutorial-view">
    <div class="tutorial-shell">
      <div class="tutorial-header">
        <div>
          <div class="eyebrow">🌸 Gentle Guide</div>
          <h1>MyLittleAgent Tutorial</h1>
          <p>Walk through the platform in a softer, calmer workspace.</p>
        </div>
        <div class="lang-switch">
          <button :class="{ active: currentLang === 'zh' }" @click="switchLang('zh')">中文</button>
          <button :class="{ active: currentLang === 'en' }" @click="switchLang('en')">English</button>
        </div>
      </div>
      <div ref="markdownBody" class="markdown-body" v-html="renderedContent"></div>
    </div>
  </div>
</template>

<style scoped>
.tutorial-view {
  padding: 26px;
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  min-height: calc(100vh - 62px);
  background: transparent;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  scroll-behavior: smooth;
}

.tutorial-shell {
  max-width: 1100px;
  margin: 0 auto;
}

.tutorial-header {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
  margin-bottom: 18px;
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 250, 252, 0.74);
  border: 1px solid rgba(223, 156, 185, 0.18);
  box-shadow: 0 18px 44px rgba(212, 142, 175, 0.14);
  backdrop-filter: blur(14px);
}

.eyebrow {
  color: #b25c82;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 10px;
}

.tutorial-header h1 {
  margin: 0 0 8px;
  font-size: 32px;
  color: #5b3041;
}

.tutorial-header p {
  margin: 0;
  color: #876473;
}

.lang-switch {
  z-index: 10;
  display: flex;
  gap: 12px;
}

.lang-switch button {
  background: linear-gradient(90deg, #fff8fb, #ffe8f3);
  color: #b05c81;
  border: 1px solid rgba(223, 156, 185, 0.25);
  border-radius: 999px;
  padding: 8px 16px;
  font-size: 0.95em;
  cursor: pointer;
  transition: all 0.2s ease;
}

.lang-switch button.active,
.lang-switch button:hover {
  background: linear-gradient(90deg, #ffd6e6, #f0d7ff, #ffc4de);
  color: #5e3346;
  box-shadow: 0 10px 20px rgba(220, 143, 175, 0.16);
}

:deep(.markdown-body) {
  max-width: 980px;
  margin: 0 auto;
  color: #5a3b47;
  font-family: 'Inter', 'Segoe UI', sans-serif;
  line-height: 1.75;
  background: rgba(255, 251, 253, 0.82);
  border-radius: 20px;
  box-shadow: 0 18px 44px rgba(212, 142, 175, 0.12);
  padding: 32px 36px;
  border: 1px solid rgba(223, 156, 185, 0.16);
  backdrop-filter: blur(10px);
}

:deep(.markdown-body h1),
:deep(.markdown-body h2),
:deep(.markdown-body h3),
:deep(.markdown-body h4),
:deep(.markdown-body h5),
:deep(.markdown-body h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 800;
  line-height: 1.25;
  color: #b35e84;
  scroll-margin-top: 20px;
}

:deep(.markdown-body h1:target),
:deep(.markdown-body h2:target),
:deep(.markdown-body h3:target),
:deep(.markdown-body h4:target),
:deep(.markdown-body h5:target),
:deep(.markdown-body h6:target) {
  background: rgba(255, 224, 236, 0.8);
  padding: 8px 12px;
  margin-left: -12px;
  margin-right: -12px;
  border-radius: 10px;
}

:deep(.markdown-body h1) { font-size: 2.2em; border-bottom: 1px solid rgba(223, 156, 185, 0.24); padding-bottom: 0.3em; }
:deep(.markdown-body h2) { font-size: 1.6em; border-bottom: 1px solid rgba(223, 156, 185, 0.16); padding-bottom: 0.3em; }
:deep(.markdown-body h3) { font-size: 1.3em; }

:deep(.markdown-body p) {
  margin-top: 0;
  margin-bottom: 16px;
  color: #6f4d5c;
  font-size: 1.05em;
}

:deep(.markdown-body a) {
  color: #c0618c;
  text-decoration: none;
  border-bottom: 1px dashed rgba(192, 97, 140, 0.5);
}

:deep(.markdown-body a:hover) {
  color: #9f456d;
  border-bottom: 1px solid rgba(159, 69, 109, 0.7);
}

:deep(.markdown-body img),
:deep(.markdown-body video) {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  border-radius: 14px;
  border: 1px solid rgba(223, 156, 185, 0.18);
  box-shadow: 0 12px 28px rgba(212, 142, 175, 0.12);
  margin: 16px 0;
}

:deep(.markdown-body code) {
  padding: 0.2em 0.5em;
  font-size: 90%;
  background: rgba(255, 237, 245, 0.8);
  border-radius: 8px;
  color: #b25c82;
  border: 1px solid rgba(223, 156, 185, 0.16);
}

:deep(.markdown-body pre) {
  padding: 18px 20px;
  overflow: auto;
  font-size: 95%;
  line-height: 1.55;
  background: rgba(255, 244, 249, 0.92);
  border-radius: 14px;
  margin-bottom: 18px;
  border: 1px solid rgba(223, 156, 185, 0.18);
  position: relative;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

:deep(.markdown-body pre code) {
  display: inline;
  padding: 0;
  margin: 0;
  background: transparent;
  border: 0;
  color: #8f4f6a;
}

:deep(.markdown-body pre.has-copy-button) {
  padding-top: 44px;
}

:deep(.markdown-body .copy-code-btn) {
  position: absolute;
  top: 10px;
  right: 10px;
  background: linear-gradient(90deg, #fff8fb, #ffe8f3);
  color: #b05c81;
  border: 1px solid rgba(223, 156, 185, 0.22);
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 0.85em;
  cursor: pointer;
}

:deep(.markdown-body blockquote) {
  padding: 0 1em;
  color: #8e6576;
  border-left: 0.25em solid rgba(223, 156, 185, 0.6);
  margin: 0 0 16px 0;
  background: rgba(255, 241, 246, 0.75);
  border-radius: 10px;
}

:deep(.markdown-body hr) {
  height: 0.25em;
  margin: 24px 0;
  background: linear-gradient(90deg, rgba(223, 156, 185, 0.35) 0%, rgba(255, 245, 249, 0) 100%);
  border: 0;
  border-radius: 999px;
}

:deep(.markdown-body table) {
  border-spacing: 0;
  border-collapse: collapse;
  margin-bottom: 16px;
  width: 100%;
  overflow: auto;
  background: rgba(255, 246, 250, 0.65);
  border-radius: 10px;
}

:deep(.markdown-body table th),
:deep(.markdown-body table td) {
  padding: 8px 15px;
  border: 1px solid rgba(223, 156, 185, 0.18);
}

:deep(.markdown-body table th) {
  font-weight: 700;
  background: rgba(255, 231, 240, 0.7);
  color: #b35e84;
}

@media (max-width: 900px) {
  .tutorial-header {
    flex-direction: column;
  }

  .lang-switch {
    width: 100%;
  }
}
</style>
