<template>
  <Transition name="modal-fade">
    <div v-if="isVisible" class="modal-overlay" @click.self="close">
      <div class="modal-content settings-modal">
        <div class="modal-header">
          <div>
            <div class="eyebrow">🌸 Preferences</div>
            <h3>MyLittleAgent Settings</h3>
          </div>
          <button class="close-button" @click="close">×</button>
        </div>
        <div class="modal-body">
          <div class="settings-item">
            <label class="checkbox-label">
              <input type="checkbox" v-model="localConfig.AUTO_SHOW_ADVANCED">
              Auto show advanced setting
            </label>
            <p class="setting-desc">Automatically expand "Advanced Settings" in configuration forms.</p>
          </div>
          <div class="settings-item">
            <label class="checkbox-label">
              <input type="checkbox" v-model="localConfig.AUTO_EXPAND_MESSAGES">
              Automatically expand messages
            </label>
            <p class="setting-desc">Automatically expand message content in the chat view.</p>
          </div>
          <div class="settings-item">
            <label class="checkbox-label">
              <input type="checkbox" v-model="localConfig.ENABLE_HELP_TOOLTIPS">
              Enable help tooltips
            </label>
            <p class="setting-desc">Show contextual help tooltips throughout the workflow interface.</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-button" @click="close">Cancel</button>
          <button class="confirm-button" @click="save">Save</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { configStore } from '../utils/configStore.js'

const props = defineProps({
  isVisible: {
    type: Boolean,
    required: true
  }
})

const localConfig = reactive({
  AUTO_SHOW_ADVANCED: false,
  AUTO_EXPAND_MESSAGES: false,
  ENABLE_HELP_TOOLTIPS: true
})

watch(() => props.isVisible, (newVal) => {
  if (newVal) {
    Object.assign(localConfig, configStore)
  }
})

const emit = defineEmits(['update:isVisible', 'close'])

const close = () => {
  emit('update:isVisible', false)
  emit('close')
}

const save = () => {
  Object.assign(configStore, localConfig)
  close()
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 240, 246, 0.38);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.modal-content.settings-modal {
  width: 520px !important;
  max-width: 92vw;
  background: rgba(255, 250, 252, 0.92);
  border-radius: 22px;
  border: 1px solid rgba(223, 156, 185, 0.18);
  color: #5b3446;
  display: flex;
  flex-direction: column;
  box-shadow: 0 22px 44px rgba(212, 142, 175, 0.18);
  backdrop-filter: blur(14px);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 18px 22px;
  border-bottom: 1px solid rgba(223, 156, 185, 0.14);
}

.eyebrow {
  color: #b25c82;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #5b3041;
}

.close-button {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(223, 156, 185, 0.18);
  color: #a35b79;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 36px;
  height: 36px;
  line-height: 1;
  border-radius: 12px;
}

.close-button:hover {
  color: #c0608b;
  background: rgba(255, 245, 249, 0.95);
}

.modal-body {
  padding: 22px;
  flex: 1;
  overflow-y: auto;
}

.settings-item {
  margin-bottom: 18px;
  padding: 16px 18px;
  border: 1px solid rgba(223, 156, 185, 0.14);
  border-radius: 18px;
  background: rgba(255, 245, 249, 0.75);
}

.settings-item:last-child {
  margin-bottom: 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #5f3b4b;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  margin-bottom: 6px;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #d97ea6;
  cursor: pointer;
}

.setting-desc {
  margin-left: 26px;
  color: #8b6a78;
  font-size: 13px;
  line-height: 1.45;
  margin-top: 0;
}

.modal-footer {
  padding: 18px 22px;
  border-top: 1px solid rgba(223, 156, 185, 0.14);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.confirm-button {
  background: linear-gradient(90deg, #ffd6e6, #f0d7ff, #ffc4de);
  color: #6a2f47;
  border: none;
  padding: 10px 18px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
}

.confirm-button:hover {
  box-shadow: 0 12px 22px rgba(226, 150, 182, 0.2);
}

.cancel-button {
  background: rgba(255, 255, 255, 0.72);
  color: #8d6174;
  border: 1px solid rgba(223, 156, 185, 0.2);
  padding: 10px 18px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}

.cancel-button:hover {
  background: rgba(255, 245, 249, 0.95);
  color: #b05c81;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
