import React, { useState } from 'react';
import { 
  X, 
  Check, 
  Copy, 
  Layers, 
  BookOpen, 
  FileText,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

export default function CitationDrawer({ isOpen, onClose, sources, retrievalTime }) {
  const [copiedIndex, setCopiedIndex] = useState(null);

  if (!isOpen) return null;

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs animate-fade-in">
      <div className="w-full max-w-xl bg-white border-l border-slate-200 h-full flex flex-col shadow-2xl relative overflow-hidden">
        
        {/* Drawer Header */}
        <div className="px-6 py-4.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/90 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-2xs">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-slate-900">
                  Verified Source Citations
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                  Top 3 Cross-Attention
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5 font-normal">
                Retrieved in {retrievalTime ? `${retrievalTime}s` : 'sub-second'} via BM25 + Dense Reranking
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Sources List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {sources && sources.length > 0 ? (
            sources.map((src, i) => (
              <div
                key={src.chunk_id || i}
                className="p-4 rounded-xl border border-slate-200/90 bg-slate-50/40 hover:bg-white hover:border-indigo-300 transition-all duration-150 shadow-2xs group"
              >
                {/* Source Metadata Header */}
                <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-slate-200/70 text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="w-5 h-5 rounded-md bg-indigo-600 text-white flex items-center justify-center text-[10px] font-bold">
                      {i + 1}
                    </span>
                    <span className="font-bold text-slate-800">
                      Page {src.page_number || '1'}
                    </span>
                    <span className="text-slate-300">•</span>
                    <span className="text-slate-500 font-mono text-[11px] truncate max-w-[170px]">
                      {src.filename}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-[10px] px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200 font-bold">
                      Score: {src.score}
                    </span>
                    <button
                      onClick={() => handleCopy(src.text, i)}
                      title="Copy chunk text"
                      className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
                    >
                      {copiedIndex === i ? (
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Excerpt Body */}
                <div className="text-xs text-slate-700 leading-relaxed font-mono whitespace-pre-wrap bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs">
                  {src.text}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12 text-slate-400">
              <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-30 text-slate-400" />
              <p className="text-xs font-medium">No citations associated with this query.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 shrink-0 text-center text-[11px] text-slate-500 font-medium">
          Verified with <span className="font-semibold text-slate-800">Cross-Attention Precision Ranking</span>
        </div>
      </div>
    </div>
  );
}
