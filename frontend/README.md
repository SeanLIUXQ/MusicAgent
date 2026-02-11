# Sonic Pi Generator

A Vue.js-based web application for generating Sonic Pi music code using AI. This application provides an intuitive interface for creating, refining, and exporting music code with feedback loops and style transfer capabilities.

## Features

- 🎵 **AI-Powered Music Generation**: Describe your desired music and let AI generate Sonic Pi code
- 🔄 **Iterative Refinement**: Provide feedback to improve generated music
- 🎨 **Style Transfer**: Transform existing music into different styles
- 📝 **Real-time Logs**: Monitor the generation process with detailed logs
- 💾 **MIDI Export**: Download generated music as MIDI files
- 📋 **Code Management**: Copy and review generated Sonic Pi code

## Prerequisites

Before running this application, ensure you have:

- **Node.js** (v16 or higher)
- **npm** or **yarn** package manager
- **Backend API** running on `http://localhost:5000` (see Backend Setup below)

## Installation

1. **Clone or download the project**

2. **Install dependencies**

```bash
npm install
# or
yarn install
```

3. **Required packages** (should be installed automatically):

```json
{
  "vue": "^3.x",
  "axios": "^1.x"
}
```

## Backend Setup

This Vue application requires a backend API server running on `http://localhost:5000`. The backend should provide the following endpoints:

## Running the Application

### Development Mode

```bash
npm run dev
# or
yarn dev
```

The application will be available at `http://localhost:5173` (or another port if specified).

### Production Build

```bash
npm run build
# or
yarn build
```

Then serve the `dist` folder using a static file server.

## Usage Guide

### 1. Generate Music

1. Enter a description of your desired music in the **Music Description** textarea
   - Example: "A cheerful melody with piano and drums, 120 BPM, major key"
2. Click the **Generate** button
3. Monitor the generation process in the **Generation Log** panel
4. Review the generated code in the **Generated Code** panel

### 2. Provide Feedback

1. After generating music, click the **Feedback** button
2. Describe improvements you'd like (e.g., "Make it slower", "Add more bass")
3. Click **Submit Feedback**
4. The system will regenerate the music incorporating your feedback

### 3. Style Transfer

1. With generated code visible, click the **Style Transfer** button
2. Specify the style you want (e.g., "Convert to jazz style")
3. Click **Apply Style**
4. The system will transform your music to the requested style

### 4. Export MIDI

1. Once generation is complete and MIDI is available, click **Download MIDI**
2. The MIDI file will open in a new tab for download

### 5. Copy Code

1. Click the **📋** (clipboard) icon in the Generated Code section
2. The Sonic Pi code will be copied to your clipboard
3. Paste it into Sonic Pi to play the music

## Project Structure

```
sonic-pi-generator/
├── src/
│   ├── components/
│   │   └── SonicPiGenerator.vue  # Main component
│   ├── App.vue
│   └── main.ts
├── public/
├── package.json
└── README.md
```

## Configuration

To change the backend API URL, modify the `API_BASE_URL` constant in the component:

```typescript
const API_BASE_URL = 'http://localhost:5000/api'
```

## Troubleshooting

### Backend Connection Issues

- **Error**: "Network Error" or "Failed to fetch"
- **Solution**: Ensure the backend API is running on `http://localhost:5000`
- **Check**: Verify CORS is properly configured on the backend

### Generation Stuck at "Processing..."

- **Solution**: Check the backend logs for errors
- **Check**: Ensure the backend task processing system is working correctly

### MIDI Download Not Available

- **Cause**: MIDI compilation may have failed
- **Solution**: Check the generation logs for compilation errors
- **Note**: Code generation may succeed even if MIDI compilation fails

## Browser Compatibility

- Chrome/Edge (recommended): Full support
- Firefox: Full support
- Safari: Full support
- Mobile browsers: Responsive design supported

## Development Notes

### Key Technologies

- **Vue 3** with Composition API
- **TypeScript** for type safety
- **Axios** for HTTP requests
- **CSS Grid** and **Flexbox** for responsive layout

### State Management

The application uses Vue's reactive refs for state management:

- `isGenerating`: Generation status
- `generatedCode`: Current Sonic Pi code
- `logs`: Generation process logs
- `midiPath`: Path to generated MIDI file

### Polling Mechanism

The app polls the backend every 1 second to check task status. Polling automatically stops when:

- Task completes successfully
- Task encounters an error
- Component is unmounted

## License

[Specify your license here]

## Support

For issues or questions, please [contact information or issue tracker link].

---

**Note**: This application requires a compatible backend API server to function. Ensure your backend implements all required endpoints before running the frontend.
