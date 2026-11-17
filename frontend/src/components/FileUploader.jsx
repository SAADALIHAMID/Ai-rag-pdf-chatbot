import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Zap, 
  Loader2,
  Sparkles,
  Layers,
  Database,
  Trash2,
  FileCheck2,
  Check,
  FileType
} from 'lucide-react';
import { uploadDocument, deleteDocument } from '../services/api';

export default function FileUploader({ onUploadComplete, activeDoc, onSelectDoc, documents }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progressState, setProgressState] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file) => {
    const allowed = ['.pdf', '.txt', '.md'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
      setErrorMessage(`Format '${ext}' unsupported. Upload PDF, TXT, or MD.`);
      return;
    }

    setErrorMessage(null);
    setIsUploading(true);
    setProgressState({
      progress: 5,
      status: 'starting',
      message: 'Hashing MD5 & dispatching parser...',
    });

    try {
      const result = await uploadDocument(file, (update) => {
        setProgressState(update);
      });

      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (err) {
      console.error('Upload processing error:', err);
      setErrorMessage(err.message || 'Failed to ingest file');
      setProgressState(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (e, docId) => {
    e.stopPropagation();
    try {
      await deleteDocument(docId);
      if (onUploadComplete) {
        onUploadComplete({});
      }
    } catch (err) {
      console.error('Delete error:', err);
    }
  };

  const getFileBadge = (filename) => {
    const ext = filename?.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') {
      return <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">PDF</span>;
    }
    if (ext === 'txt') {
      return <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">TXT</span>;
    }
    return <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">DOC</span>;
  };

  return (
    <div className="h-full flex flex-col gap-3.5">
      
      {/* 1. Drag & Drop Card */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-4 flex flex-col shrink-0">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <UploadCloud className="w-4 h-4" />
            </div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Document Ingestion
            </h2>
          </div>
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
            Fast Ingestion
          </span>
        </div>

        {/* Drop Target */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all duration-200 ${
            isDragging
              ? 'border-indigo-500 bg-indigo-50/60 scale-[0.99]'
              : 'border-slate-200/90 hover:border-indigo-400 bg-slate-50/60 hover:bg-indigo-50/30'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md"
            className="hidden"
            onChange={handleFileSelect}
            disabled={isUploading}
          />

          <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 text-indigo-600 flex items-center justify-center mx-auto mb-2.5 shadow-2xs">
            {isUploading ? (
              <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
            ) : (
              <UploadCloud className="w-5 h-5 text-indigo-600" />
            )}
          </div>

          <p className="text-xs font-bold text-slate-800">
            {isUploading ? 'Vectorizing Document...' : 'Upload Document'}
          </p>
          <p className="text-[11px] text-slate-500 mt-1">
            Drag & drop PDF / TXT up to 1000+ pages
          </p>

          <div className="flex items-center justify-center gap-1.5 mt-2.5">
            <span className="text-[9px] font-mono font-medium px-1.5 py-0.2 rounded bg-slate-200/70 text-slate-600">.PDF</span>
            <span className="text-[9px] font-mono font-medium px-1.5 py-0.2 rounded bg-slate-200/70 text-slate-600">.TXT</span>
            <span className="text-[9px] font-mono font-medium px-1.5 py-0.2 rounded bg-slate-200/70 text-slate-600">.MD</span>
          </div>
        </div>

        {/* Live Ingestion Progress */}
        {progressState && (
          <div className="mt-3.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center justify-between text-[11px] mb-1.5 font-medium">
              <span className="text-slate-700 truncate pr-2 font-medium">
                {progressState.message || 'Processing chunks...'}
              </span>
              <span className="font-mono text-indigo-600 font-bold shrink-0">
                {progressState.progress || 0}%
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-indigo-600 h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${progressState.progress || 5}%` }}
              />
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && (
          <div className="mt-3 p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="font-medium">{errorMessage}</span>
          </div>
        )}
      </div>

      {/* 2. Documents Registry List */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-4 flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="flex items-center justify-between mb-3 shrink-0">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Database className="w-4 h-4" />
            </div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Active Documents
            </h2>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
            {documents?.length || 0} Indexed
          </span>
        </div>

        {/* Documents Cards */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {documents && documents.length > 0 ? (
            documents.map((doc) => {
              const isActive = doc.doc_id === activeDoc;
              return (
                <div
                  key={doc.doc_id}
                  onClick={() => onSelectDoc && onSelectDoc(doc.doc_id)}
                  className={`p-3 rounded-xl border text-left cursor-pointer transition-all duration-150 relative group ${
                    isActive
                      ? 'bg-indigo-50/70 border-indigo-300 shadow-2xs ring-1 ring-indigo-400/30'
                      : 'bg-slate-50/50 hover:bg-slate-100/70 border-slate-200/70'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-2.5 min-w-0 pr-2">
                      <div className={`p-2 rounded-lg mt-0.5 shrink-0 shadow-2xs ${
                        isActive ? 'bg-indigo-600 text-white' : 'bg-white text-slate-600 border border-slate-200'
                      }`}>
                        <FileText className="w-3.5 h-3.5" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center space-x-1.5">
                          <p className={`text-xs truncate ${
                            isActive ? 'text-indigo-950 font-bold' : 'text-slate-800 font-semibold'
                          }`}>
                            {doc.filename}
                          </p>
                          {getFileBadge(doc.filename)}
                        </div>
                        <div className="flex items-center space-x-2 mt-1 text-[10px] text-slate-500 font-mono">
                          <span>{doc.total_pages || 1} Pages</span>
                          <span>•</span>
                          <span className="text-indigo-600 font-semibold">{doc.chunk_count || 0} Chunks</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-1 shrink-0">
                      {isActive && (
                        <span className="w-2 h-2 rounded-full bg-indigo-600" />
                      )}
                      <button
                        onClick={(e) => handleDelete(e, doc.doc_id)}
                        title="Delete document"
                        className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-all"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center py-10 text-slate-400">
              <FileText className="w-8 h-8 mx-auto mb-2 opacity-30 text-slate-400" />
              <p className="text-xs font-medium">No documents indexed</p>
              <p className="text-[11px] text-slate-400 mt-0.5">Upload a PDF above to begin querying.</p>
            </div>
          )}
        </div>

        {/* Footer Status */}
        <div className="mt-3 pt-3 border-t border-slate-100 shrink-0 text-[11px] text-slate-500 flex items-center justify-between font-medium">
          <span>Encrypted Storage</span>
          <span className="text-emerald-600 font-semibold flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Instant Caching Active
          </span>
        </div>
      </div>
    </div>
  );
}
