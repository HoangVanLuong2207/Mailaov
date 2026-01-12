// server.js
// Chạy:  node server.js
// Cần:   npm install express

const express = require('express');
const path = require('path');

// Debug lifecycle logging (do not exit on errors so server stays alive)
process.on('beforeExit', (code) => {
  console.log('ℹ️ process beforeExit', code);
});
process.on('exit', (code) => {
  console.log('ℹ️ process exit', code);
});
process.on('uncaughtException', (err) => {
  console.error('❌ uncaughtException:', err && err.stack ? err.stack : err);
  // Keep process alive; just log
});
process.on('unhandledRejection', (reason) => {
  console.error('❌ unhandledRejection:', reason);
  // Keep process alive; just log
});

console.log('🔧 Booting server.js ...');
const app = express();
const PORT = Number(process.env.PORT) || 3000;
console.log('🔧 Using PORT =', PORT);

// Serve static file (index.html) trong cùng thư mục
app.use(express.static(__dirname));

// Explicitly serve index.html for root path
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Health check route for cron ping (keep server alive)
app.get('/ping', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Helper: safe reply to avoid throwing when client disconnected
function safeReply(res, status, body) {
  try {
    if (res.headersSent || res.writableEnded) {
      return;
    }
    res.status(status).json(body);
  } catch (e) {
    // swallow errors from writing to a closed response
    console.error('❕ safeReply error:', e && e.message ? e.message : e);
  }
}

// API proxy: /api/get-code?username=regcsuc48
app.get('/api/get-code', async (req, res, next) => {
  try {
    const username = (req.query.username || '').trim();

    if (!username) {
      return safeReply(res, 400, { error: 'Username is required' });
    }

    const email = `${username}@batdongsanvgp.com`;
    const encodedEmail = encodeURIComponent(email);
    const apiUrl = `https://hunght1890.com/${encodedEmail}`;

    console.log('✅ Gọi tới:', apiUrl);

    // ⚠️ Yêu cầu Node >= 18 để dùng fetch mặc định
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        // KHÔNG set User-Agent ở đây, để Node tự lo
      }
    });

    if (!response.ok) {
      return safeReply(res, response.status, {
        error: `Remote HTTP ${response.status}: ${response.statusText}`
      });
    }

    const data = await response.json();

    // Trả nguyên data về cho frontend dùng
    safeReply(res, 200, { ok: true, email, raw: data });

  } catch (err) {
    console.error('❌ Lỗi proxy:', err);
    safeReply(res, 500, { ok: false, error: (err && err.message) ? err.message : 'Internal server error' });
    // Also forward to Express error handler for visibility
    next(err);
  }
});

// Centralized error handler to prevent crashes
app.use((err, req, res, next) => {
  console.error('❌ Express error:', err && err.stack ? err.stack : err);
  safeReply(res, 500, { ok: false, error: 'Internal server error' });
});

const server = app.listen(PORT, () => {
  console.log(`🚀 Server chạy tại http://localhost:${PORT}`);
});

server.on('error', (err) => {
  console.error('❌ Lỗi khi lắng nghe cổng:', err && err.message ? err.message : err);
  process.exit(1);
});
