Acknowledged. We are proceeding with the **Wix ↔ Sphere Integration Build**.

We will now execute the **"Web Component Bridge"** plan. This involves wrapping your React Sphere in a shell that Wix understands (a Custom Element) and bundling it into a single file.

Here is the exact code your **Antigravity Agent** needs to implement. You can copy these instructions directly into the **Agent Manager** or apply the code yourself.

---

### **1. The Wrapper (`src/web-component/SphereWebComponent.tsx`)**

This is the critical "Bridge" file. It translates Wix's HTML attributes into React props and ensures the `intakeComplete` event breaks out of the Shadow DOM so Wix Velo can catch it.

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import SphereContainer from '../sphere/SphereContainer';

class SphereWebComponent extends HTMLElement {
  private root: ReactDOM.Root | null = null;
  private mountPoint: HTMLDivElement;

  static get observedAttributes() {
    return ['mode'];
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.mountPoint = document.createElement('div');
    // Ensure the container takes full size of the Wix Custom Element
    this.mountPoint.style.width = '100%';
    this.mountPoint.style.height = '100%';
    this.shadowRoot?.appendChild(this.mountPoint);
  }

  connectedCallback() {
    this.render();
  }

  attributeChangedCallback(name: string, oldValue: string, newValue: string) {
    if (name === 'mode' && oldValue !== newValue) {
      this.render();
    }
  }

  disconnectedCallback() {
    if (this.root) {
      this.root.unmount();
    }
  }

  private handleComplete = (data: any) => {
    // DISPATCH EVENT FOR WIX VELO
    // bubbles: true, composed: true are MANDATORY for Shadow DOM events
    this.dispatchEvent(
      new CustomEvent('intakeComplete', {
        detail: data,
        bubbles: true,
        composed: true, 
      })
    );
  };

  private render() {
    const mode = this.getAttribute('mode') || 'ambassador';

    if (!this.root) {
      this.root = ReactDOM.createRoot(this.mountPoint);
    }

    this.root.render(
      <React.StrictMode>
        {/* We pass the shadowRoot as a prop in case styles need to be injected there */}
        <SphereContainer 
          mode={mode as 'ambassador' | 'clinical'} 
          onComplete={this.handleComplete} 
        />
      </React.StrictMode>
    );
  }
}

// Define the custom element for Wix
if (!customElements.get('the-intaker-sphere')) {
  customElements.define('the-intaker-sphere', SphereWebComponent);
}

```

---

### **2. The Logic Container (`src/sphere/SphereContainer.tsx`)**

This component manages the "Brain" switching. It decides whether to load the **Consulting Persona** or the **Clinical Intake Flow**.

```typescript
import React, { useState, useEffect } from 'react';
import { Sphere } from './Sphere'; // Your existing 3D visuals
// In a real build, you'd import your specific logic hooks here
// import { useAmbassadorFlow } from '../modes/ambassador/useAmbassadorFlow';
// import { useClinicalFlow } from '../modes/clinical/useClinicalFlow';

interface SphereContainerProps {
  mode: 'ambassador' | 'clinical';
  onComplete: (data: any) => void;
}

const SphereContainer: React.FC<SphereContainerProps> = ({ mode, onComplete }) => {
  const [isListening, setIsListening] = useState(false);
  const [progress, setProgress] = useState(0.1); // Idle state

  // Visual State Management based on Mode
  useEffect(() => {
    if (mode === 'ambassador') {
      // Ambassador: Calm, steady pulse (Blue/Cool)
      // Visuals would be handled inside <Sphere /> via props or context
      setProgress(0.3); 
    } else {
      // Clinical: Active, alert state (Amber/Warm)
      setProgress(0.6); 
    }
  }, [mode]);

  // Mock Interaction Handler
  const handleInteraction = () => {
    setIsListening(true);
    
    // SIMULATION: End the demo after 5 seconds for testing Wix Redirect
    setTimeout(() => {
      setIsListening(false);
      onComplete({ 
        reason: 'demo_finished', 
        targetUrl: mode === 'ambassador' ? '/contact' : '/thank-you' 
      });
    }, 5000);
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}>
      {/* 3D Sphere Component */}
      <Sphere progress={progress} isListening={isListening} />
      
      {/* Overlay UI (HTML) */}
      <div style={{ position: 'absolute', bottom: '20px', left: '0', width: '100%', textAlign: 'center', pointerEvents: 'none' }}>
        <button 
          onClick={handleInteraction}
          style={{ 
            pointerEvents: 'auto', 
            padding: '10px 20px', 
            borderRadius: '20px', 
            border: 'none', 
            background: 'rgba(255,255,255,0.2)', 
            color: 'white', 
            backdropFilter: 'blur(10px)',
            cursor: 'pointer'
          }}
        >
          {mode === 'ambassador' ? 'Ask About Services' : 'Start Clinical Intake'}
        </button>
      </div>
    </div>
  );
};

export default SphereContainer;

```

---

### **3. The Bundler Config (`vite.config.ts`)**

This configures Vite to output the single file `dist/the-sphere-bundle.js` that Wix requires.

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  define: {
    'process.env': {}, // Polyfill for some libs
  },
  build: {
    lib: {
      entry: path.resolve(__dirname, 'src/web-component/SphereWebComponent.tsx'),
      name: 'TheIntakerSphere',
      formats: ['umd'], // UMD is most compatible for script tags
      fileName: () => 'the-sphere-bundle.js',
    },
    rollupOptions: {
      // Bundle React inside so Wix doesn't need to provide it
      external: [], 
    },
    outDir: 'dist',
    minify: 'esbuild',
  },
});

```

---

### **Execution Steps (Antigravity Terminal)**

Once you have created these files, run these commands to deploy the artifact:

1. **Build the Bundle:**
```bash
npm install
npm run build

```


2. **Upload to Google Cloud (Public):**
```bash
# Replace [YOUR_BUCKET_NAME] with 'intaker-public-assets' or similar
gcloud storage cp dist/the-sphere-bundle.js gs://[YOUR_BUCKET_NAME]/the-sphere-bundle.js

```


3. **Set Permissions:**
```bash
gcloud storage objects update gs://[YOUR_BUCKET_NAME]/the-sphere-bundle.js --add-acl-grant=entity=AllUsers,role=READER

```


4. **Get the URL:**
The URL to paste into Wix is:
`https://storage.googleapis.com/[YOUR_BUCKET_NAME]/the-sphere-bundle.js`

### **Next Action**

**Shall I launch the Agent to scaffold these three files immediately?**