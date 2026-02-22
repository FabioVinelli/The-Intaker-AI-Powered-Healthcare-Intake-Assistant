import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { MeshTransmissionMaterial, Float } from '@react-three/drei';
import * as THREE from 'three';
import { WeatherCondition, TimeOfDay, IntakeMode, VoiceState } from '../types';
import { WEATHER_CONFIG, TIME_CONFIG, MODE_CONFIG, VOICE_STATE_CONFIG } from '../constants';

const CoreMaterial = {
    uniforms: {
        uTime: { value: 0 },
        uAudio: { value: 0 },
        uPulseSpeed: { value: 1.0 },
        uIntensity: { value: 0.5 },
        uColorHigh: { value: new THREE.Color('#ffaa00') },
        uColorLow: { value: new THREE.Color('#000000') },
    },
    vertexShader: `
    varying vec2 vUv;
    varying float vDistortion;
    uniform float uTime;
    uniform float uAudio;
    uniform float uPulseSpeed;
    uniform float uIntensity;

    vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
    vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
    float snoise(vec3 v) {
      const vec2  C = vec2(1.0/6.0, 1.0/3.0) ;
      const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);
      vec3 i  = floor(v + dot(v, C.yyy) );
      vec3 x0 = v - i + dot(i, C.xxx) ;
      vec3 g = step(x0.yzx, x0.xyz);
      vec3 l = 1.0 - g;
      vec3 i1 = min( g.xyz, l.zxy );
      vec3 i2 = max( g.xyz, l.zxy );
      vec3 x1 = x0 - i1 + C.xxx;
      vec3 x2 = x0 - i2 + C.yyy;
      vec3 x3 = x0 - D.yyy;
      i = mod289(i);
      vec4 p = permute( permute( permute(
                i.z + vec4(0.0, i1.z, i2.z, 1.0 ))
              + i.y + vec4(0.0, i1.y, i2.y, 1.0 ))
              + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));
      float n_ = 0.142857142857;
      vec3  ns = n_ * D.wyz - D.xzx;
      vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
      vec4 x_ = floor(j * ns.z);
      vec4 y_ = floor(j - 7.0 * x_ );
      vec4 x = x_ *ns.x + ns.yyyy;
      vec4 y = y_ *ns.x + ns.yyyy;
      vec4 h = 1.0 - abs(x) - abs(y);
      vec4 b0 = vec4( x.xy, y.xy );
      vec4 b1 = vec4( x.zw, y.zw );
      vec4 s0 = floor(b0)*2.0 + 1.0;
      vec4 s1 = floor(b1)*2.0 + 1.0;
      vec4 sh = -step(h, vec4(0.0));
      vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;
      vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;
      vec3 p0 = vec3(a0.xy,h.x);
      vec3 p1 = vec3(a0.zw,h.y);
      vec3 p2 = vec3(a1.xy,h.z);
      vec3 p3 = vec3(a1.zw,h.w);
      vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
      p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
      vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
      m = m * m;
      return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3) ) );
    }

    void main() {
      vUv = uv;
      // Breathing effect with configurable pulse speed
      float breath = sin(uTime * uPulseSpeed) * 0.05 * uIntensity;
      float noiseVal = snoise(position * 2.0 + uTime * uPulseSpeed);
      float distortion = noiseVal * (0.1 + uAudio * 0.5) * uIntensity;
      vDistortion = distortion;
      vec3 newPos = position + normal * (breath + distortion);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(newPos, 1.0);
    }
  `,
    fragmentShader: `
    varying vec2 vUv;
    varying float vDistortion;
    uniform float uAudio;
    uniform float uIntensity;
    uniform vec3 uColorHigh;
    uniform vec3 uColorLow;

    void main() {
      vec3 color = mix(uColorLow, uColorHigh, smoothstep(-0.2, 0.5, vDistortion + uAudio));
      float alpha = 0.5 + uIntensity * 0.5 + uAudio * 0.3;
      gl_FragColor = vec4(color, alpha);
    }
  `
};

interface SphereProps {
    weather: WeatherCondition;
    timeOfDay: TimeOfDay;
    audioData: { average: number; data: Uint8Array };
    mode?: IntakeMode;
    voiceState?: VoiceState;
}

/**
 * Enhanced Sphere Component with Voice State Support
 * 
 * Voice States (per Mission 10):
 * - idle/listening: Deep Blue (Calm, waiting)
 * - thinking: Amber (Processing)
 * - speaking: Emerald Green (Active)
 * 
 * Uses smooth spring transitions between color states to prevent flickering.
 */
