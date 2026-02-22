import React, { useRef, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Billboard, Text } from '@react-three/drei';
import * as THREE from 'three';
import { ASAM_DIMENSIONS } from '../constants';
import { A2UIElement, VoiceCommand } from '../types';

interface HolographicUIProps {
    a2uiState: A2UIElement;
    onA2UIAction: (action: string, value: any) => void;
    showDimensions: boolean;
    voiceCommand: { cmd: VoiceCommand; ts: number } | null;
    onPlaySound: (type: 'select' | 'adjust') => void;
}

export const HolographicUI: React.FC<HolographicUIProps> = ({
    a2uiState, onA2UIAction, showDimensions, voiceCommand, onPlaySound
}) => {
    const groupRef = useRef<THREE.Group>(null);
    const [activeFeedback, setActiveFeedback] = useState<string | null>(null);

    useEffect(() => {
        if (!voiceCommand) return;
        const { cmd } = voiceCommand;
        if (a2uiState === 'button' && cmd === 'confirm') {
            setActiveFeedback('button');
            onPlaySound('select');
            onA2UIAction('button', 'confirm-voice');
            setTimeout(() => setActiveFeedback(null), 1000);
        }
    }, [voiceCommand, a2uiState, onA2UIAction, onPlaySound]);

    useFrame(() => {
        if (groupRef.current) groupRef.current.rotation.y += 0.002;
    });

    return (
        <group ref={groupRef}>
            {showDimensions && ASAM_DIMENSIONS.map((dim, index) => {
                const angle = (index / ASAM_DIMENSIONS.length) * Math.PI * 2;
                const radius = 2.8;
                return (
                    <group key={dim.id} position={[Math.cos(angle) * radius, Math.sin(index * 2) * 0.5, Math.sin(angle) * radius]}>
                        <Billboard follow={true}>
                            <Text fontSize={0.15} color="white" anchorX="center" anchorY="middle" font="https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hjp-Ek-_EeA.woff">
                                {dim.short.toUpperCase()}
                            </Text>
                        </Billboard>
                    </group>
                );
            })}
        </group>
    );
};
