<template>
  <div class="studio-shell">
    <header class="app-bar">
      <div class="brand-block">
        <span class="brand-mark" aria-hidden="true">M</span>
        <div>
          <strong>MusicAgent</strong>
          <span>Browser studio</span>
        </div>
      </div>
      <div class="app-status" role="status">
        <span class="status-dot" :class="healthState"></span>
        <span>{{ statusText }}</span>
      </div>
      <div class="app-actions">
        <label class="button button-quiet file-button" title="Import a MIDI file">
          <span aria-hidden="true">↥</span>
          Import MIDI
          <input ref="midiInput" type="file" accept=".mid,.midi,audio/midi" @change="importMidi" />
        </label>
        <button class="icon-button" type="button" title="Refresh history" aria-label="Refresh history" @click="refreshHistory">↻</button>
      </div>
    </header>

    <main class="studio-grid">
      <aside class="brief-panel" aria-label="Generation controls">
        <div class="panel-heading">
          <h1>New session</h1>
          <span>{{ aiEnabled ? 'AI engine' : 'Local engine' }}</span>
        </div>

        <label class="field-label" for="music-brief">Music brief</label>
        <textarea
          id="music-brief"
          v-model="prompt"
          class="brief-input"
          rows="7"
          placeholder="A bright electronic track with a warm bass line, 124 BPM..."
          :disabled="isGenerating"
        ></textarea>
        <button class="button button-primary generate-button" type="button" :disabled="isGenerating || !prompt.trim()" @click="generate">
          <span aria-hidden="true">✦</span>
          {{ isGenerating ? 'Building arrangement' : 'Generate and audition' }}
        </button>

        <section class="inline-tool" :class="{ disabled: !composition }">
          <div class="tool-title">
            <h2>Refine</h2>
            <span>Uses the current arrangement</span>
          </div>
          <textarea v-model="feedback" rows="3" placeholder="Make the chorus faster and lift the lead..." :disabled="!composition || isGenerating"></textarea>
          <button class="button button-secondary" type="button" :disabled="!composition || !feedback.trim() || isGenerating" @click="refine">
            Apply feedback
          </button>
        </section>

        <section class="inline-tool" :class="{ disabled: !composition }">
          <div class="tool-title">
            <h2>Arrange</h2>
            <span>Shift the overall character</span>
          </div>
          <div class="style-options" aria-label="Arrangement styles">
            <button v-for="preset in stylePresets" :key="preset" type="button" :disabled="!composition || isGenerating" @click="arrange(preset)">
              {{ preset }}
            </button>
          </div>
          <div class="arrange-row">
            <input v-model="styleRequest" type="text" placeholder="Custom direction" :disabled="!composition || isGenerating" />
            <button class="icon-button" type="button" title="Apply custom arrangement" aria-label="Apply custom arrangement" :disabled="!composition || !styleRequest.trim() || isGenerating" @click="arrange(styleRequest)">→</button>
          </div>
        </section>

        <section class="history-block">
          <div class="tool-title">
            <h2>Sessions</h2>
            <span>{{ historyFiles.length }} saved</span>
          </div>
          <select v-model="selectedHistory" aria-label="Saved sessions" :disabled="isGenerating">
            <option value="">Select a saved session</option>
            <option v-for="file in historyFiles" :key="file.filename" :value="file.filename">{{ file.display_name }}</option>
          </select>
          <div class="history-actions">
            <button class="button button-quiet" type="button" :disabled="!selectedHistory || isGenerating" @click="loadHistory">Load</button>
            <button class="button button-danger" type="button" :disabled="!selectedHistory || isGenerating" @click="deleteHistory">Delete</button>
          </div>
        </section>
      </aside>

      <section ref="workspaceElement" class="workspace" aria-label="Composition workspace">
        <div class="visualizer-band">
          <div class="composition-meta">
            <div>
              <p>{{ composition ? 'Now editing' : 'Ready for an idea' }}</p>
              <h2>{{ composition?.title || 'Your arrangement will appear here' }}</h2>
            </div>
            <dl v-if="composition">
              <div><dt>BPM</dt><dd>{{ composition.tempo }}</dd></div>
              <div><dt>Tracks</dt><dd>{{ composition.tracks.length }}</dd></div>
              <div><dt>Length</dt><dd>{{ formatDuration(composition.duration_beats) }}</dd></div>
            </dl>
          </div>
          <div class="waveform-frame">
            <WaveformVisualizer :analyser="analyser" :active="isPlaying" />
            <div v-if="!composition" class="waveform-empty">Generate or import MIDI to start</div>
          </div>
        </div>

        <div class="transport" aria-label="Playback controls">
          <div class="transport-buttons">
            <button class="transport-button primary" type="button" :disabled="!composition" :title="isPlaying ? 'Pause' : 'Play'" :aria-label="isPlaying ? 'Pause' : 'Play'" @click="togglePlayback">
              {{ isPlaying ? 'Ⅱ' : '▶' }}
            </button>
            <button class="transport-button" type="button" title="Stop" aria-label="Stop" :disabled="!composition" @click="stopPlayback">■</button>
          </div>
          <span class="time-readout">{{ formatBeat(playheadBeat) }}</span>
          <input
            class="playhead-slider"
            type="range"
            min="0"
            :max="composition?.duration_beats || 1"
            step="0.01"
            :value="playheadBeat"
            aria-label="Playback position"
            :disabled="!composition"
            @input="seek"
          />
          <label class="master-control">
            <span>Master</span>
            <input v-model.number="masterGain" type="range" min="0" max="1" step="0.01" @input="updateMasterGain" />
          </label>
          <div class="export-actions">
            <button class="button button-quiet" type="button" :disabled="!composition" @click="exportJson">JSON</button>
            <button class="button button-quiet" type="button" :disabled="!composition" @click="exportMidi">MIDI</button>
            <button class="button button-accent" type="button" :disabled="!composition || isRendering" @click="exportWav">
              {{ isRendering ? 'Rendering' : 'WAV' }}
            </button>
          </div>
        </div>

        <div class="arrangement" :class="{ empty: !composition }">
          <div class="timeline-header">
            <div class="timeline-label">Arrangement</div>
            <div class="ruler" :style="timelineColumns">
              <span v-for="bar in barCount" :key="bar">{{ bar }}</span>
            </div>
          </div>
          <template v-if="composition">
            <div
              v-for="(track, trackIndex) in composition.tracks"
              :key="track.id"
              class="track-row"
              :class="{ selected: selectedTrackId === track.id, muted: track.muted }"
              @click="selectedTrackId = track.id"
            >
              <button class="track-label" type="button" @click.stop="selectedTrackId = track.id">
                <span class="track-color" :style="{ backgroundColor: trackColor(trackIndex) }"></span>
                <span><strong>{{ track.name }}</strong><small>{{ track.instrument }}</small></span>
              </button>
              <div class="note-lane" @dblclick="addNoteAtPointer($event, track.id)">
                <div class="bar-grid" :style="timelineColumns">
                  <span v-for="bar in barCount" :key="bar"></span>
                </div>
                <span
                  v-for="note in track.notes"
                  :key="note.id"
                  class="note-block"
                  :style="noteStyle(note, trackIndex)"
                  :title="`${noteName(note.pitch)} · ${note.duration} beats`"
                ></span>
                <span class="lane-playhead" :style="{ left: `${playheadPercent}%` }"></span>
              </div>
            </div>
          </template>
          <div v-else class="arrangement-empty">
            <strong>No arrangement yet</strong>
            <span>Your generated tracks and notes will stay synchronized with playback here.</span>
          </div>
        </div>

        <section v-if="selectedTrack" class="note-editor" aria-label="Selected track editor">
          <div class="editor-heading">
            <div>
              <span class="track-color" :style="{ backgroundColor: selectedTrackColor }"></span>
              <h2>{{ selectedTrack.name }}</h2>
              <span>{{ selectedTrack.notes.length }} notes</span>
            </div>
            <button class="button button-secondary" type="button" @click="addNote()">+ Add note</button>
          </div>
          <div class="note-table-wrap">
            <table class="note-table">
              <thead><tr><th>Pitch</th><th>Start</th><th>Length</th><th>Velocity</th><th><span class="sr-only">Actions</span></th></tr></thead>
              <tbody>
                <tr v-for="note in selectedTrack.notes" :key="note.id">
                  <td><input v-model.number="note.pitch" type="number" min="0" max="127" @change="normalizeComposition" /><span>{{ noteName(note.pitch) }}</span></td>
                  <td><input v-model.number="note.start" type="number" min="0" :max="composition?.duration_beats" step="0.25" @change="normalizeComposition" /></td>
                  <td><input v-model.number="note.duration" type="number" min="0.03125" max="32" step="0.25" @change="normalizeComposition" /></td>
                  <td><input v-model.number="note.velocity" type="number" min="1" max="127" @change="normalizeComposition" /></td>
                  <td><button class="icon-button danger" type="button" title="Delete note" aria-label="Delete note" @click="deleteNote(note.id)">×</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </section>

      <aside class="mixer-panel" aria-label="Mixer and track controls">
        <div class="panel-heading">
          <h2>Mixer</h2>
          <span>{{ composition?.tracks.length || 0 }} channels</span>
        </div>
        <template v-if="composition">
          <label class="compact-field">
            <span>Title</span>
            <input v-model="composition.title" type="text" maxlength="120" />
          </label>
          <label class="compact-field split-field">
            <span>Tempo</span>
            <input v-model.number="composition.tempo" type="number" min="30" max="240" @change="normalizeComposition" />
          </label>
          <div class="mixer-list">
            <section v-for="(track, index) in composition.tracks" :key="track.id" class="channel-strip" :class="{ selected: selectedTrackId === track.id }" @click="selectedTrackId = track.id">
              <div class="channel-title">
                <span class="track-color" :style="{ backgroundColor: trackColor(index) }"></span>
                <input v-model="track.name" type="text" aria-label="Track name" maxlength="80" />
                <button type="button" :class="{ active: track.muted }" :aria-pressed="track.muted" @click.stop="track.muted = !track.muted; restartIfPlaying()">M</button>
              </div>
              <label><span>Sound</span><select v-model="track.waveform" @change="restartIfPlaying"><option value="sine">Sine</option><option value="triangle">Triangle</option><option value="square">Square</option><option value="sawtooth">Saw</option></select></label>
              <label><span>Level</span><input v-model.number="track.gain" type="range" min="0" max="1" step="0.01" @input="restartIfPlaying" /></label>
              <label><span>Pan</span><input v-model.number="track.pan" type="range" min="-1" max="1" step="0.01" @input="restartIfPlaying" /></label>
            </section>
          </div>
        </template>
        <div v-else class="mixer-empty">Mixer controls become available with the first arrangement.</div>
      </aside>
    </main>

    <footer class="activity-bar">
      <button type="button" @click="showActivity = !showActivity">{{ showActivity ? 'Hide' : 'Show' }} activity</button>
      <span>{{ latestLog }}</span>
    </footer>
    <section v-if="showActivity" class="activity-drawer" aria-label="Activity log">
      <div v-for="(log, index) in logs" :key="`${index}-${log}`">{{ log }}</div>
      <div v-if="logs.length === 0">No activity yet.</div>
    </section>
    <div v-if="toast" class="toast" role="status">{{ toast }}</div>
  </div>
