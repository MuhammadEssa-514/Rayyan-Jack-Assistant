const axios = require('axios');

const OLLAMA_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const MODEL = process.env.OLLAMA_MODEL || 'qwen2.5:7b';

// ─── System Prompt ────────────────────────────────────────────────────────────
const SYSTEM_PROMPT = `Tum Jack AI ho — ek aqalmand personal assistant jo Windows laptop aur Android phone control karta hai.

AAPKA KAAM:
User ki baat sun ke SIRF ek valid JSON object return karo. Kuch aur mat likho — na explanation, na text, sirf JSON.

JSON FORMAT (hamesha yahi structure use karo):
{
  "intent": "string",
  "target": "windows|android|both|system",
  "confidence": 0.0-1.0,
  "parameters": {},
  "response_text": "Urdu mein jawab (Roman Urdu bhi theek hai)"
}

AVAILABLE INTENTS:
- Windows: open_app, close_app, browse_url, search_web, type_text, press_key, click_element, scroll, screenshot, set_volume, set_brightness, shutdown, restart, sleep, play_music, pause_music, next_track, prev_track, open_folder, create_file, copy_clipboard, paste_clipboard
- Android: send_whatsapp_message, make_call, send_sms, open_android_app, set_android_volume, set_android_brightness, enable_bluetooth, disable_bluetooth, enable_wifi, disable_wifi, toggle_flashlight, take_photo, read_notifications
- Both: set_alarm, set_reminder, search_web
- System: get_time, get_date, get_weather, unknown

PARAMETERS EXAMPLES:
- open_app: { "app_name": "Chrome" }
- send_whatsapp_message: { "contact": "Ali", "message": "Main aa raha hoon" }
- browse_url: { "url": "https://youtube.com" }
- search_web: { "query": "Pakistan cricket score" }
- set_volume: { "level": 50 } OR { "action": "increase"/"decrease" }
- make_call: { "contact": "Ali", "phone": "" }
- open_folder: { "path": "C:/Users/Downloads" }
- press_key: { "keys": ["ctrl", "c"] }
- type_text: { "text": "hello world" }

LANGUAGE RULES:
- User Urdu mein bolega, Roman Urdu mein bolega, ya English mein bolega
- response_text HAMESHA Urdu ya Roman Urdu mein likhna
- Parameters mein contact names aur messages bilkul waise rakhna jaise user ne bola

EXAMPLE:
User: "Jack, Ali ko WhatsApp karo ke main 10 minute baad aa raha hoon"
Response:
{
  "intent": "send_whatsapp_message",
  "target": "android",
  "confidence": 0.97,
  "parameters": { "contact": "Ali", "message": "Main 10 minute baad aa raha hoon" },
  "response_text": "Ali ko WhatsApp message bhej raha hoon"
}

Agar command samajh na aaye:
{
  "intent": "unknown",
  "target": "system",
  "confidence": 0.1,
  "parameters": {},
  "response_text": "Maafi chahta hoon, mujhe samajh nahi aaya. Dobara bolen?"
}`;

// ─── Parse AI response ────────────────────────────────────────────────────────
const parseAIResponse = (text) => {
  try {
    // Try direct JSON parse
    const cleaned = text.trim();
    if (cleaned.startsWith('{')) {
      return JSON.parse(cleaned);
    }

    // Extract JSON from markdown code block
    const jsonMatch = cleaned.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[1]);
    }

    // Find first { ... } in the text
    const start = cleaned.indexOf('{');
    const end = cleaned.lastIndexOf('}');
    if (start !== -1 && end !== -1) {
      return JSON.parse(cleaned.substring(start, end + 1));
    }

    throw new Error('JSON nahi mila response mein');
  } catch (err) {
    console.error('❌ AI response parse error:', err.message, '\nRaw:', text);
    return {
      intent: 'unknown',
      target: 'system',
      confidence: 0,
      parameters: {},
      response_text: 'Kuch masla ho gaya, dobara try karein',
    };
  }
};

