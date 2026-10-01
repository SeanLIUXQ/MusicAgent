export type Waveform = 'sine' | 'square' | 'sawtooth' | 'triangle'

export interface MusicNote {
  id: string
  pitch: number
  start: number
  duration: number
  velocity: number
}

export interface MusicTrack {
  id: string
  name: string
  instrument: string
  waveform: Waveform
  gain: number
  pan: number
  muted: boolean
  notes: MusicNote[]
}

export interface Composition {
  id: string
  title: string
  tempo: number
  time_signature: [number, number]
  duration_beats: number
  tracks: MusicTrack[]
}

export interface TaskStatus {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'error'
  progress: string
  logs: string[]
  result_composition: Composition | null
  midi_filename: string | null
  composition_filename: string | null
  action: 'generate' | 'arrange' | 'import'
  error_message: string | null
  created_at: string
}

export interface HistoryFile {
  filename: string
  display_name: string
  modified_time: string
  size: number
}
