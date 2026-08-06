const Device = require('../models/Device');

/**
 * Handle events from the Windows Agent
 */
const handleWindowsEvent = async (socket, data, io) => {
  const { event, payload } = data;
  console.log(`🖥️  Windows Event: ${event}`, payload);

  switch (event) {
    case 'status_update':
      // Windows agent reporting its status
      await Device.findOneAndUpdate(
        { socketId: socket.id },
        { status: payload.status || 'online', lastSeen: new Date() }
      );
      io.to('dashboard').emit('windows_status', payload);
      break;

    case 'screenshot_ready':
      // Forward screenshot data to dashboard
      io.to('dashboard').emit('screenshot', payload);
      break;

    case 'app_opened':
      io.to('dashboard').emit('notification', {
        type: 'success',
        message: `${payload.appName} khul gaya ✅`,
      });
      break;

    case 'error':
      console.error('❌ Windows Agent Error:', payload.message);
      io.to('dashboard').emit('notification', {
        type: 'error',
        message: `Windows error: ${payload.message}`,
      });
      break;

    default:
      console.warn(`⚠️  Unknown Windows event: ${event}`);
  }
};

/**
 * Send a command to the Windows agent
 */
const sendToWindows = (io, command) => {
  io.to('windows').emit('execute_command', command);
  console.log(`📤 Windows command sent: ${command.intent}`);
};

module.exports = { handleWindowsEvent, sendToWindows };