// ─── Main: Process text through Ollama or Groq Cloud ───────────────────────
const processWithOllama = async (userText, memoryContext = '') => {
  const startTime = Date.now();

  // 1. If GROQ_API_KEY is available (e.g. Vercel deployment), use Groq Cloud API
  if (process.env.GROQ_API_KEY) {
    try {
      console.log('⚡ Processing via Groq Cloud AI API...');
      const groqMessages = [
        { role: 'system', content: SYSTEM_PROMPT },
      ];
      if (memoryContext) {
        groqMessages.push({ role: 'system', content: `YAAD RAKHNE WALI CHEEZEIN:\n${memoryContext}` });
      }
      groqMessages.push({ role: 'user', content: userText });

      const response = await axios.post(
        'https://api.groq.com/openai/v1/chat/completions',
        {
          model: process.env.GROQ_MODEL || 'llama-3.3-70b-versatile',
          messages: groqMessages,
          temperature: 0.1,
          response_format: { type: 'json_object' },
        },
        {
          headers: {
            'Authorization': `Bearer ${process.env.GROQ_API_KEY}`,
            'Content-Type': 'application/json',
          },
          timeout: 15000,
        }
      );

      const rawText = response.data?.choices?.[0]?.message?.content || '';
      const parsed = parseAIResponse(rawText);
      const duration = Date.now() - startTime;
      console.log(`🧠 Groq AI [${duration}ms]: ${parsed.intent} → ${parsed.target} (${(parsed.confidence * 100).toFixed(0)}%)`);
      return { ...parsed, _processingTime: duration };
    } catch (groqErr) {
      console.error('❌ Groq API error:', groqErr.response?.data || groqErr.message);
      // Fallthrough to Ollama
    }
  }

  // 2. Local Ollama processing
  try {
    // Build messages
    const messages = [
      { role: 'system', content: SYSTEM_PROMPT },
    ];

    // Inject memory context if available
    if (memoryContext) {
      messages.push({
        role: 'system',
        content: `YAAD RAKHNE WALI CHEEZEIN:\n${memoryContext}`,
      });
    }

    messages.push({ role: 'user', content: userText });

    const response = await axios.post(
      `${OLLAMA_URL}/api/chat`,
      {
        model: MODEL,
        messages,
        stream: false,
        options: {
          temperature: 0.1,      // Low temperature for consistent JSON
          top_p: 0.9,
          num_predict: 512,      // Limit response length for speed
          repeat_penalty: 1.1,
        },
        format: 'json',          // Force JSON mode (Ollama 0.2+)
      },
      {
        timeout: 30000,          // 30 second timeout
        headers: { 'Content-Type': 'application/json' },
      }
    );

    const rawText = response.data?.message?.content || response.data?.response || '';
    const parsed = parseAIResponse(rawText);
    const duration = Date.now() - startTime;

    console.log(`🧠 AI [${duration}ms]: ${parsed.intent} → ${parsed.target} (${(parsed.confidence * 100).toFixed(0)}%)`);

    return { ...parsed, _processingTime: duration };

  } catch (err) {
    const duration = Date.now() - startTime;

    if (err.code === 'ECONNREFUSED') {
      console.error('❌ Ollama nahi chal raha! Run: ollama serve');
      return {
        intent: 'system_error',
        target: 'system',
        confidence: 0,
        parameters: { error: 'ollama_offline' },
        response_text: 'Ollama service band hai. Pehle ollama serve chalayein.',
        _processingTime: duration,
      };
    }

    if (err.response?.status === 404) {
      console.error(`❌ Model "${MODEL}" nahi mila! Run: ollama pull ${MODEL}`);
      return {
        intent: 'system_error',
        target: 'system',
        confidence: 0,
        parameters: { error: 'model_not_found', model: MODEL },
        response_text: `Model ${MODEL} download nahi hai. Terminal mein chalayein: ollama pull ${MODEL}`,
        _processingTime: duration,
      };
    }

    console.error('❌ Ollama error:', err.message);
    return {
      intent: 'unknown',
      target: 'system',
      confidence: 0,
      parameters: {},
      response_text: 'AI se connection mein masla aa gaya',
      _processingTime: duration,
    };
  }
};

// ─── Check Ollama status ──────────────────────────────────────────────────────
const checkOllamaStatus = async () => {
  try {
    const res = await axios.get(`${OLLAMA_URL}/api/tags`, { timeout: 3000 });
    const models = res.data?.models?.map(m => m.name) || [];
    const hasModel = models.some(m => m.startsWith('qwen2.5'));
    return {
      online: true,
      models,
      hasRequiredModel: hasModel,
      currentModel: MODEL,
    };
  } catch {
    return { online: false, models: [], hasRequiredModel: false, currentModel: MODEL };
  }
};

module.exports = { processWithOllama, checkOllamaStatus, MODEL };