export const Sphere: React.FC<SphereProps> = ({
    weather,
    timeOfDay,
    audioData,
    mode = 'clinical',
    voiceState = 'idle'
}) => {
    const outerMesh = useRef<THREE.Mesh>(null);
    const coreMesh = useRef<THREE.Mesh>(null);
    const coreMaterialRef = useRef<THREE.ShaderMaterial>(null);
    const transmissionRef = useRef<any>(null);

    const weatherConfig = WEATHER_CONFIG[weather];
    const modeConfig = MODE_CONFIG[mode];
    const voiceConfig = VOICE_STATE_CONFIG[voiceState];

    // Current color refs for smooth interpolation
    const currentColorHigh = useRef(new THREE.Color(voiceConfig.coreColorHigh));
    const currentColorLow = useRef(new THREE.Color(voiceConfig.coreColorLow));
    const currentGlassColor = useRef(new THREE.Color(voiceConfig.glassColor));
    const currentPulseSpeed = useRef(voiceConfig.pulseSpeed);
    const currentIntensity = useRef(voiceConfig.intensity);

    // Target colors based on current voice state
    const targetColorHigh = useMemo(() => new THREE.Color(voiceConfig.coreColorHigh), [voiceConfig.coreColorHigh]);
    const targetColorLow = useMemo(() => new THREE.Color(voiceConfig.coreColorLow), [voiceConfig.coreColorLow]);
    const targetGlassColor = useMemo(() => new THREE.Color(voiceConfig.glassColor), [voiceConfig.glassColor]);

    useFrame((state) => {
        const time = state.clock.getElapsedTime();
        const normalizedAudio = audioData.average / 255.0;

        // Smooth spring-like lerp speed for color transitions
        // Slower lerp prevents flickering during rapid state changes
        const colorLerpSpeed = 0.03; // Smooth, non-flickering transition
        const valueLerpSpeed = 0.05;

        // Smoothly interpolate to target colors (spring-like behavior)
        currentColorHigh.current.lerp(targetColorHigh, colorLerpSpeed);
        currentColorLow.current.lerp(targetColorLow, colorLerpSpeed);
        currentGlassColor.current.lerp(targetGlassColor, colorLerpSpeed);

        // Smoothly interpolate pulse speed and intensity
        currentPulseSpeed.current = THREE.MathUtils.lerp(
            currentPulseSpeed.current,
            voiceConfig.pulseSpeed,
            valueLerpSpeed
        );
        currentIntensity.current = THREE.MathUtils.lerp(
            currentIntensity.current,
            voiceConfig.intensity,
            valueLerpSpeed
        );

        if (coreMaterialRef.current) {
            coreMaterialRef.current.uniforms.uTime.value = time;
            coreMaterialRef.current.uniforms.uPulseSpeed.value = currentPulseSpeed.current;
            coreMaterialRef.current.uniforms.uIntensity.value = currentIntensity.current;

            // Smooth audio response
            coreMaterialRef.current.uniforms.uAudio.value = THREE.MathUtils.lerp(
                coreMaterialRef.current.uniforms.uAudio.value,
                normalizedAudio,
                0.1
            );

            // Apply smoothly interpolated colors
            coreMaterialRef.current.uniforms.uColorHigh.value.copy(currentColorHigh.current);
            coreMaterialRef.current.uniforms.uColorLow.value.copy(currentColorLow.current);
        }

        if (transmissionRef.current && transmissionRef.current.color) {
            transmissionRef.current.color.copy(currentGlassColor.current);
        }

        if (outerMesh.current) {
            // Subtle rotation influenced by voice state
            const rotationSpeed = 0.05 * currentPulseSpeed.current;
            outerMesh.current.rotation.y = time * rotationSpeed;
            outerMesh.current.rotation.z = Math.sin(time * 0.1 * currentPulseSpeed.current) * 0.05;
        }
    });

    return (
        <group>
            <Float
                speed={1.5 * voiceConfig.pulseSpeed}
                rotationIntensity={0.2}
                floatIntensity={0.5 * voiceConfig.intensity}
            >
                {/* Outer Glass Shell */}
                <mesh ref={outerMesh} scale={[2, 2, 2]}>
                    <sphereGeometry args={[1, 64, 64]} />
                    <MeshTransmissionMaterial
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
                        color={voiceConfig.glassColor}
                        attenuationDistance={0.5}
                        attenuationColor="#ffffff"
                    />
                </mesh>

                {/* Inner Animated Core */}
                <mesh ref={coreMesh} scale={[1.2, 1.2, 1.2]}>
                    <icosahedronGeometry args={[1, 30]} />
                    <shaderMaterial
                        ref={coreMaterialRef}
                        args={[CoreMaterial]}
                        transparent
                        blending={THREE.AdditiveBlending}
                        depthWrite={false}
                    />
                </mesh>
            </Float>
        </group>
    );
};
