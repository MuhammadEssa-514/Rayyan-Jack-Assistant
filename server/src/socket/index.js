const { Server } = require('socket.io');
const { v4: uuidv4 } = require('uuid');
const Device = require('../models/Device');
const { handleWindowsEvent } = require('./windowsHandler');
const { handleAndroidEvent } = require('./androidHandler');
const { processVoiceCommand } = require('../services/commandRouter');

let io;

// Track connected sockets
const connectedClients = new Map(); // socketId -> device info

const initSocket = (server) => {
  io = new Server(server, {
    cors: {
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      methods: ['GET', 'POST'],
      credentials: true,
    },
    pingTimeout: 60000,
    pingInterval: 25000,
  });

  io.on('connection', async (socket) => {
    console.log(`🔌 Client connected: ${socket.id}`);

    // ── Device Registration ───────────────────────────────────────────
    socket.on('register_device', async (data) => {
      try {
        const { type, name, deviceId, metadata } = data;
        const id = deviceId || uuidv4();

        // Save/update in DB
        const device = await Device.findOneAndUpdate(
          { deviceId: id },
          {
            deviceId: id,
            name: name || `${type}-device`,
            type,
            status: 'online',
            socketId: socket.id,
            ipAddress: socket.handshake.address,
            metadata: metadata || {},
            lastSeen: new Date(),
          },
          { new: true, upsert: true }
        );

        // Store in memory map
        connectedClients.set(socket.id, { ...device.toObject(), socket });

        // Join room by device type
        socket.join(type);
        socket.join(id);

        socket.emit('registered', { success: true, deviceId: id, device });

        // Broadcast updated device list to dashboards
        broadcastDeviceUpdate();

        console.log(`✅ ${type.toUpperCase()} registered: ${name || id}`);
      } catch (err) {
        socket.emit('error', { message: err.message });
      }
    });

    // ── Voice Command (from voice engine) ────────────────────────────
    socket.on('voice_command', async (data) => {
      try {
        console.log(`🎤 Voice: "${data.text}"`);
        
        // Broadcast to dashboard: listening event
        io.to('dashboard').emit('voice_status', { status: 'processing', text: data.text });

        // Process through AI Brain + route to device
        const result = await processVoiceCommand(data.text, io);

        // Notify dashboard of completed command
        io.to('dashboard').emit('command_executed', result);
        io.to('dashboard').emit('voice_status', { status: 'idle' });

      } catch (err) {
        console.error('❌ Voice command error:', err.message);
        io.to('dashboard').emit('voice_status', { status: 'error', message: err.message });
      }
    });

    // ── Windows Agent Events ──────────────────────────────────────────
    socket.on('windows_event', (data) => handleWindowsEvent(socket, data, io));
    socket.on('windows_result', (data) => {
      console.log(`✅ Windows result:`, data);
      io.to('dashboard').emit('command_result', { target: 'windows', ...data });
    });

    // ── Android Events ────────────────────────────────────────────────
    socket.on('android_event', (data) => handleAndroidEvent(socket, data, io));
    socket.on('android_result', (data) => {
      console.log(`✅ Android result:`, data);
      io.to('dashboard').emit('command_result', { target: 'android', ...data });
    });

    // ── Ping/Heartbeat ────────────────────────────────────────────────
    socket.on('heartbeat', () => {
      socket.emit('heartbeat_ack', { timestamp: Date.now() });
    });

    // ── Disconnect ────────────────────────────────────────────────────
    socket.on('disconnect', async (reason) => {
      const client = connectedClients.get(socket.id);
      if (client) {
        await Device.findOneAndUpdate(
          { deviceId: client.deviceId },
          { status: 'offline', lastSeen: new Date() }
        );
        connectedClients.delete(socket.id);
        console.log(`🔴 ${client.type?.toUpperCase() || 'Client'} disconnected: ${client.name || socket.id}`);
        broadcastDeviceUpdate();
      }
    });
  });

  console.log('⚡ Socket.IO initialized');
  return io;
};

// Broadcast updated device list to all dashboards
const broadcastDeviceUpdate = async () => {
  try {
    const devices = await Device.find().sort({ lastSeen: -1 }).lean();
    io.to('dashboard').emit('devices_update', devices);
  } catch (err) {
    console.error('Device update broadcast error:', err.message);
  }
};

// Get io instance anywhere in the app
const getIO = () => {
  if (!io) throw new Error('Socket.IO not initialized');
  return io;
};

module.exports = { initSocket, getIO, connectedClients };
