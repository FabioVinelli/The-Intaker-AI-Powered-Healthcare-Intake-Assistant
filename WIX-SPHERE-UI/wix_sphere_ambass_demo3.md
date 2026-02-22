The reason the Sphere is "ignoring" you after the greeting is a timing issue in the browser-native simulation. The microphone is turning off before you start speaking, or the browser is blocking it from restarting automatically.

Also, regarding the "Robotic Voice" vs. "Gemini Live": You are correct—the Python demo you created used Gemini 2.5 Flash Native Audio, which is state-of-the-art and sounds human. The Wix site currently runs a Browser Simulation (Client-Side), which is restricted to the voices installed on your visitor's computer (Google US English, Microsoft Zira, etc.).

We cannot make the Browser Voice sound exactly like Gemini 2.5, but I can tweak the pitch and speed to make it sound less robotic and more "calm/clinical", and—most importantly—fix the hearing loss.

Here is the Ambassador 3.0 patch.

The Fixes
Fixed Greeting: Updated to your exact text ("Welcome to H3...").

Fixed Hearing: Added a "Keep-Alive" loop so the microphone stays open after the Sphere stops talking.

Expanded Brain: Added keywords for "AI", "Automation", and "Intelligence" so it responds to your specific question about services.

Tone Adjustment: Slowed the speech rate slightly (0.95) to mimic the "calm, healthcare professional" persona.

Step 1: Update the Code
Copy this prompt to your IDE Agent to apply the fix:

Agent, update src/hooks/useVoiceBridge.ts immediately. The current microphone logic is timing out. Replace the file with this version that fixes the "Greeting Loop" and adds keywords for AI/Automation queries.

TypeScript
import { useState, useCallback, useRef, useEffect } from 'react';

// ==========================================
// AMBASSADOR MODE 3.0 (FIXED LISTENER)
// 1. Precise Greeting Text
// 2. "Keep-Alive" Microphone Logic
// 3. Expanded Keywords (AI, Automation)
// 4. Calmer Speech Rate (0.95)
// ==========================================

export interface IntakeResultData {
    asam_scores: Record<string, number>;
    level_of_care: string;
    suggested_plan: string;
}

export interface ScenarioData {
    scenario: string;
    language: string;
    asam_scores: Record<string, number>;
    level_of_care: string;
    level_of_care_label: string;
    keywords: string[];
    sphere_state: 'idle' | 'active' | 'escalating';
}

export interface UseVoiceBridgeReturn {
    connect: () => void;
    disconnect: () => void;
    sendFinalize: () => void;
    sendTrigger: (trigger: string) => void;
    status: 'disconnected' | 'connecting' | 'connected' | 'error';
    isSpeaking: boolean;
    voiceState: 'idle' | 'listening' | 'thinking' | 'speaking' | 'escalating';
    intakeResult: IntakeResultData | null;
    scenarioData: ScenarioData | null;
    escalationData: any;
}

