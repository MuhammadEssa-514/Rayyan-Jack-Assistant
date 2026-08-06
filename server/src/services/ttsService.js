/**
 * TTS Service - Triggers text-to-speech on the voice engine
 * The voice engine runs Piper TTS locally.
 * Server sends TTS requests back to the voice engine via Socket.IO.
 */

const { getIO } = require('../socket');

/**
 * Speak text via the local Piper TTS engine
 * The voice engine listens for 'speak' events
 */
const speak = (text) => {
  try {
    const io = getIO();
    // Send to voice-engine room
    io.to('voice-engine').emit('speak', { text });
    console.log(`🔊 TTS: "${text}"`);
  } catch (err) {
    console.warn('TTS send error (voice engine may not be connected):', err.message);
  }
};

module.exports = { speak };
