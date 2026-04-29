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

// API proxy: /api/get-code?username= OR /api/get-code?username=test@ruutukf.com
app.get('/api/get-code', async (req, res, next) => {
  try {
    const input = (req.query.username || '').trim();

    if (!input) {
      return safeReply(res, 400, { error: 'Username or email is required' });
    }

    let email;
    let domain;

    if (input.includes('@')) {
      email = input;
      domain = input.split('@')[1].toLowerCase();
    } else {
      email = `${input}@batdongsanvgp.com`;
      domain = 'batdongsanvgp.com';
    }

    let apiUrl;
    let isTempMailApi = false;

    if (domain === 'batdongsanvgp.com' || domain === 'hunght1890.com') {
      apiUrl = `https://hunght1890.com/${email}`;
    } else if (domain === 'ruutukf.com') {
      // Dedicated flow for ruutukf.com via temp-mail.io API
      apiUrl = `https://api.internal.temp-mail.io/api/v3/email/${email}/messages`;
      isTempMailApi = true;
    } else {
      // Default fallback
      apiUrl = `https://api.internal.temp-mail.io/api/v3/email/${email}/messages`;
      isTempMailApi = true;
    }

    console.log(`✅ [${domain}] Gọi tới:`, apiUrl);

    // ⚠️ Yêu cầu Node >= 18 để dùng fetch mặc định
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      }
    });

    if (!response.ok) {
      if (isTempMailApi && response.status === 400) {
        try {
          const errData = await response.json();
          if (errData && errData.message === "Email not found") {
            console.log(`❕ Chưa có hộp thư ${email}, đang tiến hành tạo mới...`);
            const name = email.split('@')[0];
            const domainStr = email.split('@')[1];

            const createReq = await fetch('https://api.internal.temp-mail.io/api/v3/email/new', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ name, domain: domainStr })
            });

            if (createReq.ok) {
              console.log(`✅ Đã tạo mới hộp thư thành công: ${email}`);
              return safeReply(res, 200, { ok: true, email, raw: [] });
            } else {
              return safeReply(res, 200, { ok: false, error: 'Không thể khởi tạo hộp thư: HTTP ' + createReq.status });
            }
          }
        } catch (e) {
          console.error("❌ Lỗi khi tự động tạo mailbox:", e);
        }
      }
      return safeReply(res, response.status, {
        error: `Remote HTTP ${response.status}: ${response.statusText}`,
        apiUrl
      });
    }

    let data = await response.json();

    // Chuẩn hóa dữ liệu temp-mail.io để tương thích với frontend hiện tại
    if (isTempMailApi && Array.isArray(data)) {
      data = data.map(item => ({
        ...item,
        body: item.body_html || item.body_text || ''
      }));
    }

    // Trả data về cho frontend dùng
    safeReply(res, 200, { ok: true, email, raw: data });

  } catch (err) {
    console.error('❌ Lỗi proxy:', err);
    safeReply(res, 500, { ok: false, error: (err && err.message) ? err.message : 'Internal server error' });
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
