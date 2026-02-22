import { useState, useRef, useCallback, useEffect } from 'react';

export interface IntakeResultData {
    asam_scores: Record<string, number>;
    level_of_care: string;
    suggested_plan: string;
}

export interface UseVoiceBridgeReturn {
    connect: () => void;
    disconnect: () => void;
    sendFinalize: () => void;
    status: 'disconnected' | 'connecting' | 'connected' | 'error';
    isSpeaking: boolean;
    intakeResult: IntakeResultData | null;
}

/**
 * Audio constraints with Echo Cancellation, Noise Suppression, and Auto Gain Control
 * These settings help hardware-level processing to prevent feedback.
 */
const AUDIO_CONSTRAINTS: MediaTrackConstraints = {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
    sampleRate: 16000,
    channelCount: 1
};

export const useVoiceBridge = (): UseVoiceBridgeReturn => {
    const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [intakeResult, setIntakeResult] = useState<IntakeResultData | null>(null);

    const wsRef = useRef<WebSocket | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const processorRef = useRef<ScriptProcessorNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const nextStartTimeRef = useRef(0);

    // MISSION 12: The "Walkie-Talkie" Gate
    // This ref acts as a hardware-level gate to prevent digital feedback/crosstalk.
    const playbackActiveRef = useRef(false);

    // Separate gain node for playback
    const playbackGainRef = useRef<GainNode | null>(null);

    const processAudio = (inputData: Float32Array) => {
        // MISSION 12: HARD GATE
        // If the AI is talking (playback is active), send ABSOLUTELY NOTHING.
        // This eliminates digital loopback where the system captures its own output.
        if (playbackActiveRef.current) {
            return; // Drop packet. Absolute silence sent to backend.
        }

        // Downsample to 16kHz
        const targetSampleRate = 16000;
        const sampleRate = audioContextRef.current?.sampleRate || 44100;
        const ratio = sampleRate / targetSampleRate;
        const newLength = Math.floor(inputData.length / ratio);
        const result = new Int16Array(newLength);

        for (let i = 0; i < newLength; i++) {
            const offset = Math.floor(i * ratio);
            const s = Math.max(-1, Math.min(1, inputData[offset]));
            result[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(result.buffer);
        }
    };

    const playAudioChunk = async (data: ArrayBuffer) => {
        const audioCtx = audioContextRef.current;
        if (!audioCtx) return;

        // Set playback active immediately when receiving AI data
        playbackActiveRef.current = true;
        setIsSpeaking(true);

        const playbackRate = 24000;
        const int16Array = new Int16Array(data);
        const float32Array = new Float32Array(int16Array.length);
        for (let i = 0; i < int16Array.length; i++) {
            float32Array[i] = int16Array[i] / 32768.0;
        }

        const buffer = audioCtx.createBuffer(1, float32Array.length, playbackRate);
        buffer.getChannelData(0).set(float32Array);

        const source = audioCtx.createBufferSource();
        source.buffer = buffer;

        if (!playbackGainRef.current) {
            playbackGainRef.current = audioCtx.createGain();
            playbackGainRef.current.gain.value = 1.0;
            playbackGainRef.current.connect(audioCtx.destination);
        }
        source.connect(playbackGainRef.current);

        const now = audioCtx.currentTime;
        const startTime = Math.max(now, nextStartTimeRef.current);
        source.start(startTime);
        nextStartTimeRef.current = startTime + buffer.duration;

        source.onended = () => {
            // Only release the gate if we've reached the end of the current scheduled playback
            // Add a small 100ms buffer to ensure final samples are processed
            if (audioCtx.currentTime >= nextStartTimeRef.current - 0.1) {
                playbackActiveRef.current = false;
                setIsSpeaking(false);
            }
        };
    };

    const startStream = async () => {
        try {
            if (audioContextRef.current) {
                await audioContextRef.current.resume();
                return;
            }

            const stream = await navigator.mediaDevices.getUserMedia({
                audio: AUDIO_CONSTRAINTS
            });
            streamRef.current = stream;

            // MISSION 12: Device Selection Logging
            // Log the actual device label to verify browser isn't using a "Virtual Cable" or "System Mixer"
            const audioTrack = stream.getAudioTracks()[0];
            if (audioTrack) {
                console.log(`🎤 Using Microphone: [${audioTrack.label}]`);
            }

            const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
            audioContextRef.current = audioCtx;

            const source = audioCtx.createMediaStreamSource(stream);
            sourceRef.current = source;

            const processor = audioCtx.createScriptProcessor(4096, 1, 1);
            processor.onaudioprocess = (e) => {
                const inputData = e.inputBuffer.getChannelData(0);
                processAudio(inputData);
            };

            source.connect(processor);

            const silentGain = audioCtx.createGain();
            silentGain.gain.value = 0;
            processor.connect(silentGain);
            silentGain.connect(audioCtx.destination);

            processorRef.current = processor;

        } catch (err) {
            console.error("Mic Error in Bridge", err);
            setStatus('error');
        }
    };

    const connect = useCallback(() => {
        if (status === 'connected' || status === 'connecting') return;
        setStatus('connecting');
        const ws = new WebSocket('ws://localhost:8000/ws/intake?token=test-token');
        ws.binaryType = 'arraybuffer';

        ws.onopen = () => {
            console.log("WebSocket connected");
            setStatus('connected');
            startStream();
        };

        ws.onmessage = async (event) => {
            if (event.data instanceof ArrayBuffer) {
                playAudioChunk(event.data);
            } else {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'intake_result' && msg.data) {
                        setIntakeResult({
                            asam_scores: msg.data.asam_scores || {},
                            level_of_care: msg.data.level_of_care || 'Undetermined',
                            suggested_plan: msg.data.suggested_plan || 'No plan generated.',
                        });
                    }
                } catch (e) {
                    console.log("Received text:", event.data);
                }
            }
        };

        ws.onclose = () => {
            console.log("WebSocket disconnected");
            setStatus('disconnected');
            stopRecording();
        };

        wsRef.current = ws;
    }, [status]);

    useEffect(() => {
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            stopRecording();
        };
    }, []);

    const stopRecording = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        if (sourceRef.current) {
            sourceRef.current.disconnect();
        }
        if (processorRef.current) {
            processorRef.current.disconnect();
        }
        if (playbackGainRef.current) {
            playbackGainRef.current.disconnect();
            playbackGainRef.current = null;
        }
        if (audioContextRef.current) {
            audioContextRef.current.close().catch(console.error);
        }
        sourceRef.current = null;
        processorRef.current = null;
        audioContextRef.current = null;
        setIsSpeaking(false);
        playbackActiveRef.current = false;
    };

    const sendFinalize = useCallback(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'finalize' }));
        }
    }, []);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        stopRecording();
        setStatus('disconnected');
    }, []);

    return { connect, disconnect, sendFinalize, status, isSpeaking, intakeResult };
};
