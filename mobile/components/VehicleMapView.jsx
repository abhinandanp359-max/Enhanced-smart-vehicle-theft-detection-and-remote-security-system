// components/VehicleMapView.jsx
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Text, Platform, Image, TouchableOpacity, Linking } from 'react-native';
import { colors } from '../utils/theme';
import LocationPin from './LocationPin';

let MapView, Marker, Polyline, Circle;
try {
  const Maps = require('react-native-maps');
  MapView = Maps.default;
  Marker = Maps.Marker;
  Polyline = Maps.Polyline;
  Circle = Maps.Circle;
} catch (e) {
  // Native map fallback for web or non-native platforms
}

const HOME = { latitude: 13.044074, longitude: 74.977508 };
const TRAIL_MAX = 50;

export default function VehicleMapView({ gpsCoords, alarmActive }) {
  const [trail, setTrail] = useState([HOME]);
  const lat = gpsCoords?.lat || HOME.latitude;
  const lng = gpsCoords?.lng || HOME.longitude;
  const position = { latitude: lat, longitude: lng };

  useEffect(() => {
    if (gpsCoords?.lat && gpsCoords?.lng) {
      setTrail(prev => {
        const next = [...prev, position];
        return next.length > TRAIL_MAX ? next.slice(-TRAIL_MAX) : next;
      });
    }
  }, [gpsCoords?.lat, gpsCoords?.lng]);

  const mapsUrl = gpsCoords?.google_maps_url || `https://www.google.com/maps?q=${lat},${lng}`;

  // Native React Native Maps (iOS / Android)
  if (MapView && Platform.OS !== 'web') {
    return (
      <View style={styles.container}>
        <MapView
          style={styles.map}
          initialRegion={{ ...position, latitudeDelta: 0.015, longitudeDelta: 0.015 }}
          region={{ ...position, latitudeDelta: 0.015, longitudeDelta: 0.015 }}
          mapType="standard"
        >
          <Marker
            coordinate={position}
            title="Vehicle veh_01"
            description={`Speed: ${gpsCoords?.speed || 0} km/h | Heading: ${gpsCoords?.heading || 0}°`}
          >
            {/* Custom teardrop pin with subtle aura */}
            <LocationPin size="lg" withAura color="#0F5132" alarm={alarmActive} />
          </Marker>
          <Polyline
            coordinates={trail}
            strokeColor={colors.primaryGreen}
            strokeWidth={3}
            lineDashPattern={[6, 4]}
          />
          <Circle
            center={HOME}
            radius={500}
            strokeColor={colors.primaryGreen}
            fillColor="rgba(19, 111, 72, 0.08)"
            strokeWidth={1.5}
          />
        </MapView>
      </View>
    );
  }

  // Web / Fallback Interactive Display with Teardrop Pin and HUD
  return (
    <View style={styles.webMapContainer}>
      {/* Background Map Imagery */}
      <Image
        source={require('../assets/map_texture.jpg')}
        style={styles.webMapImage}
        resizeMode="cover"
      />

      {/* Grid Overlay Texture for high-tech GPS feel */}
      <View style={styles.gridOverlay} />

      {/* Geofence Safe Radius Perimeter */}
      <View style={styles.geofenceCircle}>
        <Text style={styles.geofenceTag}>500m Safe Zone</Text>
      </View>

      {/* Center Location Symbol with Subtle Circular Highlight */}
      <View style={styles.centerPinWrapper}>
        <LocationPin size="lg" withAura color="#0F5132" alarm={alarmActive} />
        <View style={styles.calloutPill}>
          <Text style={styles.calloutText}>
            {alarmActive ? '🚨 ALERT: VEH_01' : '🚗 Modern SUV • veh_01'}
          </Text>
        </View>
      </View>

      {/* Live Telemetry Overlay HUD */}
      <View style={styles.hudCard}>
        <View style={styles.hudRow}>
          <View style={styles.hudMetric}>
            <Text style={styles.hudLabel}>SATELLITE LOCK</Text>
            <Text style={styles.hudValue}>14 SATS (RTK FIX)</Text>
          </View>
          <View style={styles.hudMetric}>
            <Text style={styles.hudLabel}>SPEED</Text>
            <Text style={styles.hudValue}>{gpsCoords?.speed || 0} km/h</Text>
          </View>
          <View style={styles.hudMetric}>
            <Text style={styles.hudLabel}>HEADING</Text>
            <Text style={styles.hudValue}>{gpsCoords?.heading || 270}° W</Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.openExternalBtn}
          onPress={() => Linking.openURL(mapsUrl).catch(() => {})}
          activeOpacity={0.85}
        >
          <Text style={styles.openExternalText}>
            🌐 View Full Satellite Navigation on Google Maps
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
  webMapContainer: {
    flex: 1,
    position: 'relative',
    overflow: 'hidden',
    backgroundColor: '#E8ECEF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  webMapImage: {
    ...StyleSheet.absoluteFillObject,
    width: '100%',
    height: '100%',
  },
  gridOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(244, 246, 248, 0.35)',
  },
  geofenceCircle: {
    width: 280,
    height: 280,
    borderRadius: 140,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: 'rgba(16, 185, 129, 0.45)',
    backgroundColor: 'rgba(16, 185, 129, 0.05)',
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingTop: 10,
  },
  geofenceTag: {
    fontSize: 10,
    fontWeight: '800',
    color: colors.primaryGreen,
    letterSpacing: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  centerPinWrapper: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  calloutPill: {
    marginTop: 6,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  calloutText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#111827',
  },
  hudCard: {
    position: 'absolute',
    bottom: 20,
    left: 16,
    right: 16,
    maxWidth: 500,
    alignSelf: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.08)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 4,
    gap: 10,
  },
  hudRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  hudMetric: {
    alignItems: 'center',
  },
  hudLabel: {
    fontSize: 9,
    fontWeight: '800',
    color: colors.textMuted,
    letterSpacing: 1,
    marginBottom: 2,
  },
  hudValue: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.primaryGreen,
    fontFamily: 'monospace',
  },
  openExternalBtn: {
    backgroundColor: colors.primaryGreenLight,
    paddingVertical: 9,
    borderRadius: 10,
    alignItems: 'center',
  },
  openExternalText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.primaryGreen,
  },
});
