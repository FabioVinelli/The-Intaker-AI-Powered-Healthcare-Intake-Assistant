This transfer package contains the complete Holographic Sphere UI (the "Neural Orb"), including the audio-reactive backend logic, shaders, and 3D environment settings.

To transfer this to your main MacBook Pro project, follow these steps.

### **1\. Install Dependencies**

Run this command in your main project's terminal to install the required 3D and React libraries:

bash

npm install three @react-three/fiber @react-three/drei lucide-react

### **2\. File Directory Structure**

Create the following file structure in your destination project (e.g., 

```
src/
```

):

text

src/

├── components/

│   ├── Experience.tsx       \<-- Main 3D Canvas Container

│   ├── Sphere.tsx           \<-- The Neural Orb (Shader Logic)

│   └── HolographicUI.tsx    \<-- 3D Text & Controls Overlay

├── hooks/

│   └── useAudioAnalyzer.ts  \<-- Audio Logic for Pulse Effect

├── constants.ts             \<-- Config for Weather/Time colors

└── types.ts                 \<-- Shared Types

---

### **3\. The Code**

Copy the content below into the respective files.

```
src/types.ts
```

typescript

import React from 'react';

export type WeatherCondition \= 'sunny' | 'rainy' | 'overcast';

export interface WeatherState {

 condition: WeatherCondition;

 temperature: number;

 description: string;

}

export type ASAMDimension \= {

 id: number;

 name: string;

 score: number; *// 0-4 risk rating*

};

export type A2UIElement \= 'slider' | 'button' | 'confirmation' | null;

export interface A2UIPayload {

 type: A2UIElement;

 label?: string;

 data?: any;

}

export type VoiceCommand \= 'select' | 'adjust' | 'confirm' | 'pause' | 'resume' | null;

export type TimeOfDay \= 'morning' | 'afternoon' | 'night';

export type IntakeState \= 'active' | 'hold' | 'escalating';

export type IntakeMode \= 'clinical' | 'technical';

*// Augment the JSX namespace to include Three.js elements*

declare global {

 namespace JSX {

   interface IntrinsicElements {

     group: any;

     mesh: any;

     sphereGeometry: any;

     icosahedronGeometry: any;

     shaderMaterial: any;

     spotLight: any;

     ambientLight: any;

     color: any;

   }

 }

}

```
src/constants.ts
```

typescript

import { WeatherCondition, TimeOfDay, IntakeMode } from "./types";

export const WEATHER\_CONFIG: Record\<WeatherCondition, {

 envPreset: "sunset" | "dawn" | "night" | "warehouse" | "forest" | "apartment" | "studio" | "city" | "park" | "lobby";

 transmission: number;

 roughness: number;

}\> \= {

 sunny: { envPreset: "sunset", transmission: 0.95, roughness: 0.05 },

 rainy: { envPreset: "city", transmission: 0.98, roughness: 0.15 },

 overcast: { envPreset: "studio", transmission: 0.92, roughness: 0.2 }

};

export const TIME\_CONFIG: Record\<TimeOfDay, {

 groundColor: string;

 lightColor: string;

 lightIntensity: number;

 coreColorHigh: string;

 coreColorLow: string;

 glassColor: string;

}\> \= {

 morning: {

   groundColor: "\#FFDAB9", lightColor: "\#FF8C00", lightIntensity: 1.8,

   coreColorHigh: "\#FFA500", coreColorLow: "\#FF4500", glassColor: "\#FFEBCD"

 },

 afternoon: {

   groundColor: "\#87CEEB", lightColor: "\#FFFFFF", lightIntensity: 2.0,

   coreColorHigh: "\#E0FFFF", coreColorLow: "\#00BFFF", glassColor: "\#F0F8FF"

 },

 night: {

   groundColor: "\#0F172A", lightColor: "\#818CF8", lightIntensity: 0.8,

   coreColorHigh: "\#A5B4FC", coreColorLow: "\#312E81", glassColor: "\#1E293B"

 }

};

