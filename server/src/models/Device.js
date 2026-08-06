const mongoose = require('mongoose');

const DeviceSchema = new mongoose.Schema(
  {
    // Unique device identifier
    deviceId: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },
    // Display name
    name: {
      type: String,
      required: true,
      trim: true,
    },
    // Device type
    type: {
      type: String,
      enum: ['windows', 'android', 'dashboard', 'voice-engine'],
      required: true,
    },
    // Connection status
    status: {
      type: String,
      enum: ['online', 'offline', 'idle'],
      default: 'offline',
    },
    // Current Socket.IO socket ID
    socketId: {
      type: String,
      default: null,
    },
    // IP address on local network
    ipAddress: {
      type: String,
      default: null,
    },
    // Device metadata
    metadata: {
      os: String,
      osVersion: String,
      appVersion: String,
      hostname: String,
      // Android specific
      androidVersion: String,
      manufacturer: String,
      model: String,
    },
    // Last seen timestamp
    lastSeen: {
      type: Date,
      default: Date.now,
    },
    // Total commands executed
    commandCount: {
      type: Number,
      default: 0,
    },
  },
  {
    timestamps: true,
  }
);

DeviceSchema.index({ type: 1, status: 1 });

module.exports = mongoose.model('Device', DeviceSchema);
