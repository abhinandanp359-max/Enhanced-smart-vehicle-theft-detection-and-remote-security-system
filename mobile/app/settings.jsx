// app/settings.jsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Image,
} from 'react-native';
import { colors } from '../utils/theme';
import { BACKEND, getVehicleProfile } from '../utils/api';
import { sendLocalNotification } from '../utils/notifications';
export default function SettingsScreen() {
  const [profile, setProfile] = useState({
    name: 'My Vehicle',
    id: 'VEH_01',
    plate: 'KA-19-MG-2026',
    model: 'Modern Luxury SUV',
    customImageUri: null,
  });

  useEffect(() => {
    getVehicleProfile().then((data) => {
      if (data) setProfile((p) => ({ ...p, ...data }));
    });
  }, []);

  const testAlert = () => {
    sendLocalNotification('🧪 TEST NOTIFICATION', 'VehicleGuard AI push notifications are working properly!');
    Alert.alert('Notification Dispatched', 'Check your device notification tray.');
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.container}>
      <Text style={styles.headerTitle}>System Settings</Text>

      {/* Vehicle Registration & Customization */}
      <View style={styles.card}>
        <Text style={styles.cardLabel}>VEHICLE REGISTRATION</Text>
        <View style={styles.vehicleRow}>
          <Image
            source={
              profile.customImageUri
                ? { uri: profile.customImageUri }
                : require('../assets/car_suv.jpg')
            }
            style={styles.carThumb}
            resizeMode="contain"
          />
          <View style={{ flex: 1 }}>
            <Text style={styles.carName}>{profile.name}</Text>
            <Text style={styles.carSub}>{profile.plate} • {profile.id}</Text>
          </View>
        </View>
      </View>

      {/* Network Config */}
      <View style={styles.card}>
        <Text style={styles.cardLabel}>NETWORK & SERVER</Text>
        <View style={styles.row}>
          <Text style={styles.rowLabel}>Gateway API</Text>
          <Text style={styles.rowValue}>{BACKEND}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.rowLabel}>Real-time WebSocket</Text>
          <Text style={styles.rowValue}>Socket.io (Port 5000)</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.rowLabel}>Camera Link</Text>
          <Text style={styles.rowValue}>AI Biometric Engine</Text>
        </View>
      </View>

      {/* Push Notification Diagnostics */}
      <View style={styles.card}>
        <Text style={styles.cardLabel}>DIAGNOSTICS</Text>
        <TouchableOpacity style={styles.testBtn} onPress={testAlert} activeOpacity={0.8}>
          <Text style={styles.testBtnText}>🔔  Test Mobile Alert Sound & Vibration</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.footerText}>
        VehicleGuard AI • v2.0{'\n'}Autonomous Anti-Theft & Evidence Vault
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#F4F6F8' },
  container: { padding: 18, gap: 16, paddingBottom: 120, maxWidth: 600, width: '100%', alignSelf: 'center' },
  headerTitle: { fontSize: 24, fontWeight: '800', color: '#111827', marginTop: 10, marginBottom: 2 },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.04)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 2,
    gap: 12,
  },
  cardLabel: { fontSize: 11, fontWeight: '800', color: colors.textMuted, letterSpacing: 1.5 },
  vehicleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    backgroundColor: '#F9FAFB',
    borderRadius: 14,
    padding: 10,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  carThumb: {
    width: 90,
    height: 60,
  },
  carName: {
    fontSize: 16,
    fontWeight: '800',
    color: '#111827',
  },
  carSub: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: '600',
    marginTop: 2,
  },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  rowLabel: { fontSize: 13, color: colors.textSecondary, fontWeight: '500' },
  rowValue: { fontSize: 13, color: colors.primaryGreen, fontWeight: '700', fontFamily: 'monospace' },
  testBtn: {
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  testBtnText: { color: '#374151', fontWeight: '800', fontSize: 13 },
  footerText: { textAlign: 'center', color: colors.textMuted, fontSize: 12, lineHeight: 18, marginTop: 12 },
});
