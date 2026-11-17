const express = require("express");
const cors = require("cors");
const multer = require("multer");
const axios = require("axios");
const FormData = require("form-data");
const fs = require("fs");
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, "../.env") });
require("dotenv").config();

const { verifyToken, issueToken } = require("./middleware/auth");

const app = express();
const PORT = process.env.GATEWAY_PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

// Ensure secure buffer directory exists
const UPLOAD_BUFFER_DIR = path.join(__dirname, "uploads_buffer");
if (!fs.existsSync(UPLOAD_BUFFER_DIR)) {
  fs.mkdirSync(UPLOAD_BUFFER_DIR, { recursive: true });
}

// Multer Disk Storage Configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, UPLOAD_BUFFER_DIR);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
    cb(null, `${uniqueSuffix}-${file.originalname}`);
  },
});

// File validation: PDF and Text documents
const fileFilter = (req, file, cb) => {
  const allowedExtensions = [".pdf", ".txt", ".md"];
  const ext = path.extname(file.originalname).toLowerCase();
  if (allowedExtensions.includes(ext)) {
    cb(null, true);
  } else {
    cb(new Error(`Invalid file type '${ext}'. Only PDF, TXT, and MD files are supported.`));
  }
};

const upload = multer({
  storage,
  fileFilter,
  limits: { fileSize: 100 * 1024 * 1024 }, // 100MB max file size (handles 1000+ pages)
});

// In-memory Audit & Session Registry
const auditLog = [];

app.use(cors({ origin: "*" }));
app.use(express.json());

// 1. Session & Token Issuance Endpoint
app.get("/api/session", (req, res) => {
  const userId = `usr_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
  const token = issueToken(userId);
  res.json({ token, userId });
});

// 2. Health & Status Check
app.get("/api/health", async (req, res) => {
  let backendHealth = "unreachable";
  try {
    const resp = await axios.get(`${BACKEND_URL}/api/health`, { timeout: 3000 });
    backendHealth = resp.data;
  } catch (err) {
    backendHealth = { status: "offline", error: err.message };
  }

  res.json({
    status: "healthy",
    gateway: "Node.js Express Gateway",
    port: PORT,
    backend_url: BACKEND_URL,
    backend_status: backendHealth,
  });
});

// 3. File Upload & Proxying to FastAPI
app.post("/api/upload", verifyToken, upload.single("file"), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No file uploaded or invalid file format." });
  }

  const fileId = `file_${Date.now()}`;
  const userId = req.user ? req.user.userId : "anonymous";
  const filePath = req.file.path;

  // Layer 2: Audit log record { file_id, user_id, status: 'pending' }
  const auditEntry = {
    file_id: fileId,
    user_id: userId,
    filename: req.file.originalname,
    size_bytes: req.file.size,
    status: "pending",
    timestamp: new Date().toISOString(),
  };
  auditLog.push(auditEntry);
  console.log(`[Gateway Audit] User '${userId}' initiated upload of '${req.file.originalname}' (${(req.file.size / 1024).toFixed(1)} KB)`);

  try {
    // Construct multipart form data for FastAPI
    const formData = new FormData();
    formData.append("file", fs.createReadStream(filePath), {
      filename: req.file.originalname,
      contentType: req.file.mimetype,
    });

    // Proxy high-speed payload to FastAPI
    const response = await axios.post(`${BACKEND_URL}/api/upload`, formData, {
      headers: {
        ...formData.getHeaders(),
      },
      maxContentLength: Infinity,
      maxBodyLength: Infinity,
    });

    auditEntry.status = response.data.cached ? "cached" : "processing";
    auditEntry.doc_id = response.data.doc_id;

    // Return FastAPI response enriched with gateway file metadata
    res.json({
      ...response.data,
      gateway_file_id: fileId,
    });
  } catch (error) {
    auditEntry.status = "failed";
    console.error("[Gateway Proxy Error]", error.response ? error.response.data : error.message);
    const statusCode = error.response ? error.response.status : 502;
    const detail = error.response ? error.response.data : { detail: "Failed to connect to AI Backend" };
    res.status(statusCode).json({ error: detail });
  } finally {
    // Clean up temporary local buffer file
    fs.unlink(filePath, (err) => {
      if (err) console.error("Error removing temp file:", err);
    });
  }
});

// 4. SSE Real-Time Progress Stream Relay
app.get("/api/progress/:taskId", async (req, res) => {
  const { taskId } = req.params;

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");

  try {
    const response = await axios({
      method: "get",
      url: `${BACKEND_URL}/api/progress/${taskId}`,
      responseType: "stream",
    });

    response.data.pipe(res);

    req.on("close", () => {
      response.data.destroy();
    });
  } catch (err) {
    console.error(`[Gateway SSE Error for ${taskId}]:`, err.message);
    res.write(`event: progress\ndata: ${JSON.stringify({ status: "error", message: err.message })}\n\n`);
    res.end();
  }
});

// 5. Streaming Chat Query Relay (Token-by-Token SSE)
app.post("/api/query", verifyToken, async (req, res) => {
  const { query, doc_id } = req.body;

  if (!query || !query.trim()) {
    return res.status(400).json({ error: "Query cannot be empty" });
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");

  try {
    const response = await axios({
      method: "post",
      url: `${BACKEND_URL}/api/query`,
      data: { query, doc_id },
      responseType: "stream",
    });

    response.data.pipe(res);

    req.on("close", () => {
      response.data.destroy();
    });
  } catch (err) {
    console.error("[Gateway Query Stream Error]:", err.message);
    res.write(`event: token\ndata: ${JSON.stringify({ token: `Error connecting to AI Backend: ${err.message}` })}\n\n`);
    res.write(`event: done\ndata: ${JSON.stringify({ total_time: 0 })}\n\n`);
    res.end();
  }
});

// 6. Ingested Documents List Relay
app.get("/api/documents", async (req, res) => {
  try {
    const response = await axios.get(`${BACKEND_URL}/api/documents`);
    res.json(response.data);
  } catch (err) {
    res.status(502).json({ error: "Unable to fetch documents from AI backend" });
  }
});

// 7. Ingested Document Deletion Relay
app.delete("/api/documents/:docId", async (req, res) => {
  try {
    const response = await axios.delete(`${BACKEND_URL}/api/documents/${req.params.docId}`);
    res.json(response.data);
  } catch (err) {
    res.status(502).json({ error: "Unable to delete document in AI backend" });
  }
});

// Start API Gateway Server
app.listen(PORT, () => {
  console.log(`=======================================================`);
  console.log(`🚀 Node.js API Gateway listening on port ${PORT}`);
  console.log(`🔗 Proxying AI workloads to FastAPI at ${BACKEND_URL}`);
  console.log(`=======================================================`);
});
