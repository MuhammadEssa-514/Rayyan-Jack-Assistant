const express = require('express');
const router = express.Router();
const Device = require('../models/Device');

// GET /api/devices - List all devices
router.get('/', async (req, res) => {
  try {
    const devices = await Device.find().sort({ lastSeen: -1 }).lean();
    res.json({ success: true, data: devices });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// GET /api/devices/online - Only online devices
router.get('/online', async (req, res) => {
  try {
    const devices = await Device.find({ status: 'online' }).lean();
    res.json({ success: true, data: devices });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// GET /api/devices/:deviceId
router.get('/:deviceId', async (req, res) => {
  try {
    const device = await Device.findOne({ deviceId: req.params.deviceId });
    if (!device) {
      return res.status(404).json({ success: false, message: 'Device nahi mili' });
    }
    res.json({ success: true, data: device });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// DELETE /api/devices/:deviceId
router.delete('/:deviceId', async (req, res) => {
  try {
    await Device.findOneAndDelete({ deviceId: req.params.deviceId });
    res.json({ success: true, message: 'Device remove ho gayi' });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

module.exports = router;
