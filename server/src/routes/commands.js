const express = require('express');
const router = express.Router();
const Command = require('../models/Command');

// GET /api/commands - Get command history (paginated)
router.get('/', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const skip = (page - 1) * limit;
    const status = req.query.status;
    const intent = req.query.intent;

    const filter = {};
    if (status) filter.status = status;
    if (intent) filter.intent = intent;

    const [commands, total] = await Promise.all([
      Command.find(filter)
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(limit)
        .lean(),
      Command.countDocuments(filter),
    ]);

    res.json({
      success: true,
      data: commands,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// GET /api/commands/stats - Get statistics
router.get('/stats', async (req, res) => {
  try {
    const [total, success, failed, byIntent] = await Promise.all([
      Command.countDocuments(),
      Command.countDocuments({ status: 'success' }),
      Command.countDocuments({ status: 'failed' }),
      Command.aggregate([
        { $group: { _id: '$intent', count: { $sum: 1 } } },
        { $sort: { count: -1 } },
        { $limit: 10 },
      ]),
    ]);

    res.json({
      success: true,
      data: { total, success, failed, topIntents: byIntent },
    });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// GET /api/commands/:id
router.get('/:id', async (req, res) => {
  try {
    const command = await Command.findById(req.params.id);
    if (!command) {
      return res.status(404).json({ success: false, message: 'Command nahi mili' });
    }
    res.json({ success: true, data: command });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// POST /api/commands/test - Test text command with Ollama
router.post('/test', async (req, res) => {
  try {
    const { text } = req.body;
    if (!text) {
      return res.status(400).json({ success: false, message: 'Text command is required' });
    }
    const { processWithOllama } = require('../services/ollamaService');
    const Memory = require('../models/Memory');
    
    // Get memory context
    const memories = await Memory.find({ confirmed: true })
      .sort({ usageCount: -1 })
      .limit(20)
      .lean();

    const memoryContext = memories
      .map(m => {
        if (m.type === 'contact') return `"${m.key}" → Contact: ${JSON.stringify(m.value)}`;
        if (m.type === 'alias') return `"${m.key}" → App: ${m.value}`;
        if (m.type === 'preference') return `Pasand: ${m.key} = ${m.value}`;
        return `${m.key}: ${JSON.stringify(m.value)}`;
      })
      .join('\n');

    const result = await processWithOllama(text, memoryContext);
    res.json({ success: true, data: result });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// DELETE /api/commands - Clear history
router.delete('/', async (req, res) => {
  try {
    await Command.deleteMany({});
    res.json({ success: true, message: 'History clear ho gayi' });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

module.exports = router;
