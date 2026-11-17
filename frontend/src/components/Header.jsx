import React from 'react';
import { 
  ShieldCheck, 
  Cpu, 
  Database, 
  Layers, 
  Zap, 
  ChevronDown,
  BookOpen,
  PanelLeftClose,
  PanelLeft,
  Github,
  Sparkles,
  ExternalLink
} from 'lucide-react';

export default function Header({ 
  backendHealth, 
  activeDoc, 
  documents, 
  onSelectDoc, 
  isSidebarOpen, 
  onToggleSidebar 
}) {
  const isHealthy = backendHealth?.status === 'healthy';
  const selectedDocObj = documents?.find((d) => d.doc_id === activeDoc);

  return (
    <header className="h-15 border-b border-slate-200/80 bg-white/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between select-none relative z-30 shadow-xs">
      
      {/* Left: Brand & Sidebar Toggle */}
      <div className="flex items-center space-x-3.5">
        <button
          onClick={onToggleSidebar}
          title={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          className="p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100/80 transition-all border border-transparent hover:border-slate-200"
        >
          {isSidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeft className="w-4 h-4" />}
        </button>

        <div className="flex items-center space-x-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-700 flex items-center justify-center shadow-sm shadow-indigo-200 text-white font-bold">
            <ShieldCheck className="w-5 h-5" />
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-sm tracking-tight text-slate-900">
                DocuMind<span className="text-indigo-600">.ai</span>
              </span>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/80">
                Enterprise RAG
              </span>
              <span className="hidden md:inline-flex text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80 items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Zero-Hallucination
              </span>
            </div>
            <p className="text-[11px] text-slate-500 hidden sm:block font-normal">
              Verified Document Intelligence & Instant Fact Extraction
            </p>
          </div>
        </div>
      </div>

      {/* Right: Document Quick Selector & Actions */}
      <div className="flex items-center space-x-2.5">
        
        {/* Document Switcher Dropdown */}
        <div className="relative">
          <select
            value={activeDoc || ''}
            onChange={(e) => onSelectDoc(e.target.value)}
            className="appearance-none bg-slate-50 hover:bg-slate-100/80 border border-slate-200/90 text-slate-800 text-xs font-semibold rounded-xl pl-8 pr-8 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer max-w-[180px] sm:max-w-[260px] truncate transition-colors shadow-2xs"
          >
            {documents && documents.length > 0 ? (
              documents.map((doc) => (
                <option key={doc.doc_id} value={doc.doc_id}>
                  {doc.filename} ({doc.chunk_count || 0} chunks)
                </option>
              ))
            ) : (
              <option value="">No documents loaded</option>
            )}
          </select>
          <BookOpen className="w-3.5 h-3.5 text-indigo-600 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        {/* GitHub Project Pill */}
        <a
          href="https://github.com"
          target="_blank"
          rel="noreferrer"
          className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium transition-all shadow-xs"
        >
          <Github className="w-3.5 h-3.5" />
          <span>GitHub</span>
        </a>
      </div>
    </header>
  );
}
