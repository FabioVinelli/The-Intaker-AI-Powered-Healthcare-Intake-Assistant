import React, { useState, useEffect, useRef } from 'react';
import { Experience } from './components/Experience';
import { useAudioAnalyzer } from './hooks/useAudioAnalyzer';
import { useVoiceBridge } from './hooks/useVoiceBridge';
import { IntakeResultPanel } from './components/IntakeResultPanel';
import { TimeOfDay, IntakeMode } from './types';
import { Mic, MicOff, CheckCircle, Clock } from 'lucide-react';

function App() {
  // Visual Audio Analyzer (for the Orb)
  const { isListening: isVisualListening, startListening: startVisuals, stopListening: stopVisuals, getFrequencyData } = useAudioAnalyzer();
  const [audioData, setAudioData] = useState({ average: 0, data: new Uint8Array(0) });

  // Voice Bridge (for Gemini Communication)
  const { connect, disconnect, sendFinalize, status: bridgeStatus, isSpeaking, intakeResult } = useVoiceBridge();

  const [mode, setMode] = useState<IntakeMode>('clinical');
  const [timeOfDay, setTimeOfDay] = useState<TimeOfDay>('morning');
  const [showPlan, setShowPlan] = useState(false);

  // Session Timer
  const [sessionSeconds, setSessionSeconds] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    let animationFrameId: number;
    const animate = () => {
      if (isVisualListening) {
        setAudioData(getFrequencyData());
      }
      animationFrameId = requestAnimationFrame(animate);
    };
    animate();
    return () => cancelAnimationFrame(animationFrameId);
  }, [isVisualListening, getFrequencyData]);

  // Timer logic
  useEffect(() => {
    if (bridgeStatus === 'connected') {
      setSessionSeconds(0);
      timerRef.current = setInterval(() => {
        setSessionSeconds(s => s + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [bridgeStatus]);

  useEffect(() => {
    if (intakeResult) {
      setShowPlan(true);
    }
  }, [intakeResult]);

  const [isHeld, setIsHeld] = useState(false);

  const handleStart = () => {
    startVisuals();
    connect();
  };

  const handleStop = () => {
    stopVisuals();
    disconnect();
    setIsHeld(false);
  };

  const toggleSession = () => {
    if (bridgeStatus === 'connected' || bridgeStatus === 'connecting') {
      handleStop();
    } else {
      handleStart();
    }
  };

  const toggleHold = () => {
    if (isHeld) {
      // Resume
      connect();
      setIsHeld(false);
    } else {
      // Hold
      setIsHeld(true);
      stopVisuals();
    }
  };

  const handleFinishIntake = () => {
    sendFinalize();
    // Optionally stop visuals but keep WS open for the result
    stopVisuals();
  };

  const handleTransfer = () => {
    setMode('technical');
    console.log("Transferring to clinical staff...");
  };

  const handleCloseResult = () => {
    setShowPlan(false);
    handleStop();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full h-screen bg-black relative overflow-hidden font-sans">
      {/* Experience Canvas */}
      <div className="absolute inset-0 z-0">
        <Experience
          weather="sunny"
          timeOfDay={timeOfDay}
          audioData={audioData}
          mode={mode}
          a2uiState={null}
          onA2UIAction={() => { }}
          showDimensions={bridgeStatus === 'connected'}
          voiceCommand={null}
          onPlaySound={() => { }}
        />
      </div>

      {/* Status Overlay */}
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
        <div className="bg-black/40 backdrop-blur-md text-white/80 px-4 py-2 rounded-lg border border-white/10 text-sm flex flex-col gap-1">
          <div className="flex items-center gap-3">
            <span>Status: <span className={bridgeStatus === 'connected' ? (intakeResult ? 'text-amber-400' : 'text-emerald-400') : 'text-amber-400'}>
              {bridgeStatus === 'connected' ? (intakeResult ? "PENDING REVIEW" : "ASSISTING") : bridgeStatus.toUpperCase()}
            </span></span>
            {bridgeStatus === 'connected' && !intakeResult && (
              <span className="flex items-center gap-1 text-white/60 border-l border-white/10 pl-3">
                <Clock size={14} />
                {formatTime(sessionSeconds)}
              </span>
            )}
          </div>
          <div className="text-[10px] uppercase tracking-widest text-white/30 border-t border-white/5 pt-1 mt-1">
            AI Assistant • Clinician Supervised
          </div>
        </div>
        {isSpeaking && (
          <div className="bg-indigo-500/20 backdrop-blur-md text-indigo-300 px-4 py-2 rounded-lg border border-indigo-500/30 text-sm animate-pulse">
            Gemini Speaking...
          </div>
        )}
      </div>

      {/* Control Bar */}
      <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 z-50 flex items-center gap-6">

        {/* Hold / Escalate Group */}
        <div className="flex flex-col gap-2 items-center">
          {isHeld ? (
            <button
              onClick={handleTransfer}
              className="bg-sky-400/80 hover:bg-sky-500 text-white px-6 py-3 rounded-full font-medium transition-all shadow-lg backdrop-blur-md border border-sky-300/30 tracking-wider"
            >
              TRANSFERRING
            </button>
          ) : (
            <button
              onClick={toggleHold}
              disabled={bridgeStatus !== 'connected'}
              className={`px-6 py-3 rounded-full font-medium transition-all shadow-lg backdrop-blur-md border border-white/10 ${bridgeStatus === 'connected' ? 'bg-white/10 text-white hover:bg-white/20' : 'bg-white/5 text-white/30 cursor-not-allowed'}`}
            >
              HOLD
            </button>
          )}
        </div>

        {/* Main Mic Button */}
        <div className="relative group">
          <div className={`absolute inset-0 rounded-full blur-xl transition-opacity duration-500 ${bridgeStatus === 'connected' ? 'bg-blue-500/40 opacity-100' : 'bg-white/10 opacity-0 group-hover:opacity-50'}`} />
          <button
            onClick={toggleSession}
            className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 border ${bridgeStatus === 'connected' ? 'bg-white text-black border-white shadow-[0_0_30px_rgba(255,255,255,0.3)] scale-110' : 'bg-black/50 text-white border-white/20 hover:bg-white/10 hover:border-white/50'}`}
          >
            {bridgeStatus === 'connected' ? (
              isHeld ? <MicOff size={32} className="text-gray-400" /> : <div className="w-8 h-8 bg-black rounded-sm animate-pulse" />
            ) : (
              <Mic size={32} />
            )}
          </button>
        </div>

        {/* Finish Intake Button */}
        <button
          onClick={handleFinishIntake}
          disabled={bridgeStatus !== 'connected'}
          className={`flex items-center gap-2 px-6 py-3 rounded-full font-medium transition-all shadow-lg backdrop-blur-md border ${bridgeStatus === 'connected' ? 'bg-emerald-500/80 hover:bg-emerald-600 text-white border-emerald-400/30' : 'bg-white/5 text-white/30 cursor-not-allowed border-white/10'}`}
        >
          <CheckCircle size={18} />
          FINISH
        </button>

        {/* Mode Toggle (Secondary) */}
        <button
          onClick={() => setMode(m => m === 'clinical' ? 'technical' : 'clinical')}
          className="w-12 h-12 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-white/50 hover:text-white transition-all backdrop-blur-md"
          title="Toggle Clinical/Technical Mode"
        >
          <div className={`w-3 h-3 rounded-full ${mode === 'clinical' ? 'bg-amber-400' : 'bg-blue-400'} shadow-[0_0_10px_currentColor]`} />
        </button>
      </div>

      {/* Intake Result Panel */}
      {showPlan && intakeResult && (
        <IntakeResultPanel
          result={intakeResult}
          onClose={handleCloseResult}
        />
      )}
    </div>
  );
}

export default App;