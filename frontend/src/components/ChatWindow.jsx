import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Sparkles, 
  ShieldCheck, 
  Trash2, 
  Layers, 
  Zap, 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  BookOpen, 
  ArrowUp,
  FileSearch,
  CheckCircle,
  HelpCircle,
  Info
} from 'lucide-react';
import MessageItem from './MessageItem';
import { streamQuery } from '../services/api';
import { voiceEngine } from '../services/voice';

const HERO_PROMPT_CARDS = [
  {
    category: "SYNTHESIS",
    title: "Executive Summary",
    prompt: "Provide a structured executive summary of the core findings and main topics in this document.",
    icon: "⚡",
    badge: "Overview"
  },
  {
    category: "FACT EXTRACTION",
    title: "Key Specifications & Rules",
    prompt: "What are the exact technical specifications, operational rules, or numeric parameters listed?",
    icon: "🔍",
    badge: "Specifics"
  },
  {
    category: "PLAYBOOK / METHODOLOGY",
    title: "Core Framework & Steps",
    prompt: "Explain the main methodology, proposal prompts, or step-by-step procedures outlined in this document.",
    icon: "📋",
    badge: "Guidelines"
  },
  {
    category: "ZERO-HALLUCINATION TEST",
    title: "Out-of-Context Trap",
    prompt: "What is the secret recipe for chocolate pizza according to this document?",
    icon: "🛡️",
    badge: "Absence Rule"
  }
];