export const ASAM\_DIMENSIONS \= \[

 { id: 1, name: "Intoxication/Withdrawal", short: "Acute" },

 { id: 2, name: "Biomedical Conditions", short: "Biomed" },

 { id: 3, name: "Emotional/Behavioral", short: "Psych" },

 { id: 4, name: "Readiness to Change", short: "Change" },

 { id: 5, name: "Relapse Potential", short: "Relapse" },

 { id: 6, name: "Recovery Environment", short: "Env" }

\];

export const MODE\_CONFIG: Record\<'clinical' | 'technical', {

 coreColorHigh: string;

 coreColorLow: string;

 glassColor: string;

}\> \= {

 clinical: {

   coreColorHigh: '\#ffaa00',  *// Warm amber*

   coreColorLow: '\#442200',   *// Deep amber*

   glassColor: '\#ffcc66',     *// Light amber glass*

 },

 technical: {

   coreColorHigh: '\#00aaff',  *// Electric blue*

   coreColorLow: '\#002244',   *// Deep blue*

   glassColor: '\#66ccff',     *// Light blue glass*

 }

};

```
src/hooks/useAudioAnalyzer.ts
```

typescript

import { useEffect, useRef, useState, useCallback } from 'react';

export const useAudioAnalyzer \= () \=\> {

 const \[isListening, setIsListening\] \= useState(false);

 const analyserRef \= useRef\<AnalyserNode | null\>(null);

 const dataArrayRef \= useRef\<Uint8Array | null\>(null);

 const audioContextRef \= useRef\<AudioContext | null\>(null);

 const sourceRef \= useRef\<MediaStreamAudioSourceNode | null\>(null);

 const startListening \= useCallback(async () \=\> {

   try {

     if (audioContextRef.current) return;

     const stream \= await navigator.mediaDevices.getUserMedia({ audio: true });

     const audioContext \= new (window.AudioContext || (window as any).webkitAudioContext)();

     const analyser \= audioContext.createAnalyser();

    

     analyser.fftSize \= 256;

     const source \= audioContext.createMediaStreamSource(stream);

     source.connect(analyser);

    

     analyserRef.current \= analyser;

     dataArrayRef.current \= new Uint8Array(analyser.frequencyBinCount);

     audioContextRef.current \= audioContext;

     sourceRef.current \= source;

    

     setIsListening(true);

   } catch (err) {

     console.error("Error accessing microphone:", err);

     setIsListening(false);

   }

 }, \[\]);

 const stopListening \= useCallback(() \=\> {

   if (sourceRef.current) sourceRef.current.disconnect();

   if (audioContextRef.current) audioContextRef.current.close();


   analyserRef.current \= null;

   audioContextRef.current \= null;

   sourceRef.current \= null;

   setIsListening(false);

 }, \[\]);

 const getFrequencyData \= useCallback(() \=\> {

   if (analyserRef.current && dataArrayRef.current) {

     analyserRef.current.getByteFrequencyData(dataArrayRef.current);

     let sum \= 0;

     for (let i \= 0; i \< dataArrayRef.current.length; i\++) {

       sum \+= dataArrayRef.current\[i\];

     }

     const average \= sum / dataArrayRef.current.length;

     return { average, data: dataArrayRef.current };

   }

   return { average: 0, data: new Uint8Array(0) };

 }, \[\]);

 useEffect(() \=\> {

   return () \=\> {

     stopListening();

   };

 }, \[stopListening\]);

 return { isListening, startListening, stopListening, getFrequencyData };

};

```
src/components/Sphere.tsx
```

typescript

import React, { useRef } from 'react';

import { useFrame } from '@react-three/fiber';

import { MeshTransmissionMaterial, Float } from '@react-three/drei';

import \* as THREE from 'three';

import { WeatherCondition, TimeOfDay, IntakeMode } from '../types';

import { WEATHER\_CONFIG, TIME\_CONFIG, MODE\_CONFIG } from '../constants';

