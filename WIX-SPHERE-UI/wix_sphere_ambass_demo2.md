Agent, update src/hooks/useVoiceBridge.ts with this "Smart Ambassador" logic. It enables microphone listening, selects a better voice, and enforces non-diagnostic compliance scripts.

TypeScript
import { useState, useCallback, useRef, useEffect } from 'react';

// ==========================================
// AMBASSADOR MODE 2.0 (SMART LISTENING)
// Features:
// 1. Compliance: Never gives diagnosis, only "Clinical Suggestions"
// 2. Voice: Auto-selects "Google US English" or Premium voices
// 3. Hearing: Uses Web Speech API to trigger responses by voice
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

    // 1. SMART VOICE SELECTION
    const speak = useCallback((text: string) => {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel(); // Stop any previous speech

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.05; // Slightly faster is more natural
            utterance.pitch = 1.0;

            // Find the best voice (Priority: Google US English -> Microsoft Zira -> Default)
            const voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(v => 
                v.name.includes('Google US English') || 
                v.name.includes('Samantha') || 
                v.name.includes('Premium')
            );
            
            if (preferredVoice) {
                utterance.voice = preferredVoice;
                console.log("🗣️ Using Voice:", preferredVoice.name);
            }

            utterance.onstart = () => {
                setIsSpeaking(true);
                setVoiceState('speaking');
            };

            utterance.onend = () => {
                setIsSpeaking(false);
                setVoiceState('listening');
                // Resume listening after speaking
                if (status === 'connected') startListening(); 
            };

            window.speechSynthesis.speak(utterance);
        }
    }, [status]);

    // 2. SMART LISTENING (Web Speech API)
    const startListening = useCallback(() => {
        if (!('webkitSpeechRecognition' in window)) return;

        if (recognitionRef.current) recognitionRef.current.abort();

        const recognition = new (window as any).webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onresult = (event: any) => {
            const transcript = event.results[0][0].transcript.toLowerCase();
            console.log("👂 Heard:", transcript);

            // KEYWORD LOGIC
            if (transcript.includes('consulting') || transcript.includes('services') || transcript.includes('h3') || transcript.includes('help')) {
                speak("H3 Highland Health Hub specializes in DHCS licensing, JCAHO accreditation, and AI automation for behavioral health clinics. Would you like to schedule an audit?");
            } 
            else if (transcript.includes('intake') || transcript.includes('demo') || transcript.includes('start') || transcript.includes('simulation')) {
                speak("I can demonstrate the intake process. I will ask standard ASAM dimensions questions. Ready to begin?");
            }
            else if (transcript.includes('finish') || transcript.includes('stop') || transcript.includes('done')) {
                sendFinalize();
            }
        };

        recognition.onend = () => {
            // Restart listening if still connected and not speaking
            if (status === 'connected' && !isSpeaking) {
                try { recognition.start(); } catch(e) {}
            }
        };

        recognitionRef.current = recognition;
        try { recognition.start(); } catch(e) {}

    }, [speak, sendFinalize, status, isSpeaking]);

    // 3. CONNECT
    const connect = useCallback(() => {
        if (status === 'connected') return;
        setStatus('connecting');
        
        setTimeout(() => {
            setStatus('connected');
            setVoiceState('speaking');
            speak("Welcome to H3 Highland Health Hub. I am The Intaker. Are you here for Consulting Services, or would you like a demo of the Intake System?");
        }, 1500);
    }, [status, speak]);

    const disconnect = useCallback(() => {
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        if (recognitionRef.current) recognitionRef.current.abort();
        setStatus('disconnected');
        setVoiceState('idle');
    }, []);

    // 4. COMPLIANCE-SAFE FINALIZE
    const sendFinalize = useCallback(() => {
        setVoiceState('thinking');
        
        // COMPLIANCE FIX: Explicitly state this is for "Clinical Staff" review
        speak("I have gathered the necessary data. I am generating a summary for the Clinical Director to review. Based on the preliminary ASAM criteria, I am suggesting Level 2.1 Intensive Outpatient Care for their approval.");
        
        setTimeout(() => {
             setIntakeResult({
                asam_scores: { "Acute": 1, "Biomedical": 1, "Psych": 2 },
                level_of_care: "Suggestion: Level 2.1 (IOP)",
                suggested_plan: "Flagged for Clinical Director Review. Preliminary scoring suggests IOP necessity."
            });
            setVoiceState('idle');
        }, 4000); // Wait for speech to finish
    }, [speak]);

    // KEYBOARD BACKUP (Director Mode)
    const sendTrigger = useCallback((trigger: string) => {
        switch(trigger) {
            case '1': speak("Welcome to H3 Highland Health Hub..."); break;
            case '2': speak("H3 offers comprehensive services including DHCS licensing and AI automation..."); break;
            case '3': speak("Let's simulate an intake. I'll need to ask you a few questions..."); break;
            case '4': speak("I am designed to be a HIPAA compliant assistant..."); break;
            case '5': 
                setVoiceState('escalating');
                speak("I am detecting a safety risk. Transferring to a counselor immediately.");
                break;
        }
    }, [speak]);

    return {
        connect,
        disconnect,
        sendFinalize,
        sendTrigger,
        status,
        isSpeaking,
        voiceState,
        intakeResult,
        scenarioData,
        escalationData
    };
};
3. Deployment Steps
Run the Update: Paste the prompt above into your IDE.

Build & Deploy:

Bash
npm run build
npx vercel deploy --prod