</template>

<script setup lang="ts">
import axios, { AxiosError } from 'axios'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { MusicPlaybackEngine, renderComposition } from '@/audio/MusicPlaybackEngine'
import { audioBufferToWav } from '@/audio/wav'
import WaveformVisualizer from '@/components/WaveformVisualizer.vue'
import type { Composition, HistoryFile, MusicNote, TaskStatus } from '@/types/music'

const API = '/api'
const TRACK_COLORS = ['#ff6b52', '#b9f35a', '#55d6df', '#ffd154', '#b79cff', '#ff8fbd', '#7ae582', '#62a8ff']
const stylePresets = ['Rock', 'Jazz', 'Electronic', 'Ambient']
const player = new MusicPlaybackEngine()

const prompt = ref('')
const feedback = ref('')
const styleRequest = ref('')
const composition = ref<Composition | null>(null)
const selectedTrackId = ref<string | null>(null)
const currentMidiFilename = ref<string | null>(null)
const currentCompositionFilename = ref<string | null>(null)
const currentTaskId = ref<string | null>(null)
const statusText = ref('Checking engine')
const healthState = ref<'online' | 'offline' | 'working'>('working')
const aiEnabled = ref(false)
const isGenerating = ref(false)
const isRendering = ref(false)
const isPlaying = ref(false)
const playheadBeat = ref(0)
const masterGain = ref(0.72)
const analyser = shallowRef<AnalyserNode | null>(null)
const logs = ref<string[]>([])
const showActivity = ref(false)
const toast = ref('')
const historyFiles = ref<HistoryFile[]>([])
const selectedHistory = ref('')
const midiInput = ref<HTMLInputElement | null>(null)
const workspaceElement = ref<HTMLElement | null>(null)
let pollTimer: number | null = null
let toastTimer: number | null = null

