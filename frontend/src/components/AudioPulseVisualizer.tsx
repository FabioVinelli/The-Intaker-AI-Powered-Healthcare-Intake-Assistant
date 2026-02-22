import React, { useRef, useEffect } from 'react';
import { cn } from '../lib/utils';

interface AudioPulseVisualizerProps {
    stream?: MediaStream | null;
    frequencyData?: Uint8Array;
    mode: 'listening' | 'speaking' | 'idle' | 'processing';
    onSuccessRipple?: boolean; // Prop to trigger ripple effect
}

export const AudioPulseVisualizer: React.FC<AudioPulseVisualizerProps> = ({
    stream,
    frequencyData,
    mode,
    onSuccessRipple
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number>();
    const analyserRef = useRef<AnalyserNode | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

    // Initialize Audio Context for Input Stream
    useEffect(() => {
        if (!stream) return;

        try {
            const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
            const ctx = new AudioContext();
            audioContextRef.current = ctx;

            const analyser = ctx.createAnalyser();
            analyser.fftSize = 256;
            analyserRef.current = analyser;

            const source = ctx.createMediaStreamSource(stream);
            source.connect(analyser);
            sourceRef.current = source;

        } catch (err) {
            console.error("Error visualizing audio stream:", err);
        }

        return () => {
            sourceRef.current?.disconnect();
            analyserRef.current?.disconnect();
            audioContextRef.current?.close();
        };
    }, [stream]);

    // Animation Loop
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const render = () => {
            const width = canvas.width;
            const height = canvas.height;
            const centerX = width / 2;
            const centerY = height / 2;

            ctx.clearRect(0, 0, width, height);

            // Determine 'energy' level from audio data
            let energy = 0;

            if (mode === 'speaking' && frequencyData) {
                // Use provided frequency data (from Gemini output)
                const dataArray = frequencyData;
                const average = dataArray.reduce((p, c) => p + c, 0) / dataArray.length;
                energy = average / 255;
            } else if (mode === 'listening' && analyserRef.current) {
                // Use local mic stream
                const bufferLength = analyserRef.current.frequencyBinCount;
                const dataArray = new Uint8Array(bufferLength);
                analyserRef.current.getByteFrequencyData(dataArray);
                const average = dataArray.reduce((p, c) => p + c, 0) / bufferLength;
                energy = average / 255;
            } else if (mode === 'processing') {
                // Throb effect
                energy = (Math.sin(Date.now() / 200) + 1) * 0.2 + 0.1;
            } else {
                // Idle pulse
                energy = (Math.sin(Date.now() / 1000) + 1) * 0.05;
            }

            // Scaling factors
            const baseRadius = 60;
            const maxScale = 1.8;
            const scale = 1 + energy * (maxScale - 1);

            // Draw Rings
            const drawRing = (radius: number, opacity: number, color: string) => {
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius * scale, 0, 2 * Math.PI);
                ctx.fillStyle = color;
                ctx.globalAlpha = opacity;
                ctx.fill();
                ctx.globalAlpha = 1.0;
            };

            // Outer glow
            drawRing(baseRadius * 1.5, 0.1 + energy * 0.2, '#A855F7'); // Purple-ish

            // Middle ring
            drawRing(baseRadius * 1.2, 0.2 + energy * 0.3, '#EC4899'); // Pink-ish

            // Core
            drawRing(baseRadius, 0.8, '#FFFFFF'); // White core

            // Ripple Effect (Success)
            if (onSuccessRipple) {
                // Simple ripple implementation could be expanded here
                // For now, we will just flash the outer ring green
                drawRing(baseRadius * 2, 0.3 * (Math.sin(Date.now() / 50) + 1), '#10B981');
            }

            animationRef.current = requestAnimationFrame(render);
        };

        render();

        return () => {
            if (animationRef.current) cancelAnimationFrame(animationRef.current);
        };
    }, [mode, frequencyData, onSuccessRipple]);

    return (
        <div className="relative w-full h-full flex items-center justify-center">
            <canvas
                ref={canvasRef}
                width={400}
                height={400}
                className="w-[400px] h-[400px]"
            />
        </div>
    );
};
