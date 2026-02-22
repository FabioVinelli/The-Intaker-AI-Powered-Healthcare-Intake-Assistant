import { useState, useEffect, useRef, useCallback } from 'react';
import { ASAM_INTAKE_SCRIPT } from '../data/intakeScript';

// Configuration for audio streaming
const SAMPLE_RATE = 24000; // Gemini often uses 24k or 16k
const BUFFER_SIZE = 4096;

/**
 * Audio constraints with Echo Cancellation, Noise Suppression, and Auto Gain Control
 * These settings prevent the feedback loop where the AI's audio gets captured by the mic.
 * 
 * Per Mission 11: Explicitly enable hardware AEC to eliminate audio feedback loops.
 */
const AUDIO_CONSTRAINTS: MediaTrackConstraints = {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
    sampleRate: 16000,
    channelCount: 1
};

export type GeminiConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';

interface UseGeminiLiveProps {
    onAudioData?: (data: Uint8Array) => void; // For visualization
    onText?: (text: string) => void;          // For subtitles
    onA2UI?: (tag: string) => void;           // For A2UI widget triggers
}

export const useGeminiLive = ({ onAudioData, onText, onA2UI }: UseGeminiLiveProps) => {
    const [state, setState] = useState<GeminiConnectionState>('disconnected');
    const [isRecording, setIsRecording] = useState(false);

    const wsRef = useRef<WebSocket | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const workletNodeRef = useRef<AudioWorkletNode | null>(null);
    const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const streamRef = useRef<MediaStream | null>(null);

    // Queue for incoming audio to play
    const audioQueueRef = useRef<Int16Array[]>([]);
    const isPlayingRef = useRef(false);
    const nextStartTimeRef = useRef<number>(0);

    // Initialize Audio Context
    const ensureAudioContext = useCallback(() => {
        if (!audioContextRef.current) {
            const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
            audioContextRef.current = new AudioContext({ sampleRate: SAMPLE_RATE });
        } else if (audioContextRef.current.state === 'suspended') {
            audioContextRef.current.resume();
        }
    }, []);

    const connect = useCallback(() => {
        if (state === 'connected' || state === 'connecting') return;

        setState('connecting');
        ensureAudioContext();

        // In a real implementation, this would be your backend proxy or direct Vertex endpoint
        // For this prototype, we'll assume a local proxy at ws://localhost:8000/api/v1/ws/live
        // or use a mock if connection fails.
        const PRODUCTION_BACKEND_URL = 'intaker-api-intaker-project-hrllc.a.run.app';
        const wsUrl = import.meta.env.PROD
            ? `wss://${PRODUCTION_BACKEND_URL}/api/v1/gemini-live`
            : `wss://${window.location.host}/api/v1/gemini-live`;
        // Constructing URL based on current host for Cloud Run compatibility
        // If local dev, it might need adjustment.

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('Gemini Live WebSocket Connected');
            setState('connected');

            // Send Initial Setup / System Instruction
            const setupMessage = {
                setup: {
                    model: "models/gemini-2.0-flash-exp", // Example model
                    system_instruction: {
                        parts: [{ text: ASAM_INTAKE_SCRIPT }]
                    }
                }
            };
            ws.send(JSON.stringify(setupMessage));
        };

        ws.onmessage = async (event) => {
            try {
                const data = JSON.parse(event.data);

                // Handle Audio Response
                if (data.serverContent?.modelTurn?.parts) {
                    for (const part of data.serverContent.modelTurn.parts) {
                        if (part.inlineData) {
                            // Audio Data (Base64)
                            const audioData = base64ToPCM(part.inlineData.data);
                            queueAudio(audioData);
                            // Also send to visualizer (approximate)
                            if (onAudioData) {
                                // Create a fake frequency bucket for visualizer (since we have PCM)
                                const vizData = new Uint8Array(256).fill(100); // Mock viz data for now
                                onAudioData(vizData);
                            }
                        } else if (part.text) {
                            // Text Data (Subtitles)
                            if (onText) onText(part.text);

                            // Check for A2UI tags
                            const a2uiMatch = part.text.match(/<a2ui>(.*?)<\/a2ui>/);
                            if (a2uiMatch && onA2UI) {
                                onA2UI(a2uiMatch[1]);
                            }
                        }
                    }
                }

                // Handle Turn Complete (useful for clearing cues)
                if (data.serverContent?.turnComplete) {
                    // console.log("Turn complete");
                }

            } catch (err) {
                console.error("Error parsing WS message", err);
            }
        };

        ws.onerror = (error) => {
            console.error("WebSocket Error", error);
            setState('error');
        };

        ws.onclose = () => {
            console.log("WebSocket Closed");
            setState('disconnected');
        };

    }, [onA2UI, onText, onAudioData, state, ensureAudioContext]);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        stopRecording();
        setState('disconnected');
    }, []);

    const startRecording = useCallback(async () => {
        ensureAudioContext();
        if (!audioContextRef.current) return;

        try {
            // Request microphone with explicit AEC/Noise Suppression constraints
            // This is the critical fix for the feedback loop issue
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: AUDIO_CONSTRAINTS
            });
            streamRef.current = stream;
            setIsRecording(true);

            const source = audioContextRef.current.createMediaStreamSource(stream);
            sourceNodeRef.current = source;

            // Use ScriptProcessor for simplicity in prototype (AudioWorklet is better for prod)
            // 4096 buffer size, 1 channel input, 1 channel output
            const scriptNode = audioContextRef.current.createScriptProcessor(4096, 1, 1);

            scriptNode.onaudioprocess = (audioProcessingEvent) => {
                if (wsRef.current?.readyState !== WebSocket.OPEN) return;

                const inputBuffer = audioProcessingEvent.inputBuffer;
                const inputData = inputBuffer.getChannelData(0);

                // Downsample/Convert to PCM16 if needed, or send as float32
                // Gemini often expects PCM16 LE, 16k or 24k
                const pcm16 = floatTo16BitPCM(inputData);

                // Send to WS
                // Protocol depends on backend. Assuming standard Gemini Live chunks.
                const message = {
                    realtime_input: {
                        media_chunks: [{
                            mime_type: "audio/pcm;rate=24000",
                            data: arrayBufferToBase64(pcm16.buffer)
                        }]
                    }
                };
                wsRef.current.send(JSON.stringify(message));
            };

            source.connect(scriptNode);

            // Connect to a silent gain node to keep the processor alive
            // This prevents the mic audio from being output to speakers (avoiding echo)
            const silentGain = audioContextRef.current.createGain();
            silentGain.gain.value = 0; // Silent - no output to speakers
            scriptNode.connect(silentGain);
            silentGain.connect(audioContextRef.current.destination);

            console.log('🎤 Audio stream started with AEC enabled:', {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            });

        } catch (err) {
            console.error("Error accessing microphone", err);
            setIsRecording(false);
        }
    }, [ensureAudioContext]);

    const stopRecording = useCallback(() => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        if (sourceNodeRef.current) {
            sourceNodeRef.current.disconnect();
            sourceNodeRef.current = null;
        }
        setIsRecording(false);
    }, []);

    // Audio Playback Logic
    const queueAudio = (pcmData: Int16Array) => {
        audioQueueRef.current.push(pcmData);
        if (!isPlayingRef.current) {
            playNextChunk();
        }
    };

    const playNextChunk = () => {
        if (audioQueueRef.current.length === 0 || !audioContextRef.current) {
            isPlayingRef.current = false;
            return;
        }

        isPlayingRef.current = true;
        const pcmData = audioQueueRef.current.shift()!;

        // Create AudioBuffer
        const buffer = audioContextRef.current.createBuffer(1, pcmData.length, SAMPLE_RATE);
        const channelData = buffer.getChannelData(0);

        // Convert Int16 to Float32
        for (let i = 0; i < pcmData.length; i++) {
            channelData[i] = pcmData[i] / 32768.0;
        }

        const source = audioContextRef.current.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContextRef.current.destination);

        // Schedule
        const currentTime = audioContextRef.current.currentTime;
        // Basic scheduler: play immediately after previous, or now if lagged
        if (nextStartTimeRef.current < currentTime) {
            nextStartTimeRef.current = currentTime;
        }
        source.start(nextStartTimeRef.current);
        nextStartTimeRef.current += buffer.duration;

        source.onended = () => {
            playNextChunk();
        };
    };

    // Helper utils
    const floatTo16BitPCM = (input: Float32Array): Int16Array => {
        const output = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            const s = Math.max(-1, Math.min(1, input[i]));
            output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return output;
    };

    const base64ToPCM = (base64: string): Int16Array => {
        const binaryString = window.atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return new Int16Array(bytes.buffer);
    };

    const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    };

    return {
        state,
        isRecording,
        connect,
        disconnect,
        startRecording,
        stopRecording,
        stream: streamRef.current // Expose stream for visualizer
    };
};