const selectedTrack = computed(() => composition.value?.tracks.find((track) => track.id === selectedTrackId.value) ?? null)
const selectedTrackIndex = computed(() => composition.value?.tracks.findIndex((track) => track.id === selectedTrackId.value) ?? -1)
const selectedTrackColor = computed(() => trackColor(Math.max(0, selectedTrackIndex.value)))
const barCount = computed(() => {
  if (!composition.value) return 8
  return Math.max(1, Math.ceil(composition.value.duration_beats / composition.value.time_signature[0]))
})
const timelineColumns = computed(() => ({ gridTemplateColumns: `repeat(${barCount.value}, minmax(72px, 1fr))` }))
const playheadPercent = computed(() => composition.value ? Math.min(100, (playheadBeat.value / composition.value.duration_beats) * 100) : 0)
const latestLog = computed(() => logs.value[logs.value.length - 1] || 'Ready')

const announce = (message: string) => {
  toast.value = message
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => (toast.value = ''), 2800)
}

const errorMessage = (error: unknown) => {
  if (error instanceof AxiosError) return String(error.response?.data?.error || error.message)
  return error instanceof Error ? error.message : 'Unknown error'
}

const checkHealth = async () => {
  try {
    const response = await axios.get<{ status: string; ai_enabled: boolean }>(`${API}/health`)
    aiEnabled.value = response.data.ai_enabled
    healthState.value = 'online'
    statusText.value = response.data.ai_enabled ? 'DeepSeek connected' : 'Local engine ready'
  } catch {
    healthState.value = 'offline'
    statusText.value = 'Backend unavailable'
  }
}

