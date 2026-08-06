import React, { useEffect, useState, useRef } from 'react';
import {
  SafeAreaView,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  TextInput,
  ScrollView,
  StatusBar,
} from 'react-native';
import io from 'socket.io-client';

const SERVER_URL = 'http://10.0.2.2:5000'; // Default Android Emulator loopback IP

export default function App() {
  const [connected, setConnected] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [serverIp, setServerIp] = useState('10.0.2.2');
  const socketRef = useRef<any>(null);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 19)]);
  };

  const connectToServer = () => {
    if (socketRef.current) {
      socketRef.current.disconnect();
    }

    const url = `http://${serverIp}:5000`;
    addLog(`Connecting to server: ${url}`);
    
    const socket = io(url, {
      transports: ['websocket'],
      reconnection: true,
    });

    socket.on('connect', () => {
      setConnected(true);
      addLog('🔌 Socket connected! Registering device...');
      socket.emit('register_device', {
        type: 'android',
        name: 'Android Mobile Companion',
        deviceId: 'android-companion-phone',
        metadata: {
          os: 'Android',
          osVersion: '13',
          appVersion: '1.0.0',
        },
      });
    });

    socket.on('disconnect', () => {
      setConnected(false);
      addLog('🔴 Disconnected from server');
    });

    socket.on('registered', (data: any) => {
      addLog(`✅ Registered successfully: ${JSON.stringify(data.deviceId)}`);
    });

    socket.on('execute_command', (data: any) => {
      const { intent, parameters, commandId } = data;
      addLog(`📥 Command received: ${intent}`);
      
      // Perform actions based on intent
      if (intent === 'send_whatsapp_message') {
        const { contact, message } = parameters || {};
        addLog(`💬 WhatsApp: sending to ${contact}: "${message}"`);
        
        // Emit results back to server
        socket.emit('android_result', {
          commandId,
          intent,
          success: true,
          message: `${contact} ko WhatsApp bhej diya: "${message}"`,
        });
        
        socket.emit('android_event', {
          event: 'message_sent',
          payload: { contact, message }
        });
      } else if (intent === 'make_call') {
        const { contact, phone } = parameters || {};
        addLog(`📞 Call: dialing ${contact} (${phone})`);
        
        socket.emit('android_result', {
          commandId,
          intent,
          success: true,
          message: `${contact} ko call mila di`,
        });
        
        socket.emit('android_event', {
          event: 'call_initiated',
          payload: { contact, phone }
        });
      } else {
        addLog(`⚠️ Unknown intent: ${intent}`);
        socket.emit('android_result', {
          commandId,
          intent,
          success: false,
          message: `Intent '${intent}' handle karne ka setup nahi hai.`,
        });
      }
    });

    socketRef.current = socket;
  };

  useEffect(() => {
    connectToServer();
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#080c14" />
      <View style={styles.header}>
        <Text style={styles.logo}>Jack AI</Text>
        <Text style={styles.subtitle}>Android Companion Node</Text>
      </View>

      <View style={styles.connectionCard}>
        <View style={styles.statusRow}>
          <Text style={styles.label}>Connection Status:</Text>
          <View style={[styles.statusIndicator, { backgroundColor: connected ? '#10b981' : '#ef4444' }]} />
          <Text style={[styles.statusText, { color: connected ? '#10b981' : '#ef4444' }]}>
            {connected ? 'ONLINE' : 'OFFLINE'}
          </Text>
        </View>

        <Text style={styles.labelInput}>Server IP Address:</Text>
        <View style={styles.ipRow}>
          <TextInput
            style={styles.input}
            value={serverIp}
            onChangeText={setServerIp}
            placeholder="10.0.2.2"
            placeholderTextColor="#475569"
          />
          <TouchableOpacity style={styles.button} onPress={connectToServer}>
            <Text style={styles.buttonText}>Reconnect</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.logsCard}>
        <Text style={styles.logsTitle}>Activity Logs</Text>
        <ScrollView style={styles.scroll}>
          {logs.map((log, index) => (
            <Text key={index} style={styles.logText}>
              {log}
            </Text>
          ))}
          {logs.length === 0 && (
            <Text style={styles.noLogsText}>No activities logged yet.</Text>
          )}
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080c14',
    padding: 16,
  },
  header: {
    alignItems: 'center',
    marginVertical: 20,
  },
  logo: {
    fontSize: 24,
    fontWeight: '800',
    color: '#818cf8',
    letterSpacing: 1,
  },
  subtitle: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 4,
  },
  connectionCard: {
    backgroundColor: '#0d1320',
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.15)',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    color: '#94a3b8',
    marginRight: 8,
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '600',
  },
  labelInput: {
    fontSize: 12,
    color: '#475569',
    marginBottom: 6,
  },
  ipRow: {
    flexDirection: 'row',
    gap: 10,
  },
  input: {
    flex: 1,
    height: 40,
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.15)',
    borderRadius: 8,
    color: '#f1f5f9',
    paddingHorizontal: 12,
    fontSize: 14,
  },
  button: {
    backgroundColor: '#6366f1',
    borderRadius: 8,
    paddingHorizontal: 16,
    justifyContent: 'center',
  },
  buttonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 13,
  },
  logsCard: {
    flex: 1,
    backgroundColor: '#0d1320',
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.15)',
    borderRadius: 16,
    padding: 16,
  },
  logsTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#f1f5f9',
    marginBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(99, 102, 241, 0.1)',
    paddingBottom: 8,
  },
  scroll: {
    flex: 1,
  },
  logText: {
    fontSize: 11,
    color: '#34d399',
    fontFamily: 'monospace',
    marginBottom: 6,
    lineHeight: 16,
  },
  noLogsText: {
    color: '#475569',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 20,
  },
});