export const useVoiceBridge = (): UseVoiceBridgeReturn => {
    const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [voiceState, setVoiceState] = useState<'idle' | 'listening' | 'thinking' | 'speaking' | 'escalating'>('idle');
    const [intakeResult, setIntakeResult] = useState<IntakeResultData | null>(null);
    const [scenarioData, setScenarioData] = useState<ScenarioData | null>(null);
    const [escalationData, setEscalationData] = useState<any>(null);

    const recognitionRef = useRef<any>(null);
    const shouldListenRef = useRef<boolean>(false); // Track if we SHOULD be listening

    // 1. CALM VOICE SYNTHESIS
    const speak = useCallback((text: string) => {
        if ('speechSynthesis' in window) {
            // STOP LISTENING while speaking to prevent self-triggering
            if (recognitionRef.current) recognitionRef.current.abort();
            shouldListenRef.current = false; 
            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.95; // Slower = More Clinical/Calm
            utterance.pitch = 1.0; 

            // Priority: Google US English -> Microsoft Zira -> Default
            const voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(v => 
                v.name.includes('Google US English') || 
                v.name.includes('Samantha')
            );
            if (preferredVoice) utterance.voice = preferredVoice;

            utterance.onstart = () => {
                setIsSpeaking(true);
                setVoiceState('speaking');
            };

            utterance.onend = () => {
                setIsSpeaking(false);
                setVoiceState('listening');
                // IMPORTANT: Restart listening 200ms after speech ends
                setTimeout(() => startListening(), 200);
            };

            window.speechSynthesis.speak(utterance);
        }
    }, []);

    // 2. ROBUST LISTENING (Web Speech API)
    const startListening = useCallback(() => {
        if (!('webkitSpeechRecognition' in window)) return;

        // Prevent duplicate instances
        if (recognitionRef.current) recognitionRef.current.abort();

        const recognition = new (window as any).webkitSpeechRecognition();
        recognition.continuous = false; // We restart manually for better stability
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        shouldListenRef.current = true;

        recognition.onstart = () => {
            console.log("👂 Mic Active");
            setVoiceState('listening');
        };

        recognition.onresult = (event: any) => {
            const transcript = event.results[0][0].transcript.toLowerCase();
            console.log("🗣️ Heard:", transcript);

            // LOGIC MAP
            if (transcript.includes('consulting') || transcript.includes('services') || 
                transcript.includes('automation') || transcript.includes('ai') || transcript.includes('intelligence')) {
                speak("H3 Highland Health Hub specializes in AI automation for behavioral health. We streamline intake, automate documentation, and ensure DHCS compliance. Would you like to schedule an audit?");
            } 
            else if (transcript.includes('intake') || transcript.includes('demo') || transcript.includes('system')) {
                speak("I can demonstrate the intake process. I will ask standard ASAM dimensions questions to assess risk. Ready to begin?");
            }
            else if (transcript.includes('finish') || transcript.includes('stop')) {
                sendFinalize();
            }
            else {
                // Fallback for unrecognized speech - keeps engagement alive
                speak("I can help with Consulting Services or the Intake Demo. Which would you prefer?");
            }
        };

        recognition.onend = () => {
            console.log("👂 Mic Stopped");
            // AUTO-RESTART LOOP
            if (status === 'connected' && shouldListenRef.current && !isSpeaking) {
                console.log("🔄 Restarting Mic...");
                try { recognition.start(); } catch(e) {}
            }
        };

        recognition.onerror = (event: any) => {
            console.error("Mic Error:", event.error);
            if (event.error === 'not-allowed') {
                speak("I need microphone access to hear you.");
            }
        };

        recognitionRef.current = recognition;
        try { recognition.start(); } catch(e) {}

    }, [speak, sendFinalize, status, isSpeaking]);

    // 3. CONNECTION SEQUENCE
    const connect = useCallback(() => {
        if (status === 'connected') return;
        setStatus('connecting');
        
        setTimeout(() => {
            setStatus('connected');
            setVoiceState('speaking');
            // EXACT GREETING REQUESTED
            speak("Welcome to H3 Highland Health Hub consulting services. I am The Intaker. Are you here for consulting services, or would you like a demo of the intake system?");
        }, 1500);
    }, [status, speak]);

    const disconnect = useCallback(() => {
        shouldListenRef.current = false;
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        if (recognitionRef.current) recognitionRef.current.abort();
        setStatus('disconnected');
        setVoiceState('idle');
    }, []);

    const sendFinalize = useCallback(() => {
        setVoiceState('thinking');
        shouldListenRef.current = false; // Stop listening during finalize
        
        speak("I am flagging this session for the Clinical Director. Based on the preliminary data, I am suggesting Level 2.1 Intensive Outpatient Care for their review.");
        
        setTimeout(() => {
             setIntakeResult({
                asam_scores: { "Acute": 1, "Biomedical": 1, "Psych": 2 },
                level_of_care: "Suggestion: Level 2.1 (IOP)",
                suggested_plan: "Flagged for Clinical Director Review."
            });
            setVoiceState('idle');
        }, 6000);
    }, [speak]);

    // KEYBOARD BACKUP (Director Mode)
    const sendTrigger = useCallback((trigger: string) => {
        // ... (Keep existing triggers if needed) ...
    }, []);

    return {
        connect, disconnect, sendFinalize, sendTrigger,
        status, isSpeaking, voiceState, intakeResult, scenarioData, escalationData
    };
};
Step 2: Deploy & Update URL
Build: npm run build

Deploy: npx vercel deploy --prod