const startTask = async (request: Promise<{ data: { task_id: string } }>) => {
  stopPlayback()
  isGenerating.value = true
  healthState.value = 'working'
  try {
    const response = await request
    currentTaskId.value = response.data.task_id
    await pollTask(response.data.task_id)
  } catch (error) {
    finishWithError(errorMessage(error))
  }
}

const pollTask = async (taskId: string, failures = 0): Promise<void> => {
  if (currentTaskId.value !== taskId) return
  try {
    const { data } = await axios.get<TaskStatus>(`${API}/task/${encodeURIComponent(taskId)}`)
    logs.value = data.logs ?? []
    statusText.value = data.progress || 'Working'
    if (data.status === 'completed' && data.result_composition) {
      composition.value = data.result_composition
      selectedTrackId.value = data.result_composition.tracks[0]?.id ?? null
      currentMidiFilename.value = data.midi_filename
      currentCompositionFilename.value = data.composition_filename
      isGenerating.value = false
      healthState.value = 'online'
      currentTaskId.value = null
      playheadBeat.value = 0
      await refreshHistory()
      announce('Arrangement ready to play')
      await nextTick()
      if (window.matchMedia('(max-width: 780px)').matches) {
        workspaceElement.value?.scrollIntoView({ behavior: 'auto', block: 'start' })
      }
      try {
        await player.play(data.result_composition, 0)
        analyser.value = player.analyser
        isPlaying.value = true
      } catch {
        logs.value.push('Automatic audition was blocked by the browser. Press Play to listen.')
      }
      return
    }
    if (data.status === 'error') {
      finishWithError(data.error_message || 'Generation failed')
      return
    }
    pollTimer = window.setTimeout(() => void pollTask(taskId), 700)
  } catch (error) {
    if (failures < 3) {
      pollTimer = window.setTimeout(() => void pollTask(taskId, failures + 1), 900 * (failures + 1))
    } else {
      finishWithError(`Task connection lost: ${errorMessage(error)}`)
    }
  }
}

const finishWithError = (message: string) => {
  isGenerating.value = false
  healthState.value = 'offline'
  statusText.value = message
  logs.value.push(message)
  currentTaskId.value = null
  announce(message)
}

const generate = () => startTask(axios.post(`${API}/generate`, { prompt: prompt.value }))
const refine = () => {
  if (!composition.value) return
  const request = axios.post(`${API}/generate`, {
    prompt: prompt.value,
    feedback: feedback.value,
    previous_composition: composition.value,
  })
  feedback.value = ''
  return startTask(request)
}
const arrange = (direction: string) => {
  if (!composition.value || !direction.trim()) return
  styleRequest.value = ''
  return startTask(axios.post(`${API}/arrange`, { composition: composition.value, style_request: direction }))
}

const importMidi = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  const formData = new FormData()
  formData.append('midi_file', file)
  await startTask(axios.post(`${API}/import-midi`, formData))
  target.value = ''
}

const refreshHistory = async () => {
  try {
    const { data } = await axios.get<{ files: HistoryFile[] }>(`${API}/history`)
    historyFiles.value = data.files
  } catch (error) {
    logs.value.push(`History unavailable: ${errorMessage(error)}`)
  }
}

const loadHistory = async () => {
  if (!selectedHistory.value) return
  try {
    stopPlayback()
    const { data } = await axios.get<{ filename: string; composition: Composition }>(`${API}/history/${encodeURIComponent(selectedHistory.value)}`)
    composition.value = data.composition
    currentCompositionFilename.value = data.filename
    currentMidiFilename.value = data.filename.replace(/\.json$/i, '.mid')
    selectedTrackId.value = data.composition.tracks[0]?.id ?? null
    playheadBeat.value = 0
    announce('Saved session loaded')
  } catch (error) {
    finishWithError(errorMessage(error))
  }
}

const deleteHistory = async () => {
  if (!selectedHistory.value) return
  if (!window.confirm(`Delete ${selectedHistory.value}?`)) return
  try {
    await axios.delete(`${API}/history/${encodeURIComponent(selectedHistory.value)}`)
    selectedHistory.value = ''
    await refreshHistory()
    announce('Session deleted')
  } catch (error) {
    finishWithError(errorMessage(error))
  }
}