export default function ChatWindow({ activeDoc, onOpenCitations, activeDocName }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Welcome to DocuMind AI. I operate under strict mathematical fact-grounding: every claim is verified against your uploaded document via Cross-Encoder reranking. Ask me any question or click a suggestion below to begin.",
      sources: [],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isAutoVoiceEnabled, setIsAutoVoiceEnabled] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleClearHistory = () => {
    voiceEngine.stopSpeaking();
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `Chat session reset. Ready to answer questions on **${activeDocName}**.`,
        sources: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
    ]);
  };

  const handleToggleVoice = () => {
    if (isListening) {
      voiceEngine.stopListening();
      setIsListening(false);
    } else {
      setIsListening(true);
      voiceEngine.startListening(
        (transcript) => {
          setInputQuery(transcript);
        },
        (finalQuery) => {
          setIsListening(false);
          setInputQuery(finalQuery);
          if (finalQuery.trim()) {
            handleSend(finalQuery);
          }
        },
        () => {
          setIsListening(false);
        }
      );
    }
  };

  const handleSend = async (overrideQuery) => {
    const queryToSend = (overrideQuery || inputQuery).trim();
    if (!queryToSend || isStreaming) return;

    setInputQuery('');

    const userMessageId = `user_${Date.now()}`;
    const assistantMessageId = `ai_${Date.now()}`;
    const timeNow = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    setMessages((prev) => [
      ...prev,
      {
        id: userMessageId,
        role: 'user',
        content: queryToSend,
        timestamp: timeNow,
      },
      {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        sources: [],
        retrievalTime: null,
        isStreaming: true,
        timestamp: timeNow,
      }
    ]);

    setIsStreaming(true);

    try {
      let accumulatedAnswer = '';
      let verifiedSources = [];

      await streamQuery(
        queryToSend,
        activeDoc,
        (token) => {
          accumulatedAnswer += token;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: accumulatedAnswer }
                : msg
            )
          );
        },
        (sources, retrievalTime) => {
          verifiedSources = sources || [];
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    sources: verifiedSources,
                    retrievalTime: retrievalTime,
                  }
                : msg
            )
          );
        },
        () => {
          setIsStreaming(false);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, isStreaming: false }
                : msg
            )
          );

          if (isAutoVoiceEnabled && accumulatedAnswer) {
            voiceEngine.speakText(accumulatedAnswer);
          }
        }
      );
    } catch (err) {
      console.error('Chat query stream error:', err);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: `Error retrieving response: ${err.message}`,
                isStreaming: false,
              }
            : msg
        )
      );
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-full flex flex-col bg-white">
      
      {/* 1. Context Status Sub-Header */}
      <div className="h-11 px-4 sm:px-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/60 text-xs shrink-0 select-none">
        <div className="flex items-center space-x-2 text-slate-600 truncate pr-2">
          <BookOpen className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
          <span className="text-slate-400 font-medium">Active Knowledge Context:</span>
          <span className="font-bold text-slate-800 truncate">
            {activeDocName}
          </span>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => setIsAutoVoiceEnabled(!isAutoVoiceEnabled)}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
              isAutoVoiceEnabled
                ? 'bg-indigo-100 text-indigo-700'
                : 'text-slate-500 hover:text-slate-800 hover:bg-slate-200/50'
            }`}
            title="Auto-read aloud response"
          >
            {isAutoVoiceEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">Voice Speech</span>
          </button>

          <button
            onClick={handleClearHistory}
            className="flex items-center space-x-1 text-slate-400 hover:text-rose-600 text-[11px] font-medium transition-colors"
            title="Clear Chat History"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear Chat</span>
          </button>
        </div>
      </div>

      {/* 2. Messages Canvas */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        
        {/* Empty State Hero (shown when chat is new) */}
        {messages.length === 1 && (
          <div className="max-w-3xl mx-auto my-6 space-y-6">
            <div className="text-center space-y-2">
              <div className="w-11 h-11 rounded-2xl bg-indigo-50 text-indigo-600 border border-indigo-100 flex items-center justify-center mx-auto shadow-xs">
                <Sparkles className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                Grounded Document Intelligence
              </h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                Every claim is verified against your document via BM25 hybrid vector retrieval and Cross-Encoder reranking.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {HERO_PROMPT_CARDS.map((card, i) => (
                <div
                  key={i}
                  onClick={() => handleSend(card.prompt)}
                  className="p-4 rounded-xl border border-slate-200/90 bg-white hover:bg-indigo-50/30 hover:border-indigo-400 transition-all duration-200 cursor-pointer shadow-2xs group flex flex-col justify-between"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-base">{card.icon}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 font-semibold group-hover:bg-indigo-100 group-hover:text-indigo-700 transition-colors">
                      {card.badge}
                    </span>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-800 group-hover:text-indigo-900 transition-colors">
                      {card.title}
                    </h4>
                    <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                      {card.prompt}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Message Items */}
        {messages.map((msg) => (
          <MessageItem
            key={msg.id}
            message={msg}
            onOpenCitations={onOpenCitations}
          />
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* 3. Floating Modern Input Bar */}
      <div className="p-4 border-t border-slate-100 bg-white shrink-0">
        <div className="max-w-4xl mx-auto">
          <div className={`relative flex items-center bg-slate-50 border rounded-2xl transition-all duration-200 ${
            isListening 
              ? 'border-indigo-500 ring-4 ring-indigo-50 bg-indigo-50/40' 
              : 'border-slate-300/90 focus-within:border-indigo-500 focus-within:ring-4 focus-within:ring-indigo-50 focus-within:bg-white shadow-2xs'
          }`}>
            
            {/* Input field */}
            <textarea
              ref={inputRef}
              rows={1}
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isListening ? "Listening... speak now" : `Ask any question about ${activeDocName}...`}
              disabled={isStreaming}
              className="w-full bg-transparent text-slate-800 placeholder-slate-400 text-xs sm:text-sm pl-4.5 pr-24 py-3.5 focus:outline-none resize-none max-h-32"
            />

            {/* Action Buttons */}
            <div className="absolute right-2.5 flex items-center space-x-1.5">
              
              {/* Mic Speech Button */}
              <button
                type="button"
                onClick={handleToggleVoice}
                title={isListening ? "Stop Listening" : "Speak Query"}
                className={`p-2 rounded-xl transition-all ${
                  isListening
                    ? 'bg-rose-500 text-white animate-pulse'
                    : 'text-slate-400 hover:text-indigo-600 hover:bg-slate-200/60'
                }`}
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>

              {/* Send Button */}
              <button
                type="button"
                onClick={() => handleSend()}
                disabled={!inputQuery.trim() || isStreaming}
                className={`p-2 rounded-xl transition-all ${
                  inputQuery.trim() && !isStreaming
                    ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs'
                    : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                }`}
              >
                <ArrowUp className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 px-1">
            <span>Press <kbd className="px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-[10px] font-mono text-slate-600">Enter ↵</kbd> to query</span>
            <span className="font-mono text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Verified Citations Enabled
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
