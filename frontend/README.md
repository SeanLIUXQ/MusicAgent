# MusicAgent Frontend

Vue 3 + TypeScript + Vite browser music workspace. Playback uses the Web Audio API; live visualization uses an `AnalyserNode` and Canvas; WAV export uses `OfflineAudioContext`.

```sh
npm install
npm run dev
```

The development server proxies `/api` to `http://127.0.0.1:5000`.