player.setCallbacks({
  onPosition: (beat) => (playheadBeat.value = beat),
  onEnded: () => {
    isPlaying.value = false
    playheadBeat.value = 0
  },
})

const togglePlayback = async () => {
  if (!composition.value) return
  if (isPlaying.value) {
    playheadBeat.value = player.pause()
    isPlaying.value = false
    return
  }
  await player.play(composition.value, playheadBeat.value)
  analyser.value = player.analyser
  isPlaying.value = true
}

const stopPlayback = () => {
  player.stop()
  isPlaying.value = false
  playheadBeat.value = 0
}

const seek = async (event: Event) => {
  playheadBeat.value = Number((event.target as HTMLInputElement).value)
  if (isPlaying.value && composition.value) {
    await player.play(composition.value, playheadBeat.value)
    analyser.value = player.analyser
  }
}

const updateMasterGain = () => player.setMasterGain(masterGain.value)
const restartIfPlaying = async () => {
  if (isPlaying.value && composition.value) {
    await player.play(composition.value, playheadBeat.value)
    analyser.value = player.analyser
  }
}

const normalizeComposition = () => {
  if (!composition.value) return
  composition.value.tempo = Math.max(30, Math.min(240, Number(composition.value.tempo) || 120))
  for (const track of composition.value.tracks) {
    track.gain = Math.max(0, Math.min(1, Number(track.gain) || 0))
    track.pan = Math.max(-1, Math.min(1, Number(track.pan) || 0))
    for (const note of track.notes) {
      note.pitch = Math.max(0, Math.min(127, Math.round(Number(note.pitch) || 60)))
      note.start = Math.max(0, Math.min(composition.value.duration_beats, Number(note.start) || 0))
      note.duration = Math.max(0.03125, Math.min(32, Number(note.duration) || 0.5))
      note.velocity = Math.max(1, Math.min(127, Math.round(Number(note.velocity) || 80)))
    }
    track.notes.sort((a, b) => a.start - b.start || a.pitch - b.pitch)
  }
  void restartIfPlaying()
}

const addNote = (start = 0) => {
  if (!selectedTrack.value || !composition.value) return
  selectedTrack.value.notes.push({ id: crypto.randomUUID(), pitch: 60, start, duration: 1, velocity: 88 })
  normalizeComposition()
}
const addNoteAtPointer = (event: MouseEvent, trackId: string) => {
  selectedTrackId.value = trackId
  const element = event.currentTarget as HTMLElement
  const ratio = (event.clientX - element.getBoundingClientRect().left) / element.getBoundingClientRect().width
  const start = Math.round((ratio * (composition.value?.duration_beats || 0)) * 4) / 4
  void nextTick(() => addNote(start))
}
const deleteNote = (noteId: string) => {
  if (!selectedTrack.value) return
  selectedTrack.value.notes = selectedTrack.value.notes.filter((note) => note.id !== noteId)
  void restartIfPlaying()
}

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}
const safeFilename = () => (composition.value?.title || 'composition').replace(/[^\p{L}\p{N}_-]+/gu, '-').replace(/^-|-$/g, '') || 'composition'
const exportJson = () => {
  if (!composition.value) return
  downloadBlob(new Blob([JSON.stringify(composition.value, null, 2)], { type: 'application/json' }), `${safeFilename()}.json`)
}
const exportMidi = async () => {
  if (!composition.value) return
  try {
    const response = await axios.post(`${API}/export-midi`, { composition: composition.value }, { responseType: 'blob' })
    downloadBlob(response.data, `${safeFilename()}.mid`)
  } catch (error) {
    finishWithError(errorMessage(error))
  }
}
const exportWav = async () => {
  if (!composition.value) return
  isRendering.value = true
  try {
    const buffer = await renderComposition(composition.value)
    downloadBlob(audioBufferToWav(buffer), `${safeFilename()}.wav`)
    announce('WAV export ready')
  } catch (error) {
    finishWithError(errorMessage(error))
  } finally {
    isRendering.value = false
  }
}

