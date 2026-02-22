import React from 'react';

export type WeatherCondition = 'sunny' | 'rainy' | 'overcast';

export interface WeatherState {
    condition: WeatherCondition;
    temperature: number;
    description: string;
}

export type ASAMDimension = {
    id: number;
    name: string;
    score: number; // 0-4 risk rating
};

export type A2UIElement = 'slider' | 'button' | 'confirmation' | null;

export interface A2UIPayload {
    type: A2UIElement;
    label?: string;
    data?: any;
}

export type VoiceCommand = 'select' | 'adjust' | 'confirm' | 'pause' | 'resume' | null;

export type TimeOfDay = 'morning' | 'afternoon' | 'night';

export type IntakeState = 'active' | 'hold' | 'escalating';

export type IntakeMode = 'clinical' | 'technical';

export type VoiceState = 'idle' | 'listening' | 'thinking' | 'speaking';

// Augment the JSX namespace to include Three.js elements
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
