import { useEffect, useRef, useState, useCallback } from 'react';

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

export const useAudioAnalyzer = () => {
    const [isListening, setIsListening] = useState(false);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const dataArrayRef = useRef<Uint8Array | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const streamRef = useRef<MediaStream | null>(null);

    const startListening = useCallback(async () => {
        try {
            if (audioContextRef.current) return;

            // Request microphone with explicit AEC/Noise Suppression constraints
            // This ensures the analyzer is also using AEC-enabled audio
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: AUDIO_CONSTRAINTS
            });
            streamRef.current = stream;

            const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
            const analyser = audioContext.createAnalyser();

            analyser.fftSize = 256;
            const source = audioContext.createMediaStreamSource(stream);

            // Connect source to analyser for frequency data
            // Note: We do NOT connect analyser to destination to prevent echo
            source.connect(analyser);

            analyserRef.current = analyser;
            dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount);
            audioContextRef.current = audioContext;
            sourceRef.current = source;

            setIsListening(true);

            console.log('🎤 Audio analyzer started with AEC enabled:', {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            });
        } catch (err) {
            console.error("Error accessing microphone:", err);
            setIsListening(false);
        }
    }, []);

    const stopListening = useCallback(() => {
        // Stop all tracks on the media stream
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        if (sourceRef.current) sourceRef.current.disconnect();
        if (audioContextRef.current) audioContextRef.current.close();

        analyserRef.current = null;
        audioContextRef.current = null;
        sourceRef.current = null;
        setIsListening(false);
    }, []);

    const getFrequencyData = useCallback(() => {
        if (analyserRef.current && dataArrayRef.current) {
            analyserRef.current.getByteFrequencyData(dataArrayRef.current);
            let sum = 0;
            for (let i = 0; i < dataArrayRef.current.length; i++) {
                sum += dataArrayRef.current[i];
            }
            const average = sum / dataArrayRef.current.length;
            return { average, data: dataArrayRef.current };
        }
        return { average: 0, data: new Uint8Array(0) };
    }, []);

    useEffect(() => {
        return () => {
            stopListening();
        };
    }, [stopListening]);

    return { isListening, startListening, stopListening, getFrequencyData };
};
