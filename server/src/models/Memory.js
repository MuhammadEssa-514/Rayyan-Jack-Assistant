const mongoose = require('mongoose');

const MemorySchema = new mongoose.Schema(
  {
    // Memory type: contact | app | alias | preference | fact
    type: {
      type: String,
      enum: ['contact', 'app', 'alias', 'preference', 'fact', 'shortcut'],
      required: true,
      index: true,
    },
    // The key/trigger word (e.g., "Ali", "browser")
    key: {
      type: String,
      required: true,
      trim: true,
      lowercase: true,
      index: true,
    },
    // The actual value (e.g., phone number, full name, app path)
    value: {
      type: mongoose.Schema.Types.Mixed,
      required: true,
    },
    // Human-readable label
    label: {
      type: String,
      trim: true,
    },
    // How many times this memory was used
    usageCount: {
      type: Number,
      default: 1,
    },
    // Confidence that this mapping is correct
    confidence: {
      type: Number,
      min: 0,
      max: 1,
      default: 1.0,
    },
    // Whether user explicitly confirmed this
    confirmed: {
      type: Boolean,
      default: false,
    },
    // Context/notes
    notes: {
      type: String,
      default: '',
    },
    // Last time this memory was accessed
    lastAccessed: {
      type: Date,
      default: Date.now,
    },
  },
  {
    timestamps: true,
  }
);

// Compound index: unique per type+key
MemorySchema.index({ type: 1, key: 1 }, { unique: true });

// Static: find or create a memory entry
MemorySchema.statics.remember = async function(type, key, value, label = '') {
  const existing = await this.findOne({ type, key: key.toLowerCase() });
  if (existing) {
    existing.usageCount += 1;
    existing.lastAccessed = new Date();
    if (value) existing.value = value;
    return existing.save();
  }
  return this.create({ type, key: key.toLowerCase(), value, label });
};

// Static: lookup a memory
MemorySchema.statics.recall = async function(type, key) {
  const mem = await this.findOneAndUpdate(
    { type, key: key.toLowerCase() },
    { $inc: { usageCount: 1 }, lastAccessed: new Date() },
    { new: true }
  );
  return mem;
};

module.exports = mongoose.model('Memory', MemorySchema);
