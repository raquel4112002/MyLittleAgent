<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goToMonitor = () => {
  router.push('/observability')
}

const petals = Array.from({ length: 26 }, (_, i) => ({
  id: i,
  left: `${Math.random() * 100}%`,
  top: `${Math.random() * 100}%`,
  size: `${Math.random() * 22 + 10}px`,
  delay: `-${Math.random() * 18}s`,
  duration: `${Math.random() * 18 + 20}s`,
  rotate: `${Math.random() * 360}deg`,
  opacity: Math.random() * 0.4 + 0.25,
}))
</script>

<template>
  <div class="home-view">
    <div class="petals-layer">
      <div
        v-for="petal in petals"
        :key="petal.id"
        class="petal"
        :style="{
          left: petal.left,
          top: petal.top,
          width: petal.size,
          height: petal.size,
          animationDelay: petal.delay,
          animationDuration: petal.duration,
          opacity: petal.opacity,
          '--rotate': petal.rotate,
        }"
      />
    </div>

    <div class="content-wrapper">
      <div class="hero-badge">🌸 Soft Ops Mode</div>
      <h1 class="title">
        <span class="title-line">MyLittleAgent</span>
        <span class="title-line title-highlight">Cherry Bloom Console</span>
      </h1>

      <p class="introduction">
        A softer command center for multi-agent workflows — designed for visibility, collaboration,
        and gentle control while your agents work.
      </p>

      <div class="actions">
        <button class="btn primary-btn" @click="goToMonitor">
          Open Monitor ✨
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-view {
  width: 100%;
  min-height: calc(100vh - 62px);
  background:
    radial-gradient(circle at 18% 20%, rgba(255, 214, 230, 0.75), transparent 0 28%),
    radial-gradient(circle at 82% 18%, rgba(255, 235, 244, 0.72), transparent 0 30%),
    linear-gradient(180deg, #fff9fc 0%, #fff1f6 48%, #ffe8f1 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  box-sizing: border-box;
  font-family: 'Inter', sans-serif;
  position: relative;
  overflow: hidden;
}

.petals-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.petal {
  position: absolute;
  border-radius: 65% 35% 70% 30%;
  background: linear-gradient(180deg, rgba(255, 202, 222, 0.9), rgba(255, 168, 203, 0.6));
  box-shadow: 0 6px 14px rgba(230, 147, 185, 0.18);
  animation: drift 18s linear infinite;
  transform: rotate(var(--rotate));
}

@keyframes drift {
  0% {
    transform: translate3d(0, 0, 0) rotate(var(--rotate));
  }
  50% {
    transform: translate3d(-22px, 35px, 0) rotate(calc(var(--rotate) + 120deg));
  }
  100% {
    transform: translate3d(18px, 90px, 0) rotate(calc(var(--rotate) + 240deg));
  }
}

.content-wrapper {
  max-width: 900px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
  background: rgba(255, 250, 252, 0.72);
  border: 1px solid rgba(226, 162, 189, 0.26);
  border-radius: 30px;
  padding: 42px 34px;
  box-shadow: 0 26px 60px rgba(215, 143, 175, 0.18);
  backdrop-filter: blur(12px);
}

.hero-badge {
  margin-bottom: 18px;
  background: rgba(255, 239, 246, 0.95);
  border: 1px solid rgba(231, 143, 179, 0.28);
  color: #ae5a80;
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 700;
}

.title {
  font-size: 72px;
  font-weight: 900;
  line-height: 1.12;
  margin: 0 0 22px 0;
  letter-spacing: -1.5px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.title-line {
  color: #593444;
}

.title-highlight {
  background: linear-gradient(90deg, #e78fb3, #d39ef8, #ffb7d5);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.introduction {
  font-size: 21px;
  color: #7e5a68;
  line-height: 1.6;
  max-width: 720px;
  margin: 0 auto 34px;
}

.actions {
  display: flex;
  gap: 18px;
  justify-content: center;
}

.btn {
  border: none;
  padding: 14px 28px;
  font-size: 16px;
  font-weight: 700;
  border-radius: 999px;
  cursor: pointer;
}

.primary-btn {
  color: #5b2a3e;
  background: linear-gradient(90deg, #ffd6e6, #f0d7ff, #ffc4de);
  box-shadow: 0 16px 30px rgba(226, 150, 182, 0.22);
}

.primary-btn:hover {
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .title {
    font-size: 42px;
  }

  .introduction {
    font-size: 18px;
  }

  .content-wrapper {
    padding: 28px 22px;
  }
}
</style>
