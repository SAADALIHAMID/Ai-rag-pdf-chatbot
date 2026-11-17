import React, { useState } from 'react';
import { 
  User, 
  Bot, 
  Copy, 
  Check, 
  Layers, 
  Clock, 
  Volume2, 
  VolumeX,
  FileCheck,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { voiceEngine } from '../services/voice';

export default function MessageItem({ message, onOpenCitations }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const hasSources = message.sources && message.sources.length > 0;
  const [isSpeakingThis, setIsSpeakingThis] = useState(false);

  const handleCopy = () => {
    if (message?.content) {
      navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleToggleSpeak = () => {
    if (isSpeakingThis) {
      voiceEngine.stopSpeaking();
      setIsSpeakingThis(false);
    } else {
      voiceEngine.speakText(message.content, () => {
        setIsSpeakingThis(false);
      });
      setIsSpeakingThis(true);
    }
  };

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in-up group`}>
      <div className={`flex max-w-2xl lg:max-w-3xl space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
        
        {/* Avatar Badge */}
        <div className="shrink-0 mt-0.5">
          {isUser ? (
            <div className="w-8 h-8 rounded-xl bg-slate-900 text-white flex items-center justify-center shadow-xs font-semibold text-xs">
              <User className="w-4 h-4" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-700 text-white flex items-center justify-center shadow-xs">
              <Bot className="w-4 h-4" />
            </div>
          )}
        </div>

        {/* Message Content Bubble */}
        <div className="flex flex-col space-y-1.5 min-w-0">
          
          {/* Metadata Row */}
          <div className={`flex items-center space-x-2 text-[11px] ${isUser ? 'justify-end text-slate-400' : 'text-slate-500'}`}>
            <span className="font-bold text-slate-700">
              {isUser ? 'You' : 'DocuMind Verified AI'}
            </span>
            {message.timestamp && <span>{message.timestamp}</span>}
            {message.retrievalTime && (
              <span className="text-[10px] font-mono font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.2 rounded-md border border-indigo-200/70">
                {message.retrievalTime}s latency
              </span>
            )}
          </div>

          {/* Main Bubble Card */}
          <div
            className={`p-4 sm:p-5 rounded-2xl text-xs sm:text-sm leading-relaxed ${
              isUser
                ? 'bg-slate-900 text-white shadow-xs rounded-tr-xs'
                : 'bg-white text-slate-800 border border-slate-200/90 shadow-2xs rounded-tl-xs'
            }`}
          >
            {/* Answer Text */}
            <div className="whitespace-pre-wrap break-words prose prose-slate max-w-none text-xs sm:text-sm">
              {message.content ? (
                message.content
              ) : message.isStreaming ? (
                <div className="flex items-center space-x-2 py-1 text-slate-400 text-xs">
                  <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping" />
                  <span className="font-medium text-slate-500">Cross-referencing text chunks...</span>
                </div>
              ) : (
                <span className="text-slate-400 italic">No content</span>
              )}
            </div>

            {/* Citations Pill for AI Answers */}
            {!isUser && hasSources && (
              <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => onOpenCitations(message.sources, message.retrievalTime)}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs font-semibold transition-all shadow-2xs group"
                >
                  <FileCheck className="w-3.5 h-3.5 text-emerald-600 group-hover:scale-110 transition-transform" />
                  <span>Inspect {message.sources.length} Verified Sources</span>
                  <ExternalLink className="w-3 h-3 text-emerald-600 opacity-60 ml-0.5" />
                </button>

                {/* Actions: Copy & Audio */}
                <div className="flex items-center space-x-1 text-slate-400">
                  <button
                    onClick={handleToggleSpeak}
                    title={isSpeakingThis ? "Stop audio" : "Read aloud"}
                    className="p-1.5 rounded-lg hover:text-slate-700 hover:bg-slate-100 transition-colors"
                  >
                    {isSpeakingThis ? <VolumeX className="w-3.5 h-3.5 text-indigo-600" /> : <Volume2 className="w-3.5 h-3.5" />}
                  </button>
                  <button
                    onClick={handleCopy}
                    title="Copy response"
                    className="p-1.5 rounded-lg hover:text-slate-700 hover:bg-slate-100 transition-colors"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
