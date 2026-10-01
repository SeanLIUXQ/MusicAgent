import type { Composition, MusicNote, MusicTrack, Waveform } from '@/types/music'

export interface PlaybackCallbacks {
  onPosition?: (beat: number) => void
  onEnded?: () => void
}

interface ActiveVoice {
  oscillator: OscillatorNode
  gain: GainNode
}

const midiToFrequency = (pitch: number) => 440 * Math.pow(2, (pitch - 69) / 12)

export class MusicPlaybackEngine {
  private context: AudioContext | null = null
  private master: GainNode | null = null
  private analyserNode: AnalyserNode | null = null
  private activeVoices: ActiveVoice[] = []
  private animationFrame: number | null = null
  private startedAt = 0
  private startBeat = 0
  private composition: Composition | null = null
  private callbacks: PlaybackCallbacks = {}
  private playing = false

  get analyser(): AnalyserNode | null {
    return this.analyserNode
  }

  get isPlaying(): boolean {
    return this.playing
  }

  setCallbacks(callbacks: PlaybackCallbacks): void {
    this.callbacks = callbacks
  }

  private ensureContext(): AudioContext {
    if (!this.context) {
      this.context = new AudioContext()
      this.master = this.context.createGain()
      this.master.gain.value = 0.72
      this.analyserNode = this.context.createAnalyser()
      this.analyserNode.fftSize = 2048
      this.analyserNode.smoothingTimeConstant = 0.78
      this.master.connect(this.analyserNode)
      this.analyserNode.connect(this.context.destination)
    }
    return this.context
  }

  async play(composition: Composition, fromBeat = 0): Promise<void> {
    this.stop(false)
    const context = this.ensureContext()
    if (context.state === 'suspended') await context.resume()
    this.composition = composition
    this.startBeat = Math.max(0, Math.min(fromBeat, composition.duration_beats))
    this.startedAt = context.currentTime + 0.04
    this.playing = true

    for (const track of composition.tracks) {
      if (track.muted || track.gain <= 0) continue
      const trackGain = context.createGain()
      const panner = context.createStereoPanner()
      trackGain.gain.value = track.gain
      panner.pan.value = track.pan
      trackGain.connect(panner)
      panner.connect(this.master!)
      for (const note of track.notes) this.scheduleNote(context, composition, track, note, trackGain)
    }
    this.tick()
  }

  pause(): number {
    const beat = this.currentBeat()
    this.stop(false)
    this.callbacks.onPosition?.(beat)
    return beat
  }

  stop(reset = true): void {
    for (const voice of this.activeVoices) {
      try {
        voice.oscillator.stop()
      } catch {
        // Voice may already have ended.
      }
      voice.oscillator.disconnect()
      voice.gain.disconnect()
    }
    this.activeVoices = []
    this.playing = false
    if (this.animationFrame !== null) cancelAnimationFrame(this.animationFrame)
    this.animationFrame = null
    if (reset) this.callbacks.onPosition?.(0)
  }

  setMasterGain(value: number): void {
    if (this.master && this.context) {
      this.master.gain.setTargetAtTime(Math.max(0, Math.min(value, 1)), this.context.currentTime, 0.015)
    }
  }

  dispose(): void {
    this.stop()
    void this.context?.close()
    this.context = null
    this.master = null
    this.analyserNode = null
  }

  private secondsPerBeat(composition: Composition): number {
    return 60 / composition.tempo
  }

