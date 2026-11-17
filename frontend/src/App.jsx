import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import FileUploader from './components/FileUploader';
import ChatWindow from './components/ChatWindow';
import CitationDrawer from './components/CitationDrawer';
import { initSession, checkHealth, fetchDocuments } from './services/api';

export default function App() {
  const [backendHealth, setBackendHealth] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [activeDoc, setActiveDoc] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [citationModal, setCitationModal] = useState({
    isOpen: false,
    sources: [],
    retrievalTime: null,
  });

  const loadInitialData = async () => {
    await initSession();
    const health = await checkHealth();
    setBackendHealth(health);

    const docsResp = await fetchDocuments();
    setDocuments(docsResp.documents || []);
    if (docsResp.documents && docsResp.documents.length > 0) {
      setActiveDoc((prev) => prev || docsResp.documents[0].doc_id);
    }
  };

  useEffect(() => {
    loadInitialData();
    const interval = setInterval(async () => {
      const health = await checkHealth();
      setBackendHealth(health);
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleUploadComplete = async (uploadResult) => {
    const docsResp = await fetchDocuments();
    setDocuments(docsResp.documents || []);
    if (uploadResult.doc_id) {
      setActiveDoc(uploadResult.doc_id);
    }
  };

  const handleOpenCitations = (sources, retrievalTime) => {
    setCitationModal({
      isOpen: true,
      sources: sources || [],
      retrievalTime,
    });
  };

  const handleCloseCitations = () => {
    setCitationModal({
      isOpen: false,
      sources: [],
      retrievalTime: null,
    });
  };

  const activeDocObj = Array.isArray(documents)
    ? documents.find((d) => d && d.doc_id === activeDoc)
    : null;

  return (
    <div className="h-screen w-screen bg-slate-50 text-slate-900 flex flex-col overflow-hidden relative font-sans bg-grid-pattern selection:bg-indigo-500 selection:text-white">
      
      {/* Ambient Top Glow Atmosphere */}
      <div className="ambient-glow" />

      {/* Top Telemetry Header */}
      <Header
        backendHealth={backendHealth}
        activeDoc={activeDoc}
        documents={documents}
        onSelectDoc={setActiveDoc}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      {/* Main Full-Viewport Workstation Area */}
      <div className="flex-1 flex overflow-hidden p-3 sm:p-4 gap-3.5 relative z-10">
        
        {/* Left Column: Document Ingestion, State & Vector Store Indexes */}
        <aside
          className={`transition-all duration-300 ease-in-out flex flex-col gap-3.5 ${
            isSidebarOpen 
              ? 'w-80 lg:w-[350px] shrink-0' 
              : 'w-0 -ml-4 opacity-0 pointer-events-none'
          }`}
        >
          <FileUploader
            onUploadComplete={handleUploadComplete}
            activeDoc={activeDoc}
            onSelectDoc={setActiveDoc}
            documents={documents}
          />
        </aside>

        {/* Center/Right Column: Fact-Grounding Chat Interface */}
        <main className="flex-1 flex flex-col min-w-0 bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden relative">
          <ChatWindow
            activeDoc={activeDoc}
            activeDocName={activeDocObj?.filename || 'Uploaded Document'}
            onOpenCitations={handleOpenCitations}
            isSidebarOpen={isSidebarOpen}
            onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          />
        </main>
      </div>

      {/* Slide-over Inspection Citation Drawer */}
      <CitationDrawer
        isOpen={citationModal.isOpen}
        onClose={handleCloseCitations}
        sources={citationModal.sources}
        retrievalTime={citationModal.retrievalTime}
      />
    </div>
  );
}
