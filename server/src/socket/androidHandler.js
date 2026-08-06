const Device = require('../models/Device');

/**
 * Handle events from the Android companion app
 */
const handleAndroidEvent = async (socket, data, io) => {
  const { event, payload } = data;
  console.log(`📱 Android Event: ${event}`, payload);

  switch (event) {
    case 'status_update':
      await Device.findOneAndUpdate(
        { socketId: socket.id },
        { status: payload.status || 'online', lastSeen: new Date() }
      );
      io.to('dashboard').emit('android_status', payload);
      break;

    case 'message_sent':
      io.to('dashboard').emit('notification', {
        type: 'success',
        message: `${payload.contact} ko message bhej diya ✅`,
      });
      break;

    case 'call_initiated':
      io.to('dashboard').emit('notification', {
        type: 'info',
        message: `${payload.contact} ko call mil rahi hai 📞`,
      });
      break;

    case 'notification_received':
      // Android forwarding a notification to dashboard
      io.to('dashboard').emit('android_notification', payload);
      break;

    case 'error':
      console.error('❌ Android Error:', payload.message);
      io.to('dashboard').emit('notification', {
        type: 'error',
        message: `Android error: ${payload.message}`,
      });
      break;

    default:
      console.warn(`⚠️  Unknown Android event: ${event}`);
  }
};

/**
 * Send a command to the Android app
 */
const sendToAndroid = (io, command) => {
  io.to('android').emit('execute_command', command);
  console.log(`📤 Android command sent: ${command.intent}`);
};

module.exports = { handleAndroidEvent, sendToAndroid };
