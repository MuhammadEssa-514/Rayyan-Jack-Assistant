const mongoose = require('mongoose');

const CommandSchema = new mongoose.Schema(
  {
    // Original voice text from user
    rawText: {
      type: String,
      required: true,
      trim: true,
    },
    // Parsed intent from AI Brain
    intent: {
      type: String,
      required: true,
      index: true,
    },
    // Target device: windows | android | both | system
    target: {
      type: String,
      enum: ['windows', 'android', 'both', 'system', 'unknown'],
      default: 'windows',
    },
    // Parameters extracted by AI
    parameters: {
      type: mongoose.Schema.Types.Mixed,
      default: {},
    },
    // AI confidence score 0-1
    confidence: {
      type: Number,
      min: 0,
      max: 1,
      default: 0,
    },
    // Urdu response text (spoken via TTS)
    responseText: {
      type: String,
      default: '',
    },
    // Execution status
    status: {
      type: String,
      enum: ['pending', 'processing', 'success', 'failed', 'rejected'],
      default: 'pending',
      index: true,
    },
    // Error message if failed
    errorMessage: {
      type: String,
      default: null,
    },
    // Execution duration in ms
    executionTime: {
      type: Number,
      default: null,
    },
    // Device that executed
    executedBy: {
      type: String,
      default: null,
    },
    // Source: voice | dashboard | api
    source: {
      type: String,
      enum: ['voice', 'dashboard', 'api'],
      default: 'voice',
    },
  },
  {
    timestamps: true,
  }
);

// Index for fast queries
CommandSchema.index({ createdAt: -1 });
CommandSchema.index({ intent: 1, status: 1 });

module.exports = mongoose.model('Command', CommandSchema);
