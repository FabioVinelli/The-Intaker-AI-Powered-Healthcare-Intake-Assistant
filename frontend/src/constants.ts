import { WeatherCondition, TimeOfDay, IntakeMode } from "./types";

export const WEATHER_CONFIG: Record<WeatherCondition, {
    envPreset: "sunset" | "dawn" | "night" | "warehouse" | "forest" | "apartment" | "studio" | "city" | "park" | "lobby";
    transmission: number;
    roughness: number;
}> = {
    sunny: { envPreset: "sunset", transmission: 0.95, roughness: 0.05 },
    rainy: { envPreset: "city", transmission: 0.98, roughness: 0.15 },
    overcast: { envPreset: "studio", transmission: 0.92, roughness: 0.2 }
};

export const TIME_CONFIG: Record<TimeOfDay, {
    groundColor: string;
    lightColor: string;
    lightIntensity: number;
    coreColorHigh: string;
    coreColorLow: string;
    glassColor: string;
}> = {
    morning: {
        groundColor: "#FFDAB9", lightColor: "#FF8C00", lightIntensity: 1.8,
        coreColorHigh: "#FFA500", coreColorLow: "#FF4500", glassColor: "#FFEBCD"
    },
    afternoon: {
        groundColor: "#87CEEB", lightColor: "#FFFFFF", lightIntensity: 2.0,
        coreColorHigh: "#E0FFFF", coreColorLow: "#00BFFF", glassColor: "#F0F8FF"
    },
    night: {
        groundColor: "#0F172A", lightColor: "#818CF8", lightIntensity: 0.8,
        coreColorHigh: "#A5B4FC", coreColorLow: "#312E81", glassColor: "#1E293B"
    }
};

export const ASAM_DIMENSIONS = [
    { id: 1, name: "Intoxication/Withdrawal", short: "Acute" },
    { id: 2, name: "Biomedical Conditions", short: "Biomed" },
    { id: 3, name: "Emotional/Behavioral", short: "Psych" },
    { id: 4, name: "Readiness to Change", short: "Change" },
    { id: 5, name: "Relapse Potential", short: "Relapse" },
    { id: 6, name: "Recovery Environment", short: "Env" }
];

export const MODE_CONFIG: Record<'clinical' | 'technical', {
    coreColorHigh: string;
    coreColorLow: string;
    glassColor: string;
}> = {
    clinical: {
        coreColorHigh: '#ffaa00',  // Warm amber
        coreColorLow: '#442200',   // Deep amber
        glassColor: '#ffcc66',     // Light amber glass
    },
    technical: {
        coreColorHigh: '#00aaff',  // Electric blue
        coreColorLow: '#002244',   // Deep blue
        glassColor: '#66ccff',     // Light blue glass
    }
};

/**
 * Voice State Configuration for Sphere UI
 * Per Mission 10: Distinct colors for each interaction state
 * 
 * - idle/listening: Deep Blue (Calm, waiting)
 * - thinking: Amber (Processing, computing)
 * - speaking: Emerald Green (Active, responding)
 */
export type VoiceState = 'idle' | 'listening' | 'thinking' | 'speaking';

export const VOICE_STATE_CONFIG: Record<VoiceState, {
    coreColorHigh: string;
    coreColorLow: string;
    glassColor: string;
    pulseSpeed: number;  // Animation speed multiplier
    intensity: number;   // Glow intensity
}> = {
    idle: {
        coreColorHigh: '#3B82F6',  // Blue-500 - Calm blue
        coreColorLow: '#1E3A8A',   // Blue-900 - Deep blue
        glassColor: '#60A5FA',     // Blue-400 - Light blue glass
        pulseSpeed: 0.5,
        intensity: 0.3
    },
    listening: {
        coreColorHigh: '#2563EB',  // Blue-600 - Slightly brighter blue
        coreColorLow: '#1E40AF',   // Blue-800 - Deep listening blue
        glassColor: '#93C5FD',     // Blue-300 - Attentive glow
        pulseSpeed: 0.8,
        intensity: 0.5
    },
    thinking: {
        coreColorHigh: '#F59E0B',  // Amber-500 - Processing amber
        coreColorLow: '#92400E',   // Amber-800 - Deep amber
        glassColor: '#FCD34D',     // Amber-300 - Warm thinking glow
        pulseSpeed: 1.5,
        intensity: 0.7
    },
    speaking: {
        coreColorHigh: '#10B981',  // Emerald-500 - Active green
        coreColorLow: '#065F46',   // Emerald-800 - Deep emerald
        glassColor: '#6EE7B7',     // Emerald-300 - Vibrant response glow
        pulseSpeed: 1.0,
        intensity: 0.8
    }
};
