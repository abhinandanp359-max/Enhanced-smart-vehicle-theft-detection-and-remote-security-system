// app/index.jsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useVehicleState } from '../hooks/useVehicleState';
import AlarmModal from '../components/AlarmModal';
import LiveCameraModal from '../components/LiveCameraModal';
import LocationPin from '../components/LocationPin';
import { colors } from '../utils/theme';
import { getVehicleProfile, postSirenCommand } from '../utils/api';

export default function HomeScreen() {
  const router = useRouter();
  const {
    securityMode,
    alarmActive,
    lastIncident,
    connectionStatus,
    gpsCoords,
    sendCommand,
  } = useVehicleState();

  const [vehicleProfile, setVehicleProfile] = useState({
    name: 'My Vehicle',
    id: 'VEH_01',
    plate: 'KA-19-MG-2026',
    model: 'Modern Luxury SUV',
    customImageUri: null,
    lastSync: '12 Oct 2025, 07:34 PM',
  });

  useEffect(() => {
    getVehicleProfile().then((data) => {
      if (data) {
        setVehicleProfile((p) => ({ ...p, ...data }));
      }
    });
  }, []);

  const isConnected = connectionStatus === 'connected';
  const isArmed = securityMode === 'ARMED';
  const isDisarmed = securityMode === 'DISARMED';
  const isTrusted = securityMode === 'TRUSTED_DRIVER' || securityMode === 'TRUSTED';
  const hasGps = Boolean(gpsCoords?.lat && gpsCoords?.lat !== 0);

  const [sirenLoading, setSirenLoading] = useState(false);
  const [cameraModalOpen, setCameraModalOpen] = useState(false);

  const handleSirenPress = () => {
    if (sirenLoading) return; // Prevent duplicate commands while in-flight

    if (alarmActive) {
      // Siren is active: offer immediate stop action
      Alert.alert(
        'Vehicle Siren Active',
        'The vehicle emergency theft siren is sounding. Stop the siren now?',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: '🔕 Stop Siren',
            style: 'destructive',
            onPress: async () => {
              setSirenLoading(true);
              try {
                await postSirenCommand('stop');
              } catch (err) {
                Alert.alert('Siren Command Error', err.message || 'Failed to silence vehicle siren.');
              } finally {
                setSirenLoading(false);
              }
            },
          },
        ]
      );
    } else {
      // Siren is standby: confirm before loud blast
      Alert.alert(
        'Activate Emergency Siren',
        'Trigger the high-decibel vehicle anti-theft siren now to deter intruders?',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: '🚨 Activate Siren Now',
            style: 'destructive',
            onPress: async () => {
              setSirenLoading(true);
              try {
                await postSirenCommand('activate');
              } catch (err) {
                Alert.alert('Siren Command Error', err.message || 'Failed to activate vehicle siren.');
              } finally {
                setSirenLoading(false);
              }
            },
          },
        ]
      );
    }
  };

  return (
    <View style={styles.screen}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
      >
        {/* 1. Top Header */}
        <View style={styles.topHeader}>
          <Text style={styles.brandTitle}>VEHICLEGUARD</Text>
          <View style={styles.onlineBadge}>
            <View style={[styles.dot, { backgroundColor: isConnected ? '#10B981' : '#EF4444' }]} />
            <Text style={styles.onlineText}>{isConnected ? 'System online' : 'System offline'}</Text>
          </View>
        </View>

        {/* 2. Hero Status */}
        <View style={styles.heroSection}>
          <View style={[
            styles.shieldBadge,
            isDisarmed && { backgroundColor: '#6B7280' },
            isTrusted && { backgroundColor: colors.amber }
          ]}>
            <Text style={styles.shieldIcon}>
              {isArmed ? '✓' : isDisarmed ? '✕' : '👤'}
            </Text>
          </View>
          <View style={styles.heroTextContainer}>
            <Text style={styles.heroSubText}>Your vehicle is</Text>
            <Text style={[
              styles.heroMainText,
              isDisarmed && { color: '#4B5563' },
              isTrusted && { color: colors.amber }
            ]}>
              {isArmed ? 'protected' : isDisarmed ? 'disarmed' : 'trusted mode'}
            </Text>
          </View>
        </View>

        {/* 3. Card 1: Vehicle Profile Card (Clean Display) */}
        <View style={styles.card}>
          <View style={styles.vehicleCardRow}>
            {/* Vehicle Image */}
            <View style={styles.carImageWrapper}>
              <Image
                source={
                  vehicleProfile.customImageUri
                    ? { uri: vehicleProfile.customImageUri }
                    : require('../assets/car_suv.jpg')
                }
                style={styles.carImage}
                resizeMode="contain"
              />
            </View>

            {/* Vehicle Info */}
            <View style={styles.vehicleDetails}>
              <View style={styles.vehicleTitleRow}>
                <Text style={styles.vehicleName}>
                  {vehicleProfile.name} <Text style={styles.vehicleId}>• {vehicleProfile.id}</Text>
                </Text>
              </View>

              {/* Status Pill Badge */}
              <View style={[
                styles.statusPill,
                isDisarmed && { backgroundColor: '#F3F4F6' },
                isTrusted && { backgroundColor: colors.amberLight },
                alarmActive && { backgroundColor: colors.crimsonLight },
              ]}>
                <Text style={[
                  styles.statusPillText,
                  isDisarmed && { color: '#4B5563' },
                  isTrusted && { color: colors.amber },
                  alarmActive && { color: colors.crimson },
                ]}>
                  {alarmActive
                    ? '🚨 Intruder alert!'
                    : isArmed
                    ? '🛡️ Protection armed'
                    : isDisarmed
                    ? '🔓 Protection disarmed'
                    : '👤 Trusted driver active'}
                </Text>
              </View>

              {/* Last Sync */}
              <Text style={styles.syncText}>
                🕒 Last sync: {vehicleProfile.lastSync || '12 Oct 2025, 07:34 PM'}
              </Text>
            </View>
          </View>
        </View>

        {/* 4. Card 2: SAFETY STATUS (Fully Interactive) */}
        <View style={styles.card}>
          <Text style={styles.sectionHeader}>SAFETY STATUS</Text>
          <View style={styles.safetyGrid}>
            {/* Metric 1: GPS (Clickable -> /map) */}
            <TouchableOpacity
              style={styles.metricItem}
              activeOpacity={0.7}
              onPress={() => router.push('/map')}
              accessibilityRole="button"
              accessibilityLabel="View live GPS telemetry and satellite map"
            >
              <View style={[styles.metricIconCircle, { backgroundColor: '#E6F4EA' }]}>
                <LocationPin size="sm" color={colors.primaryGreen} />
              </View>
              <Text style={styles.metricLabel}>GPS</Text>
              <View style={styles.metricStatusRow}>
                <View style={[styles.statusMiniDot, { backgroundColor: hasGps ? '#10B981' : '#F59E0B' }]} />
                <Text style={styles.metricStatusText}>{hasGps ? 'Live' : 'Searching'}</Text>
              </View>
            </TouchableOpacity>

            <View style={styles.metricDivider} />

            {/* Metric 2: Siren (Clickable -> Activate/Stop with Hardware Confirmation) */}
            <TouchableOpacity
              style={styles.metricItem}
              activeOpacity={0.7}
              onPress={handleSirenPress}
              disabled={sirenLoading}
              accessibilityRole="button"
              accessibilityLabel={alarmActive ? "Stop vehicle siren" : "Activate vehicle emergency siren"}
            >
              <View
                style={[
                  styles.metricIconCircle,
                  { backgroundColor: alarmActive ? colors.crimsonLight : '#FEF3C7' },
                  sirenLoading && { opacity: 0.6 },
                ]}
              >
                {sirenLoading ? (
                  <ActivityIndicator size="small" color={alarmActive ? colors.crimson : colors.amber} />
                ) : (
                  <Text style={styles.metricEmoji}>{alarmActive ? '📢' : '🚨'}</Text>
                )}
              </View>
              <Text style={styles.metricLabel}>Siren</Text>
              <View style={styles.metricStatusRow}>
                <View
                  style={[
                    styles.statusMiniDot,
                    { backgroundColor: alarmActive ? colors.crimson : colors.amber },
                  ]}
                />
                <Text
                  style={[
                    styles.metricStatusText,
                    alarmActive && { color: colors.crimson, fontWeight: '800' },
                  ]}
                >
                  {sirenLoading ? 'Sending...' : alarmActive ? 'ACTIVE' : 'Standby'}
                </Text>
              </View>
            </TouchableOpacity>

            <View style={styles.metricDivider} />

            {/* Metric 3: Camera (Clickable -> Live Camera Monitoring) */}
            <TouchableOpacity
              style={styles.metricItem}
              activeOpacity={0.7}
              onPress={() => setCameraModalOpen(true)}
              accessibilityRole="button"
              accessibilityLabel="Open live cabin camera monitoring"
            >
              <View style={[styles.metricIconCircle, { backgroundColor: isDisarmed ? '#F3F4F6' : '#E6F4EA' }]}>
                <Text style={styles.metricEmoji}>📷</Text>
              </View>
              <Text style={styles.metricLabel}>Camera</Text>
              <View style={styles.metricStatusRow}>
                <View
                  style={[
                    styles.statusMiniDot,
                    { backgroundColor: isDisarmed ? '#9CA3AF' : '#10B981' },
                  ]}
                />
                <Text style={styles.metricStatusText}>
                  {isDisarmed ? 'Paused' : 'Monitoring'}
                </Text>
              </View>
            </TouchableOpacity>
          </View>
        </View>

        {/* 5. Card 3: Vehicle Location */}
        <View style={styles.card}>
          <TouchableOpacity
            style={styles.locationHeaderRow}
            activeOpacity={0.8}
            onPress={() => router.push('/map')}
          >
            <View style={styles.locationIconWrapper}>
              <LocationPin size="sm" color={colors.primaryGreen} />
            </View>
            <View style={styles.locationTitleWrapper}>
              <Text style={styles.locationTitle}>Vehicle Location</Text>
              <Text style={styles.locationCoords}>
                {gpsCoords?.lat ? Number(gpsCoords.lat).toFixed(6) : '13.044074'}, {gpsCoords?.lng ? Number(gpsCoords.lng).toFixed(6) : '74.977508'}
              </Text>
            </View>
            <Text style={styles.chevron}>›</Text>
          </TouchableOpacity>

          {/* Map Image Texture Preview with Sleek Teardrop Pin */}
          <View style={styles.mapTextureWrapper}>
            <Image
              source={require('../assets/map_texture.jpg')}
              style={styles.mapTextureImage}
              resizeMode="cover"
            />
            {/* Center Pulsing Teardrop Pin (No Lollipop!) */}
            <View style={styles.centerPinContainer}>
              <View style={styles.pinAuraOuter}>
                <View style={styles.pinAuraInner}>
                  <View style={styles.teardropPin}>
                    <View style={styles.teardropDot} />
                  </View>
                </View>
              </View>
            </View>
          </View>

          {/* View Live Location Action Button */}
          <TouchableOpacity
            style={styles.viewLocationBtn}
            onPress={() => router.push('/map')}
            activeOpacity={0.85}
          >
            <Text style={styles.viewLocationBtnText}>🗺️  View live location</Text>
          </TouchableOpacity>
        </View>

        {/* 6. Card 4: Recent Security Activity & Controls */}
        <View style={styles.card}>
          <View style={styles.activityHeaderRow}>
            <View style={styles.activityTitleGroup}>
              <Text style={{ fontSize: 18 }}>🛡️</Text>
              <Text style={styles.activityTitle}>Recent Security Activity</Text>
            </View>
            <TouchableOpacity onPress={() => router.push('/incidents')}>
              <Text style={styles.viewAllText}>View all ›</Text>
            </TouchableOpacity>
          </View>

          {/* Activity Banner */}
          <TouchableOpacity
            style={[
              styles.activityBanner,
              alarmActive && { backgroundColor: colors.crimsonLight, borderColor: 'rgba(239,68,68,0.2)' }
            ]}
            activeOpacity={0.8}
            onPress={() => setCameraModalOpen(true)}
            accessibilityRole="button"
            accessibilityLabel="Open live camera monitoring"
          >
            <View style={[
              styles.activityCheckCircle,
              alarmActive && { backgroundColor: '#FEE2E2' }
            ]}>
              <Text style={{ fontSize: 16 }}>{alarmActive ? '🚨' : '✓'}</Text>
            </View>
            <View style={styles.activityBannerTexts}>
              <Text style={[
                styles.activityStatusBold,
                alarmActive && { color: colors.crimson }
              ]}>
                {alarmActive ? 'Critical Threat Detected!' : 'No threats detected'}
              </Text>
              <Text style={styles.activityStatusSub}>
                {alarmActive ? 'Intruder confirmed in driver seat' : 'Camera monitoring is active (tap to view)'}
              </Text>
            </View>
          </TouchableOpacity>

          {/* Controls Row (Side by Side Buttons matching mockup!) */}
          <View style={styles.controlButtonsRow}>
            {/* Primary Toggle: Disarm / Arm */}
            <TouchableOpacity
              style={[
                styles.pillButton,
                styles.disarmPill,
                !isArmed && { backgroundColor: colors.primaryGreen }
              ]}
              onPress={() => sendCommand(isArmed ? 'DISARM' : 'ARM')}
              activeOpacity={0.85}
            >
              <Text style={styles.disarmPillText}>
                {isArmed ? '🔒  Disarm protection' : '🛡️  Arm protection'}
              </Text>
            </TouchableOpacity>

            {/* Secondary Action: Trusted Driver */}
            <TouchableOpacity
              style={[
                styles.pillButton,
                styles.trustedPill,
                isTrusted && { backgroundColor: colors.amber, borderColor: colors.amber }
              ]}
              onPress={() => sendCommand('TRUSTED_DRIVER_ON')}
              activeOpacity={0.85}
            >
              <Text style={[
                styles.trustedPillText,
                isTrusted && { color: '#FFFFFF' }
              ]}>
                👤  Trusted driver
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>

      {/* Full-Screen Alarm Modal */}
      <AlarmModal
        visible={alarmActive}
        incident={lastIncident}
        onSilence={() => sendCommand('SILENCE_ALARM')}
        onDisarm={() => sendCommand('DISARM')}
        onTrustedDriver={() => sendCommand('TRUSTED_DRIVER_ON')}
      />

      {/* Dedicated Full-Screen Live Camera Monitoring Modal */}
      <LiveCameraModal
        visible={cameraModalOpen}
        onClose={() => setCameraModalOpen(false)}
        securityMode={securityMode}
        alarmActive={alarmActive}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#F4F6F8',
  },
  scroll: {
    flex: 1,
  },
  container: {
    padding: 16,
    paddingTop: Platform.OS === 'web' ? 20 : (Platform.OS === 'android' ? 34 : 44),
    gap: 12,
    paddingBottom: 120,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  topHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  brandTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#111827',
    letterSpacing: 2,
  },
  onlineBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  onlineText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#10B981',
  },
  heroSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginVertical: 2,
  },
  shieldBadge: {
    width: 48,
    height: 48,
    borderRadius: 15,
    backgroundColor: colors.primaryGreen,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.primaryGreen,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.18,
    shadowRadius: 6,
    elevation: 3,
  },
  shieldIcon: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: '900',
  },
  heroTextContainer: {
    gap: 0,
  },
  heroSubText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  heroMainText: {
    fontSize: 24,
    fontWeight: '900',
    color: colors.primaryGreen,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.04)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 2,
    gap: 10,
  },
  vehicleCardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  carImageWrapper: {
    width: 125,
    height: 78,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 2,
  },
  carImage: {
    width: '100%',
    height: '100%',
  },
  vehicleDetails: {
    flex: 1,
    gap: 6,
  },
  vehicleTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  vehicleName: {
    fontSize: 15,
    fontWeight: '800',
    color: '#111827',
  },
  vehicleId: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  statusPill: {
    backgroundColor: colors.primaryGreenLight,
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  statusPillText: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.greenText,
  },
  syncText: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: '800',
    color: '#9CA3AF',
    letterSpacing: 1.5,
  },
  safetyGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 4,
  },
  metricItem: {
    alignItems: 'center',
    flex: 1,
    gap: 4,
  },
  metricIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 2,
  },
  metricEmoji: {
    fontSize: 20,
  },
  metricLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#374151',
  },
  metricStatusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statusMiniDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  metricStatusText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  metricDivider: {
    width: 1,
    height: 38,
    backgroundColor: '#F3F4F6',
  },
  locationHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  locationIconWrapper: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  locationTitleWrapper: {
    flex: 1,
  },
  locationTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#111827',
  },
  locationCoords: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: '500',
    marginTop: 2,
  },
  chevron: {
    fontSize: 22,
    color: '#9CA3AF',
    fontWeight: '300',
  },
  mapTextureWrapper: {
    height: 96,
    borderRadius: 14,
    overflow: 'hidden',
    position: 'relative',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  mapTextureImage: {
    width: '100%',
    height: '100%',
  },
  centerPinContainer: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -30 }, { translateY: -30 }],
    alignItems: 'center',
    justifyContent: 'center',
  },
  pinAuraOuter: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(16, 185, 129, 0.16)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  pinAuraInner: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(16, 185, 129, 0.32)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  teardropPin: {
    width: 24,
    height: 24,
    backgroundColor: '#0F5132',
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
    borderBottomLeftRadius: 12,
    borderBottomRightRadius: 0,
    transform: [{ rotate: '-45deg' }, { translateY: -2 }],
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
  teardropDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: '#FFFFFF',
  },
  miniTeardropPin: {
    width: 18,
    height: 18,
    backgroundColor: '#0F5132',
    borderTopLeftRadius: 9,
    borderTopRightRadius: 9,
    borderBottomLeftRadius: 9,
    borderBottomRightRadius: 0,
    transform: [{ rotate: '-45deg' }, { translateY: -1 }],
    alignItems: 'center',
    justifyContent: 'center',
  },
  miniTeardropDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: '#FFFFFF',
  },
  viewLocationBtn: {
    backgroundColor: colors.primaryGreen,
    borderRadius: 22,
    paddingVertical: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  viewLocationBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  activityHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  activityTitleGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  activityTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#111827',
  },
  viewAllText: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  activityBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: 'rgba(34, 197, 94, 0.2)',
    borderRadius: 12,
    padding: 10,
  },
  activityCheckCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.primaryGreenLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activityBannerTexts: {
    flex: 1,
  },
  activityStatusBold: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.primaryGreen,
  },
  activityStatusSub: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 1,
  },
  controlButtonsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 2,
  },
  pillButton: {
    flex: 1,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  disarmPill: {
    backgroundColor: colors.primaryGreen,
  },
  disarmPillText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
  },
  trustedPill: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: colors.primaryGreen,
  },
  trustedPillText: {
    color: colors.primaryGreen,
    fontSize: 12,
    fontWeight: '800',
  },
});
