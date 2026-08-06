const Command = require('../models/Command');
const Memory = require('../models/Memory');
const { processWithOllama } = require('./ollamaService');
const { sendToWindows } = require('../socket/windowsHandler');
const { sendToAndroid } = require('../socket/androidHandler');

/**
 * Main command processor:
 * voice text → Ollama AI → JSON → route to device → save to DB
 */
const processVoiceCommand = async (text, io) => {
  const startTime = Date.now();

  // 1. Build memory context (inject known contacts/aliases into prompt)
  const memoryContext = await buildMemoryContext(text);

  // 2. Send to AI Brain
  const aiResult = await processWithOllama(text, memoryContext);

  // 3. Enhance parameters with stored memories
  const enrichedResult = await enrichWithMemory(aiResult);

  // 4. Save command to DB
  let savedCommand;
  try {
    savedCommand = await Command.create({
      rawText: text,
      intent: enrichedResult.intent,
      target: enrichedResult.target,
      parameters: enrichedResult.parameters,
      confidence: enrichedResult.confidence,
      responseText: enrichedResult.response_text,
      status: 'processing',
      source: 'voice',
    });
  } catch (dbErr) {
    console.warn('⚠️  DB save failed (continuing anyway):', dbErr.message);
  }

  // 5. Route to correct device
  try {
    await routeCommand(enrichedResult, io);

    // Mark success
    if (savedCommand) {
      await Command.findByIdAndUpdate(savedCommand._id, {
        status: 'success',
        executionTime: Date.now() - startTime,
      });
    }
  } catch (routeErr) {
    console.error('❌ Routing error:', routeErr.message);
    if (savedCommand) {
      await Command.findByIdAndUpdate(savedCommand._id, {
        status: 'failed',
        errorMessage: routeErr.message,
      });
    }
  }

  // 6. Update memory with new contact/app references
  await learnFromCommand(enrichedResult, text);

  return {
    commandId: savedCommand?._id,
    rawText: text,
    ...enrichedResult,
    executionTime: Date.now() - startTime,
  };
};

// ─── Route command to device ──────────────────────────────────────────────────
const routeCommand = async (command, io) => {
  const { target, intent } = command;

  // Handle system-level commands
  if (target === 'system') {
    return handleSystemCommand(command, io);
  }

  // Route to Windows
  if (target === 'windows' || target === 'both') {
    sendToWindows(io, command);
  }

  // Route to Android
  if (target === 'android' || target === 'both') {
    sendToAndroid(io, command);
  }

  // Unknown intents
  if (intent === 'unknown') {
    io.to('dashboard').emit('notification', {
      type: 'warning',
      message: command.response_text,
    });
  }
};

// ─── Handle system commands (no device needed) ────────────────────────────────
const handleSystemCommand = (command, io) => {
  const { intent } = command;

  if (intent === 'get_time') {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('ur-PK', { hour: '2-digit', minute: '2-digit' });
    io.to('dashboard').emit('system_response', {
      intent,
      response: `Abhi ${timeStr} baj rahe hain`,
    });
  } else if (intent === 'get_date') {
    const now = new Date();
    io.to('dashboard').emit('system_response', { intent, response: now.toLocaleDateString('ur-PK') });
  } else {
    io.to('dashboard').emit('system_response', {
      intent,
      response: command.response_text,
    });
  }
};

// ─── Build memory context for prompt ─────────────────────────────────────────
const buildMemoryContext = async (text) => {
  try {
    // Get most used contacts and aliases
    const memories = await Memory.find({ confirmed: true })
      .sort({ usageCount: -1 })
      .limit(20)
      .lean();

    if (!memories.length) return '';

    return memories
      .map(m => {
        if (m.type === 'contact') return `"${m.key}" → Contact: ${JSON.stringify(m.value)}`;
        if (m.type === 'alias') return `"${m.key}" → App: ${m.value}`;
        if (m.type === 'preference') return `Pasand: ${m.key} = ${m.value}`;
        return `${m.key}: ${JSON.stringify(m.value)}`;
      })
      .join('\n');
  } catch {
    return '';
  }
};

// ─── Enrich parameters using stored memories ──────────────────────────────────
const enrichWithMemory = async (result) => {
  const { parameters, intent } = result;

  // If contact mentioned, look up in memory
  if (parameters?.contact) {
    const contactMemory = await Memory.recall('contact', parameters.contact).catch(() => null);
    if (contactMemory?.value?.phone) {
      result.parameters.phone = contactMemory.value.phone;
      result.parameters.whatsappNumber = contactMemory.value.whatsapp || contactMemory.value.phone;
    }
  }

  // If app name mentioned, look up alias
  if (parameters?.app_name) {
    const appMemory = await Memory.recall('alias', parameters.app_name).catch(() => null);
    if (appMemory?.value) {
      result.parameters.app_path = appMemory.value;
    }
  }

  return result;
};

// ─── Learn from executed commands ─────────────────────────────────────────────
const learnFromCommand = async (result, originalText) => {
  try {
    const { intent, parameters } = result;

    // Auto-save contact references (unconfirmed - needs user confirmation)
    if (parameters?.contact && intent.includes('message') || intent.includes('call')) {
      await Memory.findOneAndUpdate(
        { type: 'contact', key: parameters.contact.toLowerCase() },
        {
          $inc: { usageCount: 1 },
          $setOnInsert: {
            type: 'contact',
            key: parameters.contact.toLowerCase(),
            value: { name: parameters.contact },
            label: parameters.contact,
            confirmed: false,
          },
          lastAccessed: new Date(),
        },
        { upsert: true }
      );
    }
  } catch (err) {
    // Non-critical - don't throw
    console.warn('Memory learn warning:', err.message);
  }
};

module.exports = { processVoiceCommand };