const CoreMaterial \= {

 uniforms: {

   uTime: { value: 0 },

   uAudio: { value: 0 },

   uColorHigh: { value: new THREE.Color('\#ffaa00') },

   uColorLow: { value: new THREE.Color('\#000000') },

 },

 vertexShader: \`

   varying vec2 vUv;

   varying float vDistortion;

   uniform float uTime;

   uniform float uAudio;


   vec3 mod289(vec3 x) { return x \- floor(x \* (1.0 / 289.0)) \* 289.0; }

   vec4 mod289(vec4 x) { return x \- floor(x \* (1.0 / 289.0)) \* 289.0; }

   vec4 permute(vec4 x) { return mod289(((x\*34.0)+1.0)\*x); }

   vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 \- 0.85373472095314 \* r; }

   float snoise(vec3 v) {

     const vec2  C \= vec2(1.0/6.0, 1.0/3.0) ;

     const vec4  D \= vec4(0.0, 0.5, 1.0, 2.0);

     vec3 i  \= floor(v \+ dot(v, C.yyy) );

     vec3 x0 \= v \- i \+ dot(i, C.xxx) ;

     vec3 g \= step(x0.yzx, x0.xyz);

     vec3 l \= 1.0 \- g;

     vec3 i1 \= min( g.xyz, l.zxy );

     vec3 i2 \= max( g.xyz, l.zxy );

     vec3 x1 \= x0 \- i1 \+ C.xxx;

     vec3 x2 \= x0 \- i2 \+ C.yyy;

     vec3 x3 \= x0 \- D.yyy;

     i \= mod289(i);

     vec4 p \= permute( permute( permute(

               i.z \+ vec4(0.0, i1.z, i2.z, 1.0 ))

             \+ i.y \+ vec4(0.0, i1.y, i2.y, 1.0 ))

             \+ i.x \+ vec4(0.0, i1.x, i2.x, 1.0 ));

     float n\_ \= 0.142857142857;

     vec3  ns \= n\_ \* D.wyz \- D.xzx;

     vec4 j \= p \- 49.0 \* floor(p \* ns.z \* ns.z);

     vec4 x\_ \= floor(j \* ns.z);

     vec4 y\_ \= floor(j \- 7.0 \* x\_ );

     vec4 x \= x\_ \*ns.x \+ ns.yyyy;

     vec4 y \= y\_ \*ns.x \+ ns.yyyy;

     vec4 h \= 1.0 \- abs(x) \- abs(y);

     vec4 b0 \= vec4( x.xy, y.xy );

     vec4 b1 \= vec4( x.zw, y.zw );

     vec4 s0 \= floor(b0)\*2.0 \+ 1.0;

     vec4 s1 \= floor(b1)\*2.0 \+ 1.0;

     vec4 sh \= \-step(h, vec4(0.0));

     vec4 a0 \= b0.xzyw \+ s0.xzyw\*sh.xxyy ;

     vec4 a1 \= b1.xzyw \+ s1.xzyw\*sh.zzww ;

     vec3 p0 \= vec3(a0.xy,h.x);

     vec3 p1 \= vec3(a0.zw,h.y);

     vec3 p2 \= vec3(a1.xy,h.z);

     vec3 p3 \= vec3(a1.zw,h.w);

     vec4 norm \= taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));

     p0 \*= norm.x; p1 \*= norm.y; p2 \*= norm.z; p3 \*= norm.w;

     vec4 m \= max(0.6 \- vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);

     m \= m \* m;

     return 42.0 \* dot( m\*m, vec4( dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3) ) );

   }

   void main() {

     vUv \= uv;

     float breath \= sin(uTime \* 0.5) \* 0.05;

     float noiseVal \= snoise(position \* 2.0 \+ uTime \* 0.5);

     float distortion \= noiseVal \* (0.1 \+ uAudio \* 0.5);

     vDistortion \= distortion;

     vec3 newPos \= position \+ normal \* (breath \+ distortion);

     gl\_Position \= projectionMatrix \* modelViewMatrix \* vec4(newPos, 1.0);

   }

 \`,

 fragmentShader: \`

   varying vec2 vUv;

   varying float vDistortion;

   uniform float uAudio;

   uniform vec3 uColorHigh;

   uniform vec3 uColorLow;

   void main() {

     vec3 color \= mix(uColorLow, uColorHigh, smoothstep(-0.2, 0.5, vDistortion \+ uAudio));

     float alpha \= 0.6 \+ uAudio \* 0.4;

     gl\_FragColor \= vec4(color, alpha);

   }

 \`

};

interface SphereProps {

 weather: WeatherCondition;

 timeOfDay: TimeOfDay;

 audioData: { average: number; data: Uint8Array };

 mode?: IntakeMode;

}

export const Sphere: React.FC\<SphereProps\> \= ({ *weather*, *timeOfDay*, *audioData*, *mode* \= 'clinical' }) \=\> {

 const outerMesh \= useRef\<THREE.Mesh\>(null);

 const coreMesh \= useRef\<THREE.Mesh\>(null);

 const coreMaterialRef \= useRef\<THREE.ShaderMaterial\>(null);

 const transmissionRef \= useRef\<any\>(null);

 const weatherConfig \= WEATHER\_CONFIG\[weather\];

 const modeConfig \= MODE\_CONFIG\[mode\];

 const targetColorHigh \= useRef(new THREE.Color(modeConfig.coreColorHigh));

 const targetColorLow \= useRef(new THREE.Color(modeConfig.coreColorLow));

 const targetGlassColor \= useRef(new THREE.Color(modeConfig.glassColor));

 useFrame((*state*) \=\> {

   const time \= state.clock.getElapsedTime();

   const normalizedAudio \= audioData.average / 255.0;

   const lerpSpeed \= 0.05;

   targetColorHigh.current.set(modeConfig.coreColorHigh);

   targetColorLow.current.set(modeConfig.coreColorLow);

   targetGlassColor.current.set(modeConfig.glassColor);

   if (coreMaterialRef.current) {

     coreMaterialRef.current.uniforms.uTime.value \= time;

     coreMaterialRef.current.uniforms.uAudio.value \= THREE.MathUtils.lerp(

       coreMaterialRef.current.uniforms.uAudio.value, normalizedAudio, 0.1

     );

     coreMaterialRef.current.uniforms.uColorHigh.value.lerp(targetColorHigh.current, lerpSpeed);

     coreMaterialRef.current.uniforms.uColorLow.value.lerp(targetColorLow.current, lerpSpeed);

   }

   if (transmissionRef.current && transmissionRef.current.color) {

     transmissionRef.current.color.lerp(targetGlassColor.current, lerpSpeed);

   }

   if (outerMesh.current) {

     outerMesh.current.rotation.y \= time \* 0.05;

     outerMesh.current.rotation.z \= Math.sin(time \* 0.1) \* 0.05;

   }

 });

 return (

   \<group\>

     \<Float speed\={1.5} rotationIntensity\={0.2} floatIntensity\={0.5}\>

       \<mesh ref\={outerMesh} scale\={\[2, 2, 2\]}\>

         \<sphereGeometry args={\[1, 64, 64\]} /\>

         \<MeshTransmissionMaterial

           ref={transmissionRef}

           backside={false}

           samples={16}

           resolution={1024}

           transmission={weatherConfig.transmission}

           roughness={weatherConfig.roughness}

           thickness={1.5}

           ior={1.5}

           chromaticAberration={0.06}

           anisotropy={0.1}

           distortion={0.1}

           distortionScale={0.3}

           temporalDistortion={0.5}

           color={modeConfig.glassColor}

           attenuationDistance={0.5}

           attenuationColor="\#ffffff"

         /\>

       \</mesh\>

       \<mesh ref={coreMesh} scale={\[1.2, 1.2, 1.2\]}\>

         \<icosahedronGeometry args={\[1, 30\]} /\>

         \<shaderMaterial

           ref={coreMaterialRef}

           args={\[CoreMaterial\]}

           transparent

           blending={THREE.AdditiveBlending}

           depthWrite={false}

         /\>

       \</mesh\>

     \</Float\>

   \</group\>

 );

};

```
src/components/HolographicUI.tsx
```

typescript

import React, { useRef, useState, useEffect } from 'react';

import { useFrame } from '@react-three/fiber';

import { Text, Html, Billboard } from '@react-three/drei';

import \* as THREE from 'three';

import { ASAM\_DIMENSIONS } from '../constants';

import { A2UIElement, VoiceCommand } from '../types';

interface HolographicUIProps {

 a2uiState: A2UIElement;

 onA2UIAction: (*action*: string, *value*: any) \=\> void;

 showDimensions: boolean;

 voiceCommand: { cmd: VoiceCommand; ts: number } | null;

 onPlaySound: (*type*: 'select' | 'adjust') \=\> void;

}

export const HolographicUI: React.FC\<HolographicUIProps\> \= ({

 a2uiState, onA2UIAction, showDimensions, voiceCommand, onPlaySound

}) \=\> {

 const groupRef \= useRef\<THREE.Group\>(null);

 const \[activeFeedback, setActiveFeedback\] \= useState\<string | null\>(null);

  useEffect(() \=\> {

   if (\!voiceCommand) return;

   const { cmd } \= voiceCommand;

   if (a2uiState \=== 'button' && cmd \=== 'confirm') {

     setActiveFeedback('button');

     onPlaySound('select');

     onA2UIAction('button', 'confirm-voice');

     setTimeout(() \=\> setActiveFeedback(null), 1000);

   }

 }, \[voiceCommand, a2uiState, onA2UIAction, onPlaySound\]);

 useFrame(() \=\> {

   if (groupRef.current) groupRef.current.rotation.y \+= 0.002;

 });

 return (

   \<group ref\={groupRef}\>

     {*showDimensions* && *ASAM\_DIMENSIONS*.*map*((*dim*, *index*) \=\> {

       const angle \= (index / ASAM\_DIMENSIONS.length) \* Math.PI \* 2;

       const radius \= 2.8;

       return (

         \<*group* *key*\={dim.id} position\={\[Math.cos(angle) \* radius, Math.sin(index \* 2) \* 0.5, Math.sin(angle) \* radius\]}\>

           \<Billboard follow={true}\>

               \<Text fontSize={0.15} color="white" anchorX="center" anchorY="middle" font="https:*//fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS\_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hjp-Ek-\_EeA.woff"\>*

               {dim.short.toUpperCase()}

               \</Text\>

           \</Billboard\>

         \</group\>

       );

     })}

   \</*group*\>

 );

};

```
src/components/Experience.tsx
```

typescript

import React, { useRef } from 'react';

import { Canvas, useFrame, useThree } from '@react-three/fiber';

import { Environment, ContactShadows, OrbitControls } from '@react-three/drei';

import \* as THREE from 'three';

import { Sphere } from './Sphere';

import { HolographicUI } from './HolographicUI';

import { WeatherCondition, A2UIElement, VoiceCommand, TimeOfDay, IntakeMode } from '../types';

import { WEATHER\_CONFIG, TIME\_CONFIG } from '../constants';

interface ExperienceProps {

 weather: WeatherCondition;

 timeOfDay: TimeOfDay;

 audioData: { average: number; data: Uint8Array };

 a2uiState: A2UIElement;

 onA2UIAction: (*action*: string, *value*: any) \=\> void;

 showDimensions: boolean;

 voiceCommand: { cmd: VoiceCommand; ts: number } | null;

 onPlaySound: (*type*: 'select' | 'adjust') \=\> void;

 mode?: IntakeMode;

}

const SceneController: React.FC\<{ timeOfDay: TimeOfDay }\> \= ({ *timeOfDay* }) \=\> {

 const { scene } \= useThree();

 const lightRef \= useRef\<THREE.SpotLight\>(null);

 const config \= TIME\_CONFIG\[timeOfDay\];

 const targetGround \= useRef(new THREE.Color(config.groundColor));

 const targetLight \= useRef(new THREE.Color(config.lightColor));

 useFrame((*state*, *delta*) \=\> {

   targetGround.current.set(config.groundColor);

   if (scene.background instanceof THREE.Color) {

     scene.background.lerp(targetGround.current, delta \* 1.5);

   }

   if (lightRef.current) {

     targetLight.current.set(config.lightColor);

     lightRef.current.color.lerp(targetLight.current, delta \* 1.5);

     lightRef.current.intensity \= THREE.MathUtils.lerp(lightRef.current.intensity, config.lightIntensity, delta \* 1.5);

   }

 });

 return (

   \<spotLight ref\={lightRef} position\={\[10, 10, 10\]} angle={0.15} penumbra={1} intensity={config.lightIntensity} castShadow /\>

 );

};

export const Experience: React.FC\<ExperienceProps\> \= ({

 weather, timeOfDay, audioData, a2uiState, onA2UIAction, showDimensions, voiceCommand, onPlaySound, mode \= 'clinical'

}) \=\> {

 const weatherConfig \= WEATHER\_CONFIG\[weather\];

 return (

   \<Canvas camera\={{ position: \[0, 0, 6\], fov: 45 }} dpr\={\[1, 2\]} gl={{ antialias: true, toneMappingExposure: 1.2 }} shadows\>

     \<color attach\="background" args\={\[TIME\_CONFIG\[timeOfDay\].groundColor\]} /\>

     \<SceneController timeOfDay={timeOfDay} /\>

     \<ambientLight intensity={0.4} /\>

     \<Environment preset={weatherConfig.envPreset} background blur={0.8} /\>

     \<group position={\[0, 0, 0\]}\>

       \<Sphere weather={weather} timeOfDay={timeOfDay} audioData={audioData} mode={mode} /\>

       \<HolographicUI a2uiState={a2uiState} onA2UIAction={onA2UIAction} showDimensions={showDimensions} voiceCommand={voiceCommand} onPlaySound={onPlaySound} /\>

     \</group\>

     \<ContactShadows resolution={1024} scale={20} blur={2} opacity={0.5} far={10} color="\#000000" /\>

     \<OrbitControls enablePan={false} enableZoom={false} minPolarAngle={Math.PI / 3} maxPolarAngle={Math.PI / 1.5} /\>

   \</Canvas\>

 );

};

---

### **4\. Implementation Guide**

Finally, in your main App file (e.g., 

App.tsx), wrap it all together like this:

typescript

import React, { useState, useEffect } from 'react';

import { Experience } from './components/Experience';

import { useAudioAnalyzer } from './hooks/useAudioAnalyzer';

import { TimeOfDay, WeatherCondition, IntakeMode } from './types';

function App() {

 const { isListening, startListening, getFrequencyData } \= useAudioAnalyzer();

 const \[audioData, setAudioData\] \= useState({ average: 0, data: new Uint8Array(0) });

  *// Example State controls*

 const \[mode, setMode\] \= useState\<IntakeMode\>('clinical');

 const \[timeOfDay, setTimeOfDay\] \= useState\<TimeOfDay\>('morning');

 useEffect(() \=\> {

   let animationFrameId: number;

   const animate \= () \=\> {

     if (isListening) {

       setAudioData(getFrequencyData());

     }

     animationFrameId \= requestAnimationFrame(animate);

   };

   animate();

   return () \=\> cancelAnimationFrame(animationFrameId);

 }, \[isListening, getFrequencyData\]);

 return (

   \<div className\="w-full h-screen bg-black"\>

     {*/\* Experience Canvas \*/*}

     \<div className\="absolute inset-0 z-0"\>

       \<*Experience*

         weather\="sunny"

         timeOfDay\={timeOfDay}

         audioData\={audioData}

         mode\={mode}

         a2uiState\={null}

         onA2UIAction\={() \=\> {}}

         showDimensions\={true}

         voiceCommand\={null}

         onPlaySound\={() \=\> {}}

       /\>

     \</div\>

    

     {*/\* HUD Controls \*/*}

     \<div className\="absolute top-4 left-4 z-10 space-y-2"\>

        \<button onClick\={startListening} className\="bg-white/10 text-white px-4 py-2 rounded border border-white/20"\>

          {*isListening* ? "Listening..." : "Enable Mic"}

        \</button\>

        \<button onClick\={() \=\> setMode(*m* \=\> m \=== 'clinical' ? 'technical' : 'clinical')} className\="bg-white/10 text-white px-4 py-2 rounded border border-white/20"\>

          Toggle Mode ({mode})

        \</button\>

     \</div\>

   \</div\>

 );

}

export default App;  
Good  
Bad

