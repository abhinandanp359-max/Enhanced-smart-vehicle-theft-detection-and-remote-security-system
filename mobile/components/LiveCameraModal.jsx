// components/LiveCameraModal.jsx
import React, { useState, useEffect, useRef } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Image,
  Alert,
  Platform,
  ScrollView,
} from 'react-native';
import { colors } from '../utils/theme';
import { useSocket } from '../hooks/useSocket';
import {
  getCameraStatus,
  captureEvidenceSnapshot,
  getLatestCameraFrameUrl,
} from '../utils/api';

export default function LiveCameraModal({ visible, onClose, securityMode, alarmActive }) {
  const socket = useSocket();
  const [loading, setLoading] = useState(true);
  const [cameraStatus, setCameraStatus] = useState(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [liveBase64, setLiveBase64] = useState(null);
  const [latestFrameUri, setLatestFrameUri] = useState(null);
  const [fpsCounter, setFpsCounter] = useState(0);
  const frameCountRef = useRef(0);
  const lastSocketFrameTimeRef = useRef(0);
  const [isLiveStreamActive, setIsLiveStreamActive] = useState(false);

  const checkStatus = async () => {
    try {
      const status = await getCameraStatus();
      setCameraStatus(status);
      if (!liveBase64) {
        setLatestFrameUri(getLatestCameraFrameUrl());
      }
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!visible) return;

    setLoading(true);
    checkStatus();

    // 1. High-speed WebSocket Real-Time Frame Listener
    if (socket) {
      // Request current frame from backend right away
      socket.emit('request_camera_frame');

      const handleCameraFrame = (data) => {
        if (data && data.image_base64) {
          setLiveBase64(data.image_base64);
          setLoading(false);
          lastSocketFrameTimeRef.current = Date.now();
          frameCountRef.current += 1;
          setIsLiveStreamActive(true);
        }
      };
      socket.on('camera_frame', handleCameraFrame);

      return () => {
        socket.off('camera_frame', handleCameraFrame);
      };
    }
  }, [visible, socket]);

  // 2. FPS Calculation & Liveness Monitor
  useEffect(() => {
    if (!visible) return;

    const fpsInterval = setInterval(() => {
      setFpsCounter(frameCountRef.current);
      frameCountRef.current = 0;

      // Check if live socket stream is active
      const isStillLive = Date.now() - lastSocketFrameTimeRef.current < 2500;
      setIsLiveStreamActive(isStillLive);

      // If no socket frames arriving, refresh status & snapshot gently
      if (!isStillLive) {
        checkStatus();
      }
    }, 1000);

    return () => {
      clearInterval(fpsInterval);
    };
  }, [visible]);

  const handleManualCapture = async () => {
    if (isCapturing) return;
    setIsCapturing(true);
    try {
      await captureEvidenceSnapshot();
      Alert.alert(
        '📸 Evidence Captured',
        'High-resolution security snapshot saved to the Vehicle Evidence Vault.',
        [{ text: 'OK', style: 'default' }]
      );
      checkStatus();
    } catch (err) {
      Alert.alert('Capture Notice', err.message || 'Unable to capture snapshot at this time.');
    } finally {
      setIsCapturing(false);
    }
  };

  if (!visible) return null;

  const isConnected = Boolean(liveBase64 || latestFrameUri);

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={styles.modalScreen}>
        <ScrollView style={styles.scroll} contentContainerStyle={styles.container}>
          {/* Header */}
          <View style={styles.topHeader}>
            <TouchableOpacity style={styles.closeBtn} onPress={onClose} activeOpacity={0.8}>
              <Text style={styles.closeBtnText}>✕  Close</Text>
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Cabin Monitoring</Text>
            <View style={styles.statusPillWrapper}>
              <View
                style={[
                  styles.statusPillDot,
                  { backgroundColor: isLiveStreamActive ? '#10B981' : isConnected ? '#F59E0B' : '#EF4444' },
                ]}
              />
              <Text style={styles.statusPillText}>
                {isLiveStreamActive ? 'LIVE FEED' : isConnected ? 'STANDBY' : 'OFFLINE'}
              </Text>
            </View>
          </View>

          {/* Viewport Card */}
          <View style={styles.viewportCard}>
            {liveBase64 ? (
              // Real-Time Socket Stream (Native Base64)
              <View style={styles.streamWrapper}>
                <Image
                  source={{ uri: `data:image/jpeg;base64,${liveBase64}` }}
                  style={styles.streamImage}
                  resizeMode="cover"
                />
                <View style={styles.recBadge}>
                  <View style={[styles.recDot, { backgroundColor: isLiveStreamActive ? '#EF4444' : '#F59E0B' }]} />
                  <Text style={styles.recText}>
                    {isLiveStreamActive
                      ? `LIVE • ${fpsCounter > 0 ? fpsCounter : 8} FPS`
                      : 'STANDBY • LAST FRAME'}
                  </Text>
                </View>
              </View>
            ) : latestFrameUri ? (
              // Verified Snapshot Fallback
              <View style={styles.streamWrapper}>
                <Image
                  source={{ uri: latestFrameUri }}
                  style={styles.streamImage}
                  resizeMode="cover"
                />
                <View style={styles.recBadge}>
                  <View style={[styles.recDot, { backgroundColor: '#10B981' }]} />
                  <Text style={styles.recText}>CABIN CAM • STANDBY</Text>
                </View>
              </View>
            ) : (
              // Initializing View
              <View style={styles.viewportPlaceholder}>
                <ActivityIndicator size="large" color={colors.primaryGreen} />
                <Text style={styles.placeholderText}>Connecting to Vehicle Camera...</Text>
              </View>
            )}

            {/* Viewfinder Telemetry Bar */}
            <View style={styles.viewfinderBar}>
              <View style={styles.viewfinderCol}>
                <Text style={styles.viewfinderLabel}>SOURCE</Text>
                <Text style={styles.viewfinderVal}>CABIN LENS 1</Text>
              </View>
              <View style={styles.viewfinderCol}>
                <Text style={styles.viewfinderLabel}>AI ENGINE</Text>
                <Text style={styles.viewfinderVal}>YOLOv8 + YuNet</Text>
              </View>
              <View style={styles.viewfinderCol}>
                <Text style={styles.viewfinderLabel}>SECURITY</Text>
                <Text
                  style={[
                    styles.viewfinderVal,
                    alarmActive && { color: colors.crimson, fontWeight: '800' },
                  ]}
                >
                  {alarmActive ? 'ALARM ACTIVE' : securityMode}
                </Text>
              </View>
            </View>
          </View>

          {/* Action Card */}
          <View style={styles.actionCard}>
            <Text style={styles.cardHeader}>CAMERA ACTIONS</Text>

            <TouchableOpacity
              style={[styles.captureBtn, isCapturing && { opacity: 0.6 }]}
              onPress={handleManualCapture}
              disabled={isCapturing}
              activeOpacity={0.85}
            >
              {isCapturing ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <Text style={styles.captureBtnText}>📸  Capture Evidence Snapshot Now</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.refreshBtn}
              onPress={checkStatus}
              activeOpacity={0.8}
            >
              <Text style={styles.refreshBtnText}>🔄  Check Camera Connection</Text>
            </TouchableOpacity>
          </View>

          {/* Info Diagnostic Card */}
          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>AI VISION & BIOMETRICS STATUS</Text>
            <Text style={styles.infoText}>
              • Driver Seat ROI Zone: Monitored 24/7{'\n'}
              • Anti-False-Alarm Threshold: 3.0s sustained presence{'\n'}
              • Intruder Auto-Capture: 1 HD Snapshot + 5s MP4 Video Clip
            </Text>
          </View>
        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalScreen: {
    flex: 1,
    backgroundColor: '#F4F6F8',
  },
  scroll: {
    flex: 1,
  },
  container: {
    padding: 16,
    paddingTop: Platform.OS === 'web' ? 20 : (Platform.OS === 'android' ? 36 : 48),
    paddingBottom: 40,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
    gap: 14,
  },
  topHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  closeBtn: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  closeBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#374151',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#111827',
  },
  statusPillWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  statusPillDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusPillText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#374151',
    letterSpacing: 0.5,
  },
  viewportCard: {
    backgroundColor: '#0F172A',
    borderRadius: 18,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#1E293B',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    elevation: 4,
  },
  viewportPlaceholder: {
    height: 240,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0F172A',
    padding: 20,
  },
  placeholderText: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: '600',
    marginTop: 10,
  },
  streamWrapper: {
    height: 240,
    width: '100%',
    position: 'relative',
    backgroundColor: '#000000',
  },
  streamImage: {
    width: '100%',
    height: '100%',
  },
  recBadge: {
    position: 'absolute',
    top: 10,
    left: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  recDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#EF4444',
  },
  recText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  viewfinderBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 10,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.08)',
  },
  viewfinderCol: {
    alignItems: 'center',
  },
  viewfinderLabel: {
    fontSize: 9,
    fontWeight: '800',
    color: '#64748B',
    letterSpacing: 1,
  },
  viewfinderVal: {
    fontSize: 11,
    fontWeight: '800',
    color: '#F1F5F9',
    marginTop: 2,
    fontFamily: 'monospace',
  },
  actionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
    gap: 12,
  },
  cardHeader: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.textMuted,
    letterSpacing: 1.5,
  },
  captureBtn: {
    backgroundColor: colors.primaryGreen,
    borderRadius: 14,
    paddingVertical: 13,
    alignItems: 'center',
    justifyContent: 'center',
  },
  captureBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
  refreshBtn: {
    backgroundColor: colors.primaryGreenLight,
    borderWidth: 1,
    borderColor: colors.primaryGreen,
    borderRadius: 14,
    paddingVertical: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  refreshBtnText: {
    color: colors.primaryGreen,
    fontSize: 13,
    fontWeight: '700',
  },
  infoCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    gap: 6,
  },
  infoTitle: {
    fontSize: 10,
    fontWeight: '800',
    color: colors.textMuted,
    letterSpacing: 1,
  },
  infoText: {
    fontSize: 11,
    color: colors.textSecondary,
    lineHeight: 18,
  },
});
