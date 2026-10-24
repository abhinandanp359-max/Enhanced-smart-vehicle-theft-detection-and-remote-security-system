// app/map.jsx
import React from 'react';
import { View, StyleSheet, Text, TouchableOpacity, Linking, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import VehicleMapView from '../components/VehicleMapView';
import { useVehicleState } from '../hooks/useVehicleState';
import LocationPin from '../components/LocationPin';
import { colors } from '../utils/theme';

export default function MapScreen() {
  const router = useRouter();
  const { gpsCoords, alarmActive } = useVehicleState();

  const isGpsAvailable = Boolean(gpsCoords?.lat && gpsCoords?.lat !== 0);
  const lat = isGpsAvailable ? Number(gpsCoords.lat).toFixed(6) : '13.044074';
  const lng = isGpsAvailable ? Number(gpsCoords.lng).toFixed(6) : '74.977508';
  const mapsUrl = gpsCoords?.google_maps_url || `https://www.google.com/maps?q=${lat},${lng}`;

  const openGoogleMaps = () => {
    Linking.openURL(mapsUrl).catch(() => {});
  };

  return (
    <View style={styles.screen}>
      <View style={styles.banner}>
        <View style={styles.bannerTopRow}>
          <View style={styles.headerLeftGroup}>
            <TouchableOpacity
              style={styles.backBtn}
              onPress={() => router.back()}
              activeOpacity={0.8}
            >
              <Text style={styles.backBtnText}>‹ Back</Text>
            </TouchableOpacity>
            <Text style={styles.bannerTitle}>LIVE SATELLITE TELEMETRY</Text>
          </View>
          <TouchableOpacity style={styles.googleMapsBtn} onPress={openGoogleMaps}>
            <Text style={styles.googleMapsBtnText}>🌐 Open Maps</Text>
          </TouchableOpacity>
        </View>

        {isGpsAvailable ? (
          <>
            <View style={styles.locationRow}>
              <LocationPin size="sm" color="#0F5132" />
              <Text style={styles.bannerLocation} numberOfLines={2}>
                {gpsCoords?.location_name || 'Solapur-Mangalore Highway, Moodabidri, Karnataka'}
              </Text>
            </View>
            <Text style={styles.bannerSub}>
              LAT: {lat} | LNG: {lng} | SPEED: {gpsCoords?.speed || 0} km/h
            </Text>
          </>
        ) : (
          <View style={styles.unavailableWarningBox}>
            <Text style={styles.warningIcon}>⚠️</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.warningTitle}>GPS Signal Searching...</Text>
              <Text style={styles.warningSub}>
                Vehicle satellite link in standby. Reconnecting to telemetry constellation...
              </Text>
            </View>
          </View>
        )}
      </View>
      <VehicleMapView gpsCoords={gpsCoords} alarmActive={alarmActive} />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#F4F6F8' },
  banner: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    paddingTop: Platform.OS === 'web' ? 20 : (Platform.OS === 'android' ? 36 : 46),
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  bannerTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  headerLeftGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  backBtn: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  backBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.primaryGreen,
  },
  bannerTitle: { fontSize: 11, fontWeight: '800', color: colors.primaryGreen, letterSpacing: 1.2 },
  googleMapsBtn: {
    backgroundColor: colors.primaryGreenLight,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  googleMapsBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.primaryGreen,
  },
  bannerLocation: { fontSize: 13, fontWeight: '800', color: '#111827', flex: 1 },
  locationRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginVertical: 4 },
  bannerSub: { fontSize: 11, color: colors.textSecondary, fontFamily: 'monospace' },
  unavailableWarningBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEF3C7',
    padding: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(245, 158, 11, 0.3)',
    marginTop: 4,
  },
  warningIcon: { fontSize: 18 },
  warningTitle: { fontSize: 12, fontWeight: '800', color: '#92400E' },
  warningSub: { fontSize: 10, color: '#B45309' },
});
