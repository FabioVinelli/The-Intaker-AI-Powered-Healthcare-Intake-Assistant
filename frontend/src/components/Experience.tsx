import React, { useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Environment, ContactShadows, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { Sphere } from './Sphere';
import { HolographicUI } from './HolographicUI';
import { WeatherCondition, A2UIElement, VoiceCommand, TimeOfDay, IntakeMode } from '../types';
import { WEATHER_CONFIG, TIME_CONFIG } from '../constants';

interface ExperienceProps {
    weather: WeatherCondition;
    timeOfDay: TimeOfDay;
    audioData: { average: number; data: Uint8Array };
    a2uiState: A2UIElement;
    onA2UIAction: (action: string, value: any) => void;
    showDimensions: boolean;
    voiceCommand: { cmd: VoiceCommand; ts: number } | null;
    onPlaySound: (type: 'select' | 'adjust') => void;
    mode?: IntakeMode;
}

const SceneController: React.FC<{ timeOfDay: TimeOfDay }> = ({ timeOfDay }) => {
    const { scene } = useThree();
    const lightRef = useRef<THREE.SpotLight>(null);
    const config = TIME_CONFIG[timeOfDay];
    const targetGround = useRef(new THREE.Color(config.groundColor));
    const targetLight = useRef(new THREE.Color(config.lightColor));

    useFrame((state, delta) => {
        targetGround.current.set(config.groundColor);
        if (scene.background instanceof THREE.Color) {
            scene.background.lerp(targetGround.current, delta * 1.5);
        }
        if (lightRef.current) {
            targetLight.current.set(config.lightColor);
            lightRef.current.color.lerp(targetLight.current, delta * 1.5);
            lightRef.current.intensity = THREE.MathUtils.lerp(lightRef.current.intensity, config.lightIntensity, delta * 1.5);
        }
    });

    return (
        <spotLight ref={lightRef} position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={config.lightIntensity} castShadow />
    );
};

export const Experience: React.FC<ExperienceProps> = ({
    weather, timeOfDay, audioData, a2uiState, onA2UIAction, showDimensions, voiceCommand, onPlaySound, mode = 'clinical'
}) => {
    const weatherConfig = WEATHER_CONFIG[weather];

    return (
        <Canvas camera={{ position: [0, 0, 6], fov: 45 }} dpr={[1, 2]} gl={{ antialias: true, toneMappingExposure: 1.2 }} shadows>
            <color attach="background" args={[TIME_CONFIG[timeOfDay].groundColor]} />
            <SceneController timeOfDay={timeOfDay} />
            <ambientLight intensity={0.4} />
            <Environment preset={weatherConfig.envPreset} background blur={0.8} />
            <group position={[0, 0, 0]}>
                <Sphere weather={weather} timeOfDay={timeOfDay} audioData={audioData} mode={mode} />
                <HolographicUI a2uiState={a2uiState} onA2UIAction={onA2UIAction} showDimensions={showDimensions} voiceCommand={voiceCommand} onPlaySound={onPlaySound} />
            </group>
            <ContactShadows resolution={1024} scale={20} blur={2} opacity={0.5} far={10} color="#000000" />
            <OrbitControls enablePan={false} enableZoom={false} minPolarAngle={Math.PI / 3} maxPolarAngle={Math.PI / 1.5} />
        </Canvas>
    );
};
