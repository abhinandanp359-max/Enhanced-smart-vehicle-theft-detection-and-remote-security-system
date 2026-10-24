// utils/api.js
import axios from 'axios';
import { Platform } from 'react-native';
import Constants from 'expo-constants';

const getBackendUrl = () => {
  if (Platform.OS === 'web' && typeof window !== 'undefined' && window.location) {
    const host = window.location.hostname || 'localhost';
    return `http://${host}:5000`;
  }

  // Dynamically resolve host IP from Expo dev server if running on LAN
  const hostUri = Constants.expoConfig?.hostUri || Constants.manifest2?.extra?.expoClient?.hostUri || '';
  if (hostUri && !hostUri.includes('exp.direct')) {
    const host = hostUri.split(':')[0];
    if (host) return `http://${host}:5000`;
  }

  // Active PC Wi-Fi IP address
  return 'http://172.21.211.170:5000';
};

export const BACKEND = getBackendUrl();

const api = axios.create({ baseURL: BACKEND, timeout: 8000 });

export const getSecurityState = async () => {
  try {
    const res = await api.get('/api/security/state');
    return res.data;
  } catch (err) {
    return null;
  }
};

export const postSecurityCommand = async (command) => {
  try {
    const res = await api.post('/api/security/command', { command });
    return res.data;
  } catch (err) {
    return null;
  }
};

export const getIncidents = async () => {
  try {
    const res = await api.get('/api/incidents');
    return res.data || [];
  } catch (err) {
    console.warn('[API] Could not fetch incidents from backend:', err.message);
    return [];
  }
};

export const getIncidentById = async (id) => {
  try {
    const res = await api.get(`/api/incidents/${id}`);
    return res.data;
  } catch (err) {
    console.warn(`[API] Could not fetch incident ${id}:`, err.message);
    return null;
  }
};

export const acknowledgeIncident = async (id) => {
  try {
    const res = await api.patch(`/api/incidents/${id}/acknowledge`);
    return res.data;
  } catch (err) {
    console.warn(`[API] Could not acknowledge incident ${id}:`, err.message);
    return null;
  }
};

export const getSnapshotUrl = (filename) => `${BACKEND}/api/evidence/snapshot/${filename}`;
export const getVideoUrl = (filename) => `${BACKEND}/api/evidence/video/${filename}`;
export const getDownloadUrl = (filename) => `${BACKEND}/api/evidence/download/${filename}`;

// Siren Remote Control
export const postSirenCommand = async (action) => {
  try {
    const res = await api.post('/api/security/siren', { action });
    return res.data;
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message || 'Siren command failed');
  }
};

// Camera Live Stream & Telemetry
export const getCameraStatus = async () => {
  try {
    const res = await api.get('/api/camera/status');
    return res.data;
  } catch (err) {
    return { connected: false, fps: 0, error: err.message };
  }
};

export const captureEvidenceSnapshot = async () => {
  try {
    const res = await api.post('/api/camera/capture');
    return res.data;
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message || 'Snapshot capture failed');
  }
};

export const getCameraStreamUrl = () => `${BACKEND}/api/camera/stream`;
export const getLatestCameraFrameUrl = () => `${BACKEND}/api/camera/latest?_t=${Date.now()}`;

export const getVehicleProfile = async () => {
  try {
    const res = await api.get('/api/vehicle/profile');
    return res.data;
  } catch (err) {
    return null;
  }
};

export const saveVehicleProfile = async (profileData) => {
  try {
    const res = await api.post('/api/vehicle/profile', profileData);
    return res.data;
  } catch (err) {
    return null;
  }
};

