const express = require('express');
const router = express.Router();
const Memory = require('../models/Memory');

// GET /api/memory - List all memories
router.get('/', async (req, res) => {
  try {
    const { type, search } = req.query;
    const filter = {};
    if (type) filter.type = type;
    if (search) filter.key = { $regex: search, $options: 'i' };

    const memories = await Memory.find(filter)
      .sort({ usageCount: -1, updatedAt: -1 })
      .lean();

    res.json({ success: true, data: memories });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// POST /api/memory - Add/update memory
router.post('/', async (req, res) => {
  try {
    const { type, key, value, label, confirmed } = req.body;
    if (!type || !key || value === undefined) {
      return res.status(400).json({ 
        success: false, 
        message: 'type, key, aur value zaroori hain' 
      });
    }

    const memory = await Memory.findOneAndUpdate(
      { type, key: key.toLowerCase() },
      { value, label, confirmed: confirmed ?? false, lastAccessed: new Date() },
      { new: true, upsert: true, runValidators: true }
    );

    res.json({ success: true, data: memory, message: 'Memory save ho gayi' });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// DELETE /api/memory/:id
router.delete('/:id', async (req, res) => {
  try {
    await Memory.findByIdAndDelete(req.params.id);
    res.json({ success: true, message: 'Memory delete ho gayi' });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// DELETE /api/memory - Clear all
router.delete('/', async (req, res) => {
  try {
    await Memory.deleteMany({});
    res.json({ success: true, message: 'Sab memories clear ho gayi' });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

module.exports = router;
