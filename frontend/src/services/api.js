let rawBase = import.meta.env.VITE_API_BASE_URL || "/api";
if (rawBase.startsWith("http") && !rawBase.replace(/\/+$/, "").endsWith("/api")) {
  rawBase = rawBase.replace(/\/+$/, "") + "/api";
}
const API_BASE = rawBase.replace(/\/+$/, "");

// Cache token in memory / localStorage
let authToken = localStorage.getItem("rag_jwt_token") || null;

export async function initSession() {
  try {
    const res = await fetch(`${API_BASE}/session`);
    if (!res.ok) throw new Error("Failed to initialize session");
    const data = await res.json();
    authToken = data.token;
    localStorage.setItem("rag_jwt_token", data.token);
    return data;
  } catch (err) {
    console.warn("Session init error:", err);
    return null;
  }
}

export function getAuthHeaders() {
  const headers = {};
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  return headers;
}

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return await res.json();
  } catch (err) {
    return { status: "offline", error: err.message };
  }
}

export async function fetchDocuments() {
  try {
    const res = await fetch(`${API_BASE}/documents`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch documents");
    return await res.json();
  } catch (err) {
    console.error("fetchDocuments error:", err);
    return { documents: [], total: 0 };
  }
}

export async function deleteDocument(docId) {
  try {
    const res = await fetch(`${API_BASE}/documents/${docId}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to delete document");
    return await res.json();
  } catch (err) {
    console.error("deleteDocument error:", err);
    throw err;
  }
}

export async function uploadDocument(file, onProgressUpdate) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error?.detail || errorData.error || "Upload failed");
  }

  const uploadResult = await res.json();

  // If already cached, notify 100% immediately
  if (uploadResult.cached) {
    if (onProgressUpdate) {
      onProgressUpdate({
        progress: 100,
        status: "completed",
        message: uploadResult.message || "Loaded instantly from ChromaDB cache.",
      });
    }
    return uploadResult;
  }

  // Otherwise, subscribe to SSE progress endpoint
  if (uploadResult.task_id && onProgressUpdate) {
    await listenToProgress(uploadResult.task_id, onProgressUpdate);
  }

  return uploadResult;
}

function listenToProgress(taskId, onProgressUpdate) {
  return new Promise((resolve) => {
    let isFinished = false;
    const eventSource = new EventSource(`${API_BASE}/progress/${taskId}`);

    const finish = (result) => {
      if (isFinished) return;
      isFinished = true;
      try { eventSource.close(); } catch (_) {}
      resolve(result);
    };

    eventSource.addEventListener("progress", (event) => {
      try {
        const data = JSON.parse(event.data);
        onProgressUpdate(data);

        if (data.status === "completed" || data.status === "error") {
          finish(data);
        }
      } catch (err) {
        console.error("Failed to parse progress frame:", err);
      }
    });

    eventSource.onerror = async (err) => {
      console.warn("Progress SSE disconnected; switching to polling fallback:", err);
      try { eventSource.close(); } catch (_) {}

      // Poll until completed or 45 seconds timeout
      let attempts = 0;
      while (!isFinished && attempts < 45) {
        attempts++;
        await new Promise((r) => setTimeout(r, 1000));
        try {
          const res = await fetch(`${API_BASE}/progress/${taskId}/status`);
          if (res.ok) {
            const data = await res.json();
            onProgressUpdate(data);
            if (data.status === "completed" || data.status === "error" || data.progress >= 100) {
              finish(data);
              return;
            }
          }
        } catch (pollErr) {
          console.warn("Poll attempt failed:", pollErr);
        }
      }
      finish(null);
    };
  });
}

/**
 * Stream query tokens and sources from Gateway via SSE
 */
export async function streamQuery(query, docId, arg3, arg4, arg5, arg6) {
  let onToken, onSources, onDone, onError;
  if (typeof arg3 === "function") {
    onToken = arg3;
    onSources = arg4;
    onDone = arg5;
    onError = arg6;
  } else if (arg3 && typeof arg3 === "object") {
    onToken = arg3.onToken;
    onSources = arg3.onSources;
    onDone = arg3.onDone;
    onError = arg3.onError;
  }

  try {
    const response = await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({ query, doc_id: docId || null }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "Query failed");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop(); // Keep unfinished line in buffer

      let currentEvent = null;

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        if (trimmed.startsWith("event:")) {
          currentEvent = trimmed.replace("event:", "").trim();
        } else if (trimmed.startsWith("data:")) {
          const rawData = trimmed.replace("data:", "").trim();
          try {
            const data = JSON.parse(rawData);

            if (currentEvent === "sources" && onSources) {
              onSources(data.sources, data.retrieval_time);
            } else if (currentEvent === "token" && onToken) {
              onToken(data.token);
            } else if (currentEvent === "done" && onDone) {
              onDone(data.total_time);
            }
          } catch (e) {
            console.error("JSON parse error on SSE data:", e, rawData);
          }
        }
      }
    }

    if (onDone) onDone();
  } catch (err) {
    console.error("streamQuery error:", err);
    if (onError) onError(err);
  }
}
