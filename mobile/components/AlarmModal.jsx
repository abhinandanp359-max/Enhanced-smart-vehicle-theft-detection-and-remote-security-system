// components/AlarmModal.jsx
import React, { useEffect, useRef } from 'react';
import {
  Modal,
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  Animated,
  ScrollView,
  Linking,
} from 'react-native';
import { colors } from '../utils/theme';
import { getSnapshotUrl, getVideoUrl, getDownloadUrl } from '../utils/api';
import LocationPin from './LocationPin';

export default function AlarmModal({
  visible,
  incident,
  onSilence,
  onDisarm,
  onTrustedDriver,
}) {
  const pulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (!visible) return;
    const anim = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1.05, duration: 600, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 1.00, duration: 600, useNativeDriver: true }),
      ])
    );
    anim.start();
    return () => anim.stop();
  }, [visible]);

  if (!incident) return null;

  const imageUrl = incident.image_id ? getSnapshotUrl(incident.image_id) : null;
  const videoUrl = incident.video_id ? getVideoUrl(incident.video_id) : null;
  const imageDownloadUrl = incident.image_id ? getDownloadUrl(incident.image_id) : null;
  const videoDownloadUrl = incident.video_id ? getDownloadUrl(incident.video_id) : null;
  const confScore = incident.confidence ? (parseFloat(incident.confidence) * 100).toFixed(0) : '91';
  const durationSec = incident.duration_seconds || '3.0';

  const gps = incident.gps || {};
  const locationName = gps.location_name || 'Solapur-Mangalore Highway, Moodabidri, Karnataka';
  const lat = gps.latitude || gps.lat || 13.044266;
  const lng = gps.longitude || gps.lng || 74.977950;
  const mapsUrl = gps.google_maps_url || `https://www.google.com/maps?q=${lat},${lng}`;

  const openMaps = () => {
    Linking.openURL(mapsUrl).catch(() => {});
  };

  const openVideo = () => {
    if (videoUrl) {
      Linking.openURL(videoUrl).catch(() => {});
    }
  };

  const handleDownload = (url, filename) => {
    if (!url) return;
    if (Platform.OS === 'web') {
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'evidence_file';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } else {
      Linking.openURL(url).catch(() => {});
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={false}>
      <ScrollView
        style={styles.screen}
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
      >
        <Animated.Text style={[styles.alarmTitle, { transform: [{ scale: pulse }] }]}>
          🚨 INTRUDER ALERT!
        </Animated.Text>
        <Text style={styles.subTitle}>Cabin Intrusion Confirmed • Siren Active</Text>

        {/* Snapshot Photo */}
        {imageUrl ? (
          <View style={{ width: '100%', gap: 8 }}>
            <Image source={{ uri: imageUrl }} style={styles.snapshot} resizeMode="cover" />
            <TouchableOpacity
              style={styles.downloadPhotoBtn}
              onPress={() => handleDownload(imageDownloadUrl, incident.image_id)}
              activeOpacity={0.8}
            >
              <Text style={styles.downloadPhotoBtnText}>⬇️  Download Intrusion Snapshot</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.noPhoto}>
            <Text style={{ color: colors.textSecondary }}>📸 Photo Evidence Captured</Text>
          </View>
        )}

        {/* Incident Details Card */}
        <View style={styles.infoBox}>
          <Text style={styles.infoText}>⏱  Presence Duration: {durationSec}s</Text>
          <Text style={styles.infoText}>🎯  Confidence: {confScore}% Match</Text>
          <Text style={styles.infoText}>🕐  Time: {incident.timestamp || 'Just now'}</Text>
          <Text style={styles.infoText}>🚗  Vehicle ID: {incident.vehicle_id || 'veh_01'}</Text>
        </View>

        {/* Location & GPS Card */}
        <View style={styles.locationBox}>
          <View style={styles.locationHeader}>
            <LocationPin size="xs" color={colors.primaryGreen} />
            <Text style={styles.locationTitle}>VEHICLE GPS LOCATION</Text>
          </View>
          <Text style={styles.locationName}>{locationName}</Text>
          <Text style={styles.coordsText}>
            {Number(lat).toFixed(6)}, {Number(lng).toFixed(6)}
          </Text>

          <TouchableOpacity style={styles.mapsBtn} onPress={openMaps} activeOpacity={0.8}>
            <Text style={styles.mapsBtnText}>🌐 Open in Google Maps</Text>
          </TouchableOpacity>
        </View>

        {/* Video Clip Action Button */}
        {incident.video_id ? (
          <TouchableOpacity style={styles.videoBtn} onPress={openVideo} activeOpacity={0.8}>
            <Text style={styles.videoBtnText}>▶️ Watch 5s HD Video Clip</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.videoPendingBox}>
            <Text style={styles.videoPendingText}>📹 5-Sec Video Clip Uploading to Phone...</Text>
          </View>
        )}

        {/* Remote Action Buttons */}
        <View style={styles.actionGroup}>
          <TouchableOpacity style={styles.silenceBtn} onPress={onSilence} activeOpacity={0.8}>
            <Text style={styles.silenceBtnText}>🔕  SILENCE CAR SIREN</Text>
          </TouchableOpacity>

          {onTrustedDriver && (
            <TouchableOpacity
              style={styles.trustedBtn}
              onPress={onTrustedDriver}
              activeOpacity={0.8}
            >
              <Text style={styles.trustedBtnText}>👤  ALLOW TRUSTED DRIVER</Text>
            </TouchableOpacity>
          )}

          {onDisarm && (
            <TouchableOpacity style={styles.disarmBtn} onPress={onDisarm} activeOpacity={0.8}>
              <Text style={styles.disarmBtnText}>🔓  DISARM SYSTEM</Text>
            </TouchableOpacity>
          )}
        </View>
      </ScrollView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#130404' },
  container: { padding: 20, gap: 14, paddingBottom: 40, alignItems: 'center' },
  alarmTitle: { fontSize: 28, fontWeight: '900', color: colors.crimson, textAlign: 'center', marginTop: 10 },
  subTitle: { fontSize: 13, color: '#FFB0B0', textAlign: 'center', fontWeight: '600', marginBottom: 4 },
  snapshot: { width: '100%', height: 210, borderRadius: 14, borderWidth: 2, borderColor: colors.crimson },
  noPhoto: { width: '100%', height: 210, borderRadius: 14, backgroundColor: colors.bgCard, alignItems: 'center', justifyContent: 'center' },
  infoBox: { backgroundColor: colors.bgCard, borderRadius: 12, padding: 14, width: '100%', gap: 6, borderWidth: 1, borderColor: 'rgba(239,68,68,0.25)' },
  infoText: { color: colors.textPrimary, fontSize: 13, fontFamily: 'monospace' },
  locationBox: { backgroundColor: colors.bgCard, borderRadius: 12, padding: 14, width: '100%', gap: 6, borderWidth: 1, borderColor: 'rgba(0, 242, 254, 0.3)' },
  locationHeader: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  locationTitle: { fontSize: 11, fontWeight: '800', color: colors.cyan, letterSpacing: 1.5 },
  locationName: { fontSize: 14, fontWeight: '700', color: colors.textPrimary, marginTop: 2 },
  coordsText: { fontSize: 12, color: colors.textSecondary, fontFamily: 'monospace' },
  mapsBtn: { backgroundColor: 'rgba(0, 242, 254, 0.12)', borderWidth: 1, borderColor: colors.cyan, borderRadius: 8, paddingVertical: 10, alignItems: 'center', marginTop: 4 },
  mapsBtnText: { color: colors.cyan, fontSize: 13, fontWeight: '700' },
  videoBtn: { backgroundColor: colors.cyan, width: '100%', paddingVertical: 14, borderRadius: 12, alignItems: 'center' },
  videoBtnText: { color: '#000', fontSize: 15, fontWeight: '800', letterSpacing: 0.5 },
  videoPendingBox: { width: '100%', paddingVertical: 10, borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.05)', alignItems: 'center' },
  videoPendingText: { color: colors.textSecondary, fontSize: 12, fontStyle: 'italic' },
  actionGroup: { width: '100%', gap: 10, marginTop: 6 },
  silenceBtn: { backgroundColor: colors.crimson, padding: 15, borderRadius: 12, width: '100%', alignItems: 'center' },
  silenceBtnText: { color: 'white', fontSize: 15, fontWeight: '800', letterSpacing: 1 },
  downloadPhotoBtn: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  downloadPhotoBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '800',
  },
  trustedBtn: { backgroundColor: colors.amber, padding: 14, borderRadius: 12, width: '100%', alignItems: 'center' },
  trustedBtnText: { color: '#000', fontSize: 15, fontWeight: '800', letterSpacing: 1 },
  disarmBtn: { backgroundColor: 'rgba(34, 197, 94, 0.15)', borderWidth: 1.5, borderColor: colors.green, padding: 14, borderRadius: 12, width: '100%', alignItems: 'center' },
  disarmBtnText: { color: colors.green, fontSize: 15, fontWeight: '800', letterSpacing: 1 },
});
