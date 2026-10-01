const writeString = (view: DataView, offset: number, value: string): void => {
  for (let index = 0; index < value.length; index += 1) view.setUint8(offset + index, value.charCodeAt(index))
}

export const audioBufferToWav = (buffer: AudioBuffer): Blob => {
  const channels = Math.min(buffer.numberOfChannels, 2)
  const samples = buffer.length
  const bytesPerSample = 2
  const blockAlign = channels * bytesPerSample
  const dataSize = samples * blockAlign
  const arrayBuffer = new ArrayBuffer(44 + dataSize)
  const view = new DataView(arrayBuffer)
  writeString(view, 0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeString(view, 8, 'WAVE')
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, channels, true)
  view.setUint32(24, buffer.sampleRate, true)
  view.setUint32(28, buffer.sampleRate * blockAlign, true)
  view.setUint16(32, blockAlign, true)
  view.setUint16(34, 16, true)
  writeString(view, 36, 'data')
  view.setUint32(40, dataSize, true)
  const channelData = Array.from({ length: channels }, (_, channel) => buffer.getChannelData(channel))
  let offset = 44
  for (let sample = 0; sample < samples; sample += 1) {
    for (let channel = 0; channel < channels; channel += 1) {
      const value = Math.max(-1, Math.min(1, channelData[channel]?.[sample] ?? 0))
      view.setInt16(offset, value < 0 ? value * 0x8000 : value * 0x7fff, true)
      offset += bytesPerSample
    }
  }
  return new Blob([arrayBuffer], { type: 'audio/wav' })
}
