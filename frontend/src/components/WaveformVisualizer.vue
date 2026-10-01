<template>
  <canvas ref="canvas" class="visualizer" aria-label="Live audio waveform and frequency energy"></canvas>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  analyser: AnalyserNode | null
  active: boolean
}>()

const canvas = ref<HTMLCanvasElement | null>(null)
let frame: number | null = null
let resizeObserver: ResizeObserver | null = null

const resize = () => {
  const element = canvas.value
  if (!element) return
  const ratio = Math.min(window.devicePixelRatio || 1, 2)
  const rect = element.getBoundingClientRect()
  element.width = Math.max(1, Math.floor(rect.width * ratio))
  element.height = Math.max(1, Math.floor(rect.height * ratio))
  draw()
}

const drawIdle = (context: CanvasRenderingContext2D, width: number, height: number) => {
  context.fillStyle = '#171816'
  context.fillRect(0, 0, width, height)
  context.strokeStyle = '#30332e'
  context.lineWidth = 1
  for (let index = 1; index < 8; index += 1) {
    const x = (width / 8) * index
    context.beginPath()
    context.moveTo(x, 0)
    context.lineTo(x, height)
    context.stroke()
  }
  context.strokeStyle = '#4b5147'
  context.beginPath()
  context.moveTo(0, height / 2)
  context.lineTo(width, height / 2)
  context.stroke()
}

const draw = () => {
  const element = canvas.value
  if (!element) return
  const context = element.getContext('2d')
  if (!context) return
  const width = element.width
  const height = element.height
  drawIdle(context, width, height)

  if (props.active && props.analyser) {
    const timeData = new Uint8Array(props.analyser.fftSize)
    const frequencyData = new Uint8Array(props.analyser.frequencyBinCount)
    props.analyser.getByteTimeDomainData(timeData)
    props.analyser.getByteFrequencyData(frequencyData)

    const barCount = 56
    const barWidth = width / barCount
    for (let index = 0; index < barCount; index += 1) {
      const sourceIndex = Math.floor((index / barCount) * frequencyData.length * 0.38)
      const energy = (frequencyData[sourceIndex] ?? 0) / 255
      const barHeight = energy * height * 0.42
      context.fillStyle = index % 3 === 0 ? 'rgba(255, 107, 82, 0.42)' : 'rgba(255, 209, 84, 0.24)'
      context.fillRect(index * barWidth, height - barHeight, Math.max(1, barWidth - 2), barHeight)
    }

    context.strokeStyle = '#b9f35a'
    context.lineWidth = Math.max(2, width / 900)
    context.beginPath()
    const slice = width / (timeData.length - 1)
    for (let index = 0; index < timeData.length; index += 1) {
      const x = index * slice
      const y = ((timeData[index] ?? 128) / 255) * height
      if (index === 0) context.moveTo(x, y)
      else context.lineTo(x, y)
    }
    context.stroke()
  }

  if (props.active) frame = requestAnimationFrame(draw)
}

watch(
  () => props.active,
  () => {
    if (frame !== null) cancelAnimationFrame(frame)
    frame = null
    draw()
  },
)

onMounted(() => {
  resizeObserver = new ResizeObserver(resize)
  if (canvas.value) resizeObserver.observe(canvas.value)
  resize()
})

onBeforeUnmount(() => {
  if (frame !== null) cancelAnimationFrame(frame)
  resizeObserver?.disconnect()
})
</script>

<style scoped>
.visualizer {
  display: block;
  width: 100%;
  height: 100%;
  min-height: 148px;
}
</style>