  private scheduleNote(
    context: AudioContext,
    composition: Composition,
    track: MusicTrack,
    note: MusicNote,
    destination: AudioNode,
  ): void {
    const noteEnd = note.start + note.duration
    if (noteEnd <= this.startBeat) return
    const secondsPerBeat = this.secondsPerBeat(composition)
    const offsetBeats = Math.max(note.start, this.startBeat) - this.startBeat
    const remainingBeats = noteEnd - Math.max(note.start, this.startBeat)
    const startsAt = this.startedAt + offsetBeats * secondsPerBeat
    const endsAt = startsAt + remainingBeats * secondsPerBeat
    const oscillator = context.createOscillator()
    const envelope = context.createGain()
    oscillator.type = track.waveform
    oscillator.frequency.value = midiToFrequency(note.pitch)
    const peak = (note.velocity / 127) * 0.24
    envelope.gain.setValueAtTime(0.0001, startsAt)
    envelope.gain.exponentialRampToValueAtTime(Math.max(peak, 0.001), startsAt + 0.012)
    envelope.gain.setValueAtTime(Math.max(peak * 0.72, 0.001), Math.max(startsAt + 0.02, endsAt - 0.06))
    envelope.gain.exponentialRampToValueAtTime(0.0001, endsAt)
    oscillator.connect(envelope)
    envelope.connect(destination)
    oscillator.start(startsAt)
    oscillator.stop(endsAt + 0.01)
    const voice = { oscillator, gain: envelope }
    this.activeVoices.push(voice)
    oscillator.addEventListener('ended', () => {
      this.activeVoices = this.activeVoices.filter((active) => active !== voice)
    })
  }

  private currentBeat(): number {
    if (!this.context || !this.composition || !this.playing) return this.startBeat
    return Math.min(
      this.composition.duration_beats,
      this.startBeat + (this.context.currentTime - this.startedAt) / this.secondsPerBeat(this.composition),
    )
  }

  private tick = (): void => {
    if (!this.playing || !this.composition) return
    const beat = this.currentBeat()
    this.callbacks.onPosition?.(beat)
    if (beat >= this.composition.duration_beats) {
      this.stop(false)
      this.callbacks.onEnded?.()
      return
    }
    this.animationFrame = requestAnimationFrame(this.tick)
  }
}

const scheduleOfflineNote = (
  context: OfflineAudioContext,
  destination: AudioNode,
  waveform: Waveform,
  pitch: number,
  velocity: number,
  startsAt: number,
  endsAt: number,
): void => {
  const oscillator = context.createOscillator()
  const envelope = context.createGain()
  oscillator.type = waveform
  oscillator.frequency.value = midiToFrequency(pitch)
  const peak = (velocity / 127) * 0.24
  envelope.gain.setValueAtTime(0.0001, startsAt)
  envelope.gain.exponentialRampToValueAtTime(Math.max(peak, 0.001), startsAt + 0.012)
  envelope.gain.setValueAtTime(Math.max(peak * 0.72, 0.001), Math.max(startsAt + 0.02, endsAt - 0.06))
  envelope.gain.exponentialRampToValueAtTime(0.0001, endsAt)
  oscillator.connect(envelope)
  envelope.connect(destination)
  oscillator.start(startsAt)
  oscillator.stop(endsAt + 0.01)
}

export const renderComposition = async (composition: Composition): Promise<AudioBuffer> => {
  const sampleRate = 44_100
  const secondsPerBeat = 60 / composition.tempo
  const duration = composition.duration_beats * secondsPerBeat + 0.25
  const context = new OfflineAudioContext(2, Math.ceil(duration * sampleRate), sampleRate)
  const master = context.createGain()
  master.gain.value = 0.72
  master.connect(context.destination)
  for (const track of composition.tracks) {
    if (track.muted || track.gain <= 0) continue
    const gain = context.createGain()
    const panner = context.createStereoPanner()
    gain.gain.value = track.gain
    panner.pan.value = track.pan
    gain.connect(panner)
    panner.connect(master)
    for (const note of track.notes) {
      const startsAt = note.start * secondsPerBeat
      const endsAt = (note.start + note.duration) * secondsPerBeat
      scheduleOfflineNote(context, gain, track.waveform, note.pitch, note.velocity, startsAt, endsAt)
    }
  }
  return context.startRendering()
}
