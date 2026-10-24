// components/IncidentCard.jsx
import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  Linking,
  Platform,
  Modal,
} from 'react-native';
import { colors } from '../utils/theme';
import { getSnapshotUrl, getVideoUrl, getDownloadUrl } from '../utils/api';
import LocationPin from './LocationPin';

export default function IncidentCard({ incident }) {
  if (!incident) return null;

  const [previewOpen, setPreviewOpen] = useState(false);

  const imageId = incident.image_id;
  const videoId = incident.video_id;

  const imageUrl = imageId ? getSnapshotUrl(imageId) : null;
  const videoUrl = videoId ? getVideoUrl(videoId) : null;
  const imageDownloadUrl = imageId ? getDownloadUrl(imageId) : null;
  const videoDownloadUrl = videoId ? getDownloadUrl(videoId) : null;

  const conf = incident.confidence ? `${(parseFloat(incident.confidence) * 100).toFixed(0)}%` : '95%';
  const duration = incident.duration_seconds ? `${incident.duration_seconds}s` : '3.0s';
  const time = incident.timestamp ? incident.timestamp.replace('T', ' ').slice(0, 19) : 'Just now';

  const gps = incident.gps || {};
  const locationName = gps.location_name || 'Solapur-Mangalore Highway, Moodabidri, Karnataka';
  const lat = gps.latitude || gps.lat || 13.044266;
  const lng = gps.longitude || gps.lng || 74.977950;
  const mapsUrl = gps.google_maps_url || `https://www.google.com/maps?q=${lat},${lng}`;

  const handleDownload = (url, defaultName) => {
    if (!url) return;
    if (Platform.OS === 'web') {
      const a = document.createElement('a');
      a.href = url;
      a.download = defaultName || 'evidence_file';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } else {
      Linking.openURL(url).catch(() => {});
    }
  };

  const handleOpenMaps = () => {
    Linking.openURL(mapsUrl).catch(() => {});
  };

  const handleWatchVideo = () => {
    if (videoUrl) {
      Linking.openURL(videoUrl).catch(() => {});
    }
  };

  return (
    <View style={styles.card}>
      {/* 1. Header Row */}
      <View style={styles.headerRow}>
        <View style={styles.badgeRow}>
          <View style={styles.redDot} />
          <Text style={styles.alertType}>UNAUTHORIZED INTRUDER</Text>
        </View>
        <Text style={styles.timeText}>{time}</Text>
      </View>

      {/* 2. Photo & Key Details Row */}
      <View style={styles.contentRow}>
        {/* Snapshot Thumbnail with zoom click */}
        <TouchableOpacity
          style={styles.imageContainer}
          activeOpacity={0.85}
          onPress={() => imageUrl && setPreviewOpen(true)}
        >
          {imageUrl ? (
            <Image source={{ uri: imageUrl }} style={styles.thumbnail} resizeMode="cover" />
          ) : (
            <View style={styles.placeholder}>
              <Text style={{ fontSize: 28 }}>📸</Text>
            </View>
          )}
          <View style={styles.zoomHintBadge}>
            <Text style={styles.zoomHintText}>🔍 Zoom</Text>
          </View>
        </TouchableOpacity>

        {/* Stats */}
        <View style={styles.detailsCol}>
          <Text style={styles.statLine}>
            Confidence: <Text style={styles.statBold}>{conf} Match</Text>
          </Text>
          <Text style={styles.statLine}>
            Duration: <Text style={styles.statBold}>{duration} in Driver Seat</Text>
          </Text>
          <View style={styles.locationWrapper}>
            <LocationPin size="xs" color="#0F5132" />
            <Text style={styles.locationLine} numberOfLines={2}>
              {locationName}
            </Text>
          </View>
          <Text style={styles.coordsLine}>
            {Number(lat).toFixed(6)}, {Number(lng).toFixed(6)}
          </Text>
        </View>
      </View>

      {/* 3. Action Buttons Row (Download Image, Watch Video, Download Video, Map) */}
      <View style={styles.actionsGrid}>
        {/* Download Image Button */}
        {imageId && (
          <TouchableOpacity
            style={styles.downloadBtn}
            onPress={() => handleDownload(imageDownloadUrl, imageId)}
            activeOpacity={0.8}
          >
            <Text style={styles.downloadBtnText}>⬇️  Download Photo</Text>
          </TouchableOpacity>
        )}

        {/* Watch Video Button */}
        {videoId && (
          <TouchableOpacity
            style={styles.watchVideoBtn}
            onPress={handleWatchVideo}
            activeOpacity={0.8}
          >
            <Text style={styles.watchVideoBtnText}>▶️  Watch Video</Text>
          </TouchableOpacity>
        )}

        {/* Download Video Button */}
        {videoId && (
          <TouchableOpacity
            style={styles.downloadVideoBtn}
            onPress={() => handleDownload(videoDownloadUrl, videoId)}
            activeOpacity={0.8}
          >
            <Text style={styles.downloadVideoBtnText}>⬇️  Download Video</Text>
          </TouchableOpacity>
        )}

        {/* Map Button */}
        <TouchableOpacity
          style={styles.mapBtn}
          onPress={handleOpenMaps}
          activeOpacity={0.8}
        >
          <Text style={styles.mapBtnText}>🗺️  Google Maps</Text>
        </TouchableOpacity>
      </View>

      {/* Full Photo Preview Modal */}
      {imageUrl && (
        <Modal visible={previewOpen} transparent={true} animationType="fade">
          <View style={styles.modalOverlay}>
            <View style={styles.modalCard}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Intruder Evidence Snapshot</Text>
                <TouchableOpacity onPress={() => setPreviewOpen(false)} style={styles.modalCloseBtn}>
                  <Text style={{ fontSize: 16, fontWeight: '800' }}>✕</Text>
                </TouchableOpacity>
              </View>
              <Image source={{ uri: imageUrl }} style={styles.fullImage} resizeMode="contain" />
              <TouchableOpacity
                style={styles.modalDownloadBtn}
                onPress={() => handleDownload(imageDownloadUrl, imageId)}
              >
                <Text style={styles.modalDownloadBtnText}>⬇️  Download Full Resolution Photo</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.06)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 2,
    gap: 12,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
    paddingBottom: 8,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  redDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.crimson,
  },
  alertType: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.crimson,
    letterSpacing: 0.5,
  },
  timeText: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  contentRow: {
    flexDirection: 'row',
    gap: 12,
  },
  imageContainer: {
    width: 110,
    height: 95,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#F3F4F6',
    position: 'relative',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  thumbnail: {
    width: '100%',
    height: '100%',
  },
  placeholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  zoomHintBadge: {
    position: 'absolute',
    bottom: 4,
    right: 4,
    backgroundColor: 'rgba(0,0,0,0.65)',
    borderRadius: 6,
    paddingHorizontal: 5,
    paddingVertical: 2,
  },
  zoomHintText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '700',
  },
  detailsCol: {
    flex: 1,
    gap: 4,
    justifyContent: 'center',
  },
  statLine: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  statBold: {
    color: colors.textPrimary,
    fontWeight: '700',
  },
  locationWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    marginTop: 2,
  },
  locationLine: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.primaryGreen,
    flex: 1,
  },
  coordsLine: {
    fontSize: 10,
    color: colors.textMuted,
    fontFamily: 'monospace',
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    paddingTop: 10,
  },
  downloadBtn: {
    backgroundColor: colors.primaryGreenLight,
    borderWidth: 1,
    borderColor: colors.primaryGreen,
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  downloadBtnText: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.primaryGreen,
  },
  watchVideoBtn: {
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: colors.amber,
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  watchVideoBtnText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#92400E',
  },
  downloadVideoBtn: {
    backgroundColor: '#EFF6FF',
    borderWidth: 1,
    borderColor: '#3B82F6',
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  downloadVideoBtnText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#1D4ED8',
  },
  mapBtn: {
    backgroundColor: '#F3F4F6',
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  mapBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textSecondary,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  modalCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    width: '100%',
    maxWidth: 540,
    gap: 12,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.textPrimary,
  },
  modalCloseBtn: {
    padding: 4,
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
  },
  fullImage: {
    width: '100%',
    height: 320,
    borderRadius: 12,
    backgroundColor: '#000',
  },
  modalDownloadBtn: {
    backgroundColor: colors.primaryGreen,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
  },
  modalDownloadBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
});