const trackColor = (index: number) => TRACK_COLORS[index % TRACK_COLORS.length] ?? TRACK_COLORS[0]
const noteStyle = (note: MusicNote, trackIndex: number) => ({
  left: `${(note.start / (composition.value?.duration_beats || 1)) * 100}%`,
  width: `${Math.max(0.25, (note.duration / (composition.value?.duration_beats || 1)) * 100)}%`,
  backgroundColor: trackColor(trackIndex),
  bottom: `${8 + ((note.pitch % 12) / 11) * 48}%`,
  opacity: `${0.55 + (note.velocity / 127) * 0.45}`,
})
const noteName = (pitch: number) => {
  const names = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B']
  return `${names[((pitch % 12) + 12) % 12]}${Math.floor(pitch / 12) - 1}`
}
const formatDuration = (beats: number) => {
  const seconds = beats * (60 / (composition.value?.tempo || 120))
  return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`
}
const formatBeat = (beat: number) => {
  const beatsPerBar = composition.value?.time_signature[0] || 4
  return `${Math.floor(beat / beatsPerBar) + 1}.${Math.floor(beat % beatsPerBar) + 1}.${Math.floor((beat % 1) * 4) + 1}`
}

onMounted(() => {
  void checkHealth()
  void refreshHistory()
})
onBeforeUnmount(() => {
  if (pollTimer !== null) window.clearTimeout(pollTimer)
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  player.dispose()
})
</script>

<style scoped>
:global(:root) {
  --bg: #10110f;
  --surface: #181a17;
  --surface-raised: #21231f;
  --surface-soft: #292c27;
  --line: #3b3f38;
  --line-strong: #555b50;
  --text: #f4f6ef;
  --text-muted: #adb4a6;
  --lime: #b9f35a;
  --lime-ink: #172000;
  --coral: #ff6b52;
  --yellow: #ffd154;
  --danger: #ff776f;
  --focus: #8fd7ff;
}

:global(body) { overflow: hidden; background: var(--bg); color: var(--text); }
:global(button), :global(input), :global(textarea), :global(select) { font: inherit; }
:global(button:focus-visible), :global(input:focus-visible), :global(textarea:focus-visible), :global(select:focus-visible) { outline: 2px solid var(--focus); outline-offset: 2px; }
.studio-shell { min-height: 100vh; background: var(--bg); color: var(--text); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.app-bar { height: 58px; display: flex; align-items: center; gap: 24px; padding: 0 18px; border-bottom: 1px solid var(--line); background: #151613; }
.brand-block { display: flex; align-items: center; gap: 10px; min-width: 248px; }
.brand-mark { display: grid; place-items: center; width: 32px; height: 32px; border-radius: 6px; background: var(--lime); color: var(--lime-ink); font-weight: 900; }
.brand-block div { display: flex; flex-direction: column; line-height: 1.15; }
.brand-block strong { font-size: 14px; }
.brand-block span:last-child { margin-top: 3px; color: var(--text-muted); font-size: 11px; }
.app-status { display: flex; align-items: center; gap: 8px; min-width: 0; color: var(--text-muted); font-size: 12px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--line-strong); }
.status-dot.online { background: var(--lime); }.status-dot.offline { background: var(--danger); }.status-dot.working { background: var(--yellow); }
.app-actions { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.studio-grid { height: calc(100vh - 86px); display: grid; grid-template-columns: 280px minmax(580px, 1fr) 250px; overflow: hidden; }
.brief-panel, .mixer-panel { min-width: 0; overflow-y: auto; background: var(--surface); }
.brief-panel { border-right: 1px solid var(--line); padding: 16px; }
.mixer-panel { border-left: 1px solid var(--line); padding: 16px 12px; }
.panel-heading, .tool-title, .editor-heading, .channel-title, .composition-meta, .transport, .history-actions, .arrange-row { display: flex; align-items: center; }
.panel-heading { justify-content: space-between; margin-bottom: 14px; }
.panel-heading h1, .panel-heading h2 { font-size: 15px; font-weight: 700; }.panel-heading span, .tool-title span { color: var(--text-muted); font-size: 11px; }
.field-label { display: block; margin-bottom: 7px; color: var(--text-muted); font-size: 11px; font-weight: 650; }
.brief-input, .inline-tool textarea, .arrange-row input, .history-block select, .compact-field input, .channel-strip input, .channel-strip select { width: 100%; border: 1px solid var(--line); border-radius: 5px; background: #121310; color: var(--text); }
.brief-input, .inline-tool textarea { resize: vertical; min-height: 72px; padding: 10px; line-height: 1.45; }
::placeholder { color: #858d7e; opacity: 1; }
.button, .icon-button, .transport-button, .style-options button, .channel-title button { border: 1px solid transparent; border-radius: 5px; cursor: pointer; transition: background-color 160ms ease, border-color 160ms ease, color 160ms ease; }
.button { min-height: 34px; display: inline-flex; align-items: center; justify-content: center; gap: 7px; padding: 0 11px; font-size: 12px; font-weight: 700; }
.button-primary { background: var(--lime); color: var(--lime-ink); }.button-primary:hover { background: #cbff78; }
.button-secondary { border-color: var(--line-strong); background: var(--surface-soft); color: var(--text); }.button-secondary:hover, .button-quiet:hover { border-color: #78816f; background: #30342e; }
.button-quiet { border-color: var(--line); background: transparent; color: var(--text); }.button-accent { background: var(--coral); color: #1e0905; }.button-danger { border-color: #81473f; background: transparent; color: #ff9d91; }
.button:disabled, .icon-button:disabled, .transport-button:disabled, .style-options button:disabled { cursor: not-allowed; opacity: 0.42; }
.generate-button { width: 100%; margin-top: 9px; }
.file-button { position: relative; overflow: hidden; }.file-button input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.icon-button { width: 32px; height: 32px; display: inline-grid; place-items: center; border-color: var(--line); background: transparent; color: var(--text); font-weight: 800; }.icon-button:hover { background: var(--surface-soft); }.icon-button.danger { color: var(--danger); }
.inline-tool, .history-block { margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--line); }.inline-tool.disabled { opacity: 0.6; }
.tool-title { justify-content: space-between; margin-bottom: 9px; }.tool-title h2 { font-size: 12px; font-weight: 750; }
.inline-tool .button { width: 100%; margin-top: 7px; }
.style-options { display: flex; flex-wrap: wrap; gap: 5px; }.style-options button { min-height: 29px; padding: 0 8px; border-color: var(--line); background: #121310; color: var(--text-muted); font-size: 11px; }.style-options button:hover { border-color: var(--coral); color: var(--text); }
.arrange-row { gap: 6px; margin-top: 7px; }.arrange-row input { min-height: 32px; padding: 0 8px; }
.history-block select { min-height: 34px; padding: 0 8px; }.history-actions { gap: 7px; margin-top: 7px; }.history-actions .button { flex: 1; }
.workspace { min-width: 0; overflow: auto; background: #11120f; }
.visualizer-band { min-height: 226px; border-bottom: 1px solid var(--line); background: #171816; }
.composition-meta { min-height: 70px; justify-content: space-between; gap: 16px; padding: 12px 18px; }.composition-meta p { color: var(--lime); font-size: 10px; font-weight: 750; }.composition-meta h2 { margin-top: 4px; font-size: 17px; font-weight: 750; text-wrap: balance; }.composition-meta dl { display: flex; gap: 22px; }.composition-meta dl div { display: flex; flex-direction: column; }.composition-meta dt { color: var(--text-muted); font-size: 9px; }.composition-meta dd { margin-top: 2px; font-size: 14px; font-weight: 750; }
.waveform-frame { position: relative; height: 156px; overflow: hidden; border-top: 1px solid #292c27; }.waveform-empty { position: absolute; inset: 0; display: grid; place-items: center; color: var(--text-muted); font-size: 12px; pointer-events: none; }
.transport { position: sticky; top: 0; z-index: 20; min-height: 54px; gap: 12px; padding: 8px 14px; border-bottom: 1px solid var(--line); background: #20221e; }
.transport-buttons { display: flex; gap: 5px; }.transport-button { width: 34px; height: 34px; border-color: var(--line-strong); background: #131411; color: var(--text); }.transport-button.primary { border-color: var(--lime); color: var(--lime); }
.time-readout { min-width: 48px; font-variant-numeric: tabular-nums; color: var(--text-muted); font-size: 11px; }.playhead-slider { flex: 1; min-width: 80px; accent-color: var(--lime); }.master-control { display: flex; align-items: center; gap: 7px; color: var(--text-muted); font-size: 10px; }.master-control input { width: 70px; accent-color: var(--coral); }
.export-actions { display: flex; gap: 5px; margin-left: auto; }.export-actions .button { min-height: 30px; padding: 0 9px; }
.arrangement { min-width: 680px; border-bottom: 1px solid var(--line); }.timeline-header, .track-row { display: grid; grid-template-columns: 150px minmax(530px, 1fr); }.timeline-header { height: 32px; border-bottom: 1px solid var(--line); background: #181a17; }.timeline-label { display: flex; align-items: center; padding: 0 12px; border-right: 1px solid var(--line); color: var(--text-muted); font-size: 10px; }.ruler, .bar-grid { display: grid; }.ruler span { padding: 7px 0 0 8px; border-right: 1px solid var(--line); color: #81897b; font-size: 9px; }
.track-row { min-height: 70px; border-bottom: 1px solid #2b2e29; }.track-row.selected { background: #1e211c; }.track-row.muted { opacity: 0.48; }
.track-label { display: flex; align-items: center; gap: 9px; padding: 0 11px; border: 0; border-right: 1px solid var(--line); background: transparent; color: var(--text); text-align: left; cursor: pointer; }.track-label span:last-child { display: flex; flex-direction: column; min-width: 0; }.track-label strong, .track-label small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.track-label strong { font-size: 11px; }.track-label small { margin-top: 3px; color: var(--text-muted); font-size: 9px; }.track-color { flex: 0 0 auto; width: 8px; height: 20px; border-radius: 2px; }
.note-lane { position: relative; min-width: 0; overflow: hidden; cursor: crosshair; }.bar-grid { position: absolute; inset: 0; }.bar-grid span { border-right: 1px solid #30332e; }.note-block { position: absolute; height: 8px; min-width: 2px; border-radius: 2px; }.lane-playhead { position: absolute; top: 0; bottom: 0; width: 1px; background: var(--lime); pointer-events: none; }
.arrangement-empty { min-height: 240px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 7px; color: var(--text-muted); }.arrangement-empty strong { color: var(--text); font-size: 13px; }.arrangement-empty span { max-width: 380px; text-align: center; font-size: 11px; }
.note-editor { min-width: 680px; padding: 14px 16px 28px; }.editor-heading { justify-content: space-between; margin-bottom: 11px; }.editor-heading > div { display: flex; align-items: center; gap: 8px; }.editor-heading h2 { font-size: 13px; }.editor-heading span:last-child { color: var(--text-muted); font-size: 10px; }
.note-table-wrap { max-height: 260px; overflow: auto; border: 1px solid var(--line); border-radius: 5px; }.note-table { width: 100%; border-collapse: collapse; font-size: 10px; }.note-table th { position: sticky; top: 0; z-index: 2; padding: 7px 9px; background: #242721; color: var(--text-muted); text-align: left; }.note-table td { height: 36px; padding: 4px 8px; border-top: 1px solid #30332e; }.note-table td:first-child { display: flex; align-items: center; gap: 7px; }.note-table input { width: 74px; min-height: 27px; padding: 0 6px; border: 1px solid var(--line); border-radius: 4px; background: #151613; color: var(--text); }
.compact-field { display: grid; grid-template-columns: 52px 1fr; align-items: center; gap: 6px; margin-bottom: 8px; color: var(--text-muted); font-size: 10px; }.compact-field input { min-height: 30px; padding: 0 7px; }.split-field input { width: 76px; }
.mixer-list { margin-top: 14px; }.channel-strip { padding: 11px 0; border-top: 1px solid var(--line); }.channel-strip.selected { background: #20231d; }.channel-title { gap: 6px; padding: 0 4px; }.channel-title input { min-width: 0; padding: 5px 6px; border-color: transparent; background: transparent; font-weight: 700; }.channel-title button { width: 26px; height: 25px; background: #121310; border-color: var(--line); color: var(--text-muted); }.channel-title button.active { border-color: var(--coral); background: var(--coral); color: #1c0704; }
.channel-strip label { display: grid; grid-template-columns: 42px 1fr; align-items: center; gap: 5px; margin-top: 7px; padding: 0 4px; color: var(--text-muted); font-size: 9px; }.channel-strip select { min-height: 27px; padding: 0 5px; }.channel-strip input[type='range'] { accent-color: var(--lime); }.mixer-empty { padding: 32px 8px; color: var(--text-muted); font-size: 11px; line-height: 1.5; }
.activity-bar { height: 28px; display: flex; align-items: center; gap: 14px; padding: 0 14px; border-top: 1px solid var(--line); background: #171816; color: var(--text-muted); font-size: 10px; }.activity-bar button { border: 0; background: transparent; color: var(--lime); cursor: pointer; }.activity-bar span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.activity-drawer { position: fixed; z-index: 40; right: 12px; bottom: 36px; width: min(520px, calc(100vw - 24px)); max-height: 260px; overflow: auto; padding: 12px; border: 1px solid var(--line-strong); border-radius: 6px; background: #11120f; color: #c8cec2; font: 11px/1.55 ui-monospace, SFMono-Regular, Consolas, monospace; }.activity-drawer div + div { margin-top: 5px; }
.toast { position: fixed; z-index: 60; right: 16px; top: 70px; max-width: 340px; padding: 10px 13px; border-radius: 5px; background: var(--lime); color: var(--lime-ink); font-size: 12px; font-weight: 750; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }

@media (max-width: 1120px) {
  .studio-grid { grid-template-columns: 250px minmax(540px, 1fr); }.mixer-panel { display: none; }.brand-block { min-width: 210px; }
}
@media (max-width: 780px) {
  :global(body) { overflow: auto; }
  .app-bar { height: auto; min-height: 58px; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px 12px; padding: 10px 12px; }
  .brand-block { min-width: 0; }
  .app-actions { margin-left: 0; }
  .app-status { grid-column: 1 / -1; width: 100%; }
  .studio-grid { height: auto; min-height: calc(100vh - 112px); display: block; overflow: visible; }
  .brief-panel { max-height: none; border-right: 0; border-bottom: 1px solid var(--line); }
  .workspace { overflow-x: auto; }
  .visualizer-band { min-width: 0; }
  .composition-meta { min-height: 82px; align-items: flex-start; flex-direction: column; gap: 8px; }
  .composition-meta dl { gap: 18px; }
  .transport { left: 0; min-width: 0; flex-wrap: wrap; }
  .playhead-slider { flex-basis: 120px; }
  .export-actions { margin-left: 0; }
  .activity-bar { position: sticky; bottom: 0; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; }
}
</style>
