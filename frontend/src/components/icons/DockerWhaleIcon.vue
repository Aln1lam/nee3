<template>
  <!-- NSSCTF 极简线稿 Docker Moby：stroke 轮廓 + 微型集装箱 -->
  <svg
    class="docker-status-icon docker-whale-icon"
    :class="{ 'is-active': active }"
    viewBox="0 0 24 24"
    :width="size"
    :height="size"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
    focusable="false"
  >
    <!-- 集装箱微型方块 -->
    <path d="M4 10h2v2H4zM7 10h2v2H7zM10 10h2v2h-2zM13 10h2v2h-2zM7 7h2v2H7zM10 7h2v2h-2zM13 7h2v2h-2zM10 4h2v2h-2z" fill="currentColor" stroke="none" />
    <!-- 极简鲸鱼轮廓 -->
    <path d="M2 13.5C2 13.5 3.5 12.5 6 12.5C9 12.5 14 12.5 17 12.5C20 12.5 22 14 22 16.5C22 18.5 18 19.5 11 19.5C5 19.5 2 17 2 13.5Z" />
    <path d="M20 13c1.5-1.5 2.5-3 2.5-3.5 0 0-1.5 1-2.5 2" />
  </svg>
</template>

<script>
export default {
  name: 'DockerWhaleIcon',
  props: {
    size: {
      type: [Number, String],
      default: 20,
    },
    /** 有容器运行时为 true → Docker 经典蓝 + 蓝光呼吸 */
    active: {
      type: Boolean,
      default: false,
    },
  },
}
</script>

<style>
/* 非 scoped：避免 Vue scoped 干扰 SVG stroke/fill */
.docker-status-icon {
  display: block;
  flex-shrink: 0;
  overflow: visible;
  color: var(--muted);
  transition: color 0.3s ease, filter 0.3s ease, opacity 0.3s ease, transform 0.3s ease;
  cursor: pointer;
  vertical-align: middle;
}

.docker-status-icon:hover {
  color: var(--muted);
}

/* 核心交互：有容器运行 → Docker Blue */
.docker-status-icon.is-active {
  color: #2496ED !important;
  filter: drop-shadow(0 0 6px rgba(36, 150, 237, 0.6));
  animation: docker-pulse 2s infinite ease-in-out;
}

@keyframes docker-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
    filter: drop-shadow(0 0 6px rgba(36, 150, 237, 0.6));
  }
  50% {
    opacity: 0.85;
    transform: scale(1.04);
    filter: drop-shadow(0 0 10px rgba(36, 150, 237, 0.9));
  }
}

/* 非状态指示场景（题卡/标题）禁用呼吸动画，仅继承父级色 */
.docker-heading-ico.docker-status-icon,
.docker-icon .docker-status-icon {
  cursor: inherit;
  animation: none !important;
  filter: none !important;
  color: inherit;
}
.docker-heading-ico.docker-status-icon:hover,
.docker-icon .docker-status-icon:hover {
  color: inherit;
}
</style>
