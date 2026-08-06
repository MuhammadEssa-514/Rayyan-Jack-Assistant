require('dotenv').config();
const express = require('express');
const http = require('http');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');

const connectDB = require('./config/db');
const { initSocket } = require('./socket');

// ─── App Setup ───────────────────────────────────────────────────────────────
const app = express();
const server = http.createServer(app);

// ─── Middleware ───────────────────────────────────────────────────────────────
app.use(helmet({ contentSecurityPolicy: false }));
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
  credentials: true,
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(morgan(process.env.NODE_ENV === 'development' ? 'dev' : 'combined'));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 500,
});
app.use('/api', limiter);

// ─── Database ─────────────────────────────────────────────────────────────────
connectDB();

// ─── Socket.IO ────────────────────────────────────────────────────────────────
initSocket(server);

// ─── Routes ───────────────────────────────────────────────────────────────────
app.use('/api/commands', require('./routes/commands'));
app.use('/api/devices', require('./routes/devices'));
app.use('/api/memory', require('./routes/memory'));

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'online',
    timestamp: new Date().toISOString(),
    message: 'Jack AI Server chal raha hai ✅',
    version: '1.0.0',
  });
});

// Voice command via HTTP (fallback when WebSocket unavailable)
app.post('/api/voice', async (req, res) => {
  try {
    const { text } = req.body;
    if (!text) return res.status(400).json({ success: false, message: 'Text required' });

    const { processVoiceCommand } = require('./services/commandRouter');
    const { getIO } = require('./socket');

    let io;
    try { io = getIO(); } catch { io = { to: () => ({ emit: () => {} }) }; }

    const result = await processVoiceCommand(text, io);
    res.json({ success: true, response_text: result.response_text, data: result });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});


// ─── Error Handler ────────────────────────────────────────────────────────────
app.use((err, req, res, next) => {
  console.error('❌ Server Error:', err.message);
  res.status(err.status || 500).json({
    success: false,
    message: err.message || 'Internal server error',
  });
});

// 404 Handler
app.use((req, res) => {
  res.status(404).json({ success: false, message: 'Route nahi mili' });
});

// ─── Start Server ─────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  console.log('\n╔══════════════════════════════════════╗');
  console.log('║      🤖 Jack AI Server Started       ║');
  console.log(`║   Port: ${PORT}  |  Mode: ${process.env.NODE_ENV || 'development'}  ║`);
  console.log('╚══════════════════════════════════════╝\n');
});

module.exports = { app, server };
