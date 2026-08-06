const mongoose = require('mongoose');

let isConnected = false;

const connectDB = async () => {
  if (isConnected) return;

  try {
    const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/jackai';
    
    await mongoose.connect(uri, {
      serverSelectionTimeoutMS: 5000,
    });

    isConnected = true;
    const dbType = uri.includes('mongodb+srv') ? 'MongoDB Atlas' : 'MongoDB Local';
    console.log(`✅ ${dbType} se connected: ${mongoose.connection.host}`);

    mongoose.connection.on('error', (err) => {
      console.error('❌ MongoDB error:', err);
      isConnected = false;
    });

    mongoose.connection.on('disconnected', () => {
      console.warn('⚠️  MongoDB disconnected. Reconnect ho raha hai...');
      isConnected = false;
    });

  } catch (error) {
    console.error('❌ MongoDB connection failed:', error.message);
    console.error('💡 Make sure MongoDB chal raha hai: mongod --dbpath C:/data/db');
    // Don't exit - allow server to run without DB for testing
  }
};

module.exports = connectDB;
