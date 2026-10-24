// hooks/useVehicleState.js
import { useState, useEffect } from 'react';
import { useSocket } from './useSocket';
import { sendLocalNotification } from '../utils/notifications';
import { EVENTS } from '../utils/socketEvents';
import { BACKEND, getSecurityState, postSecurityCommand } from '../utils/api';

// Global shared state across all dashboard tabs and components
let globalState = {
  securityMode:     'ARMED',
  alarmActive:      false,
  lastIncident:     null,
  gpsCoords: {
    lat: 13.044074,
    lng: 74.977508,
    heading: 270,
    speed: 0,
    location_name: 'Solapur-Mangalore Highway, Moodabidri, Karnataka',
    google_maps_url: 'https://www.google.com/maps?q=13.044074,74.977508'
  },
  connectionStatus: 'connecting',
};

const listeners = new Set();
let lastUserActionTime = 0;

function notifyListeners() {
  for (const listener of listeners) {
    try {
      listener({ ...globalState });
    } catch (e) {}
  }
}

function setSharedState(patch) {
  const next = typeof patch === 'function' ? patch(globalState) : patch;
  let hasChange = false;

  for (const k of Object.keys(next)) {
    if (k === 'gpsCoords') {
      const oldGps = globalState.gpsCoords || {};
      const newGps = next.gpsCoords || {};
      if (
        oldGps.lat !== newGps.lat ||
        oldGps.lng !== newGps.lng ||
        oldGps.speed !== newGps.speed ||
        oldGps.location_name !== newGps.location_name
      ) {
        hasChange = true;
      }
    } else if (globalState[k] !== next[k]) {
      hasChange = true;
    }
  }

  if (hasChange) {
    globalState = { ...globalState, ...next };
    notifyListeners();
  }
}

export function useVehicleState() {
  const [state, setState] = useState({ ...globalState });
  const socket = useSocket();

  // 0. Live device/browser geolocation detection
  useEffect(() => {
    if (typeof navigator !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = parseFloat(pos.coords.latitude.toFixed(6));
          const lng = parseFloat(pos.coords.longitude.toFixed(6));
          if (lat && lng) {
            const gps = {
              lat,
              lng,
              latitude: lat,
              longitude: lng,
              speed: Math.round(pos.coords.speed || 0),
              heading: Math.round(pos.coords.heading || 270),
              location_name: 'Live Device GPS',
              google_maps_url: `https://www.google.com/maps?q=${lat},${lng}`,
            };
            setSharedState({ gpsCoords: gps });
            fetch(`${BACKEND}/api/gps`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(gps),
            }).catch(() => {});
          }
        },
        () => {},
        { enableHighAccuracy: true, timeout: 4000 }
      );
    }
  }, []);

  // Subscribe to shared state updates
  useEffect(() => {
    listeners.add(setState);
    return () => {
      listeners.delete(setState);
    };
  }, []);

  // 1. Initial State Sync & Background Polling
  useEffect(() => {
    let mounted = true;

    const syncState = async () => {
      const data = await getSecurityState();
      if (!mounted || !data) return;

      const isRecentlyClicked = (Date.now() - lastUserActionTime) < 5000;
      const serverMode = data.state;
      const isAlarm = serverMode === 'ALARM' || Boolean(data.alarmActive);

      setSharedState(s => ({
        securityMode: serverMode || s.securityMode,
        alarmActive: isAlarm,
        gpsCoords: data.coords ? { ...s.gpsCoords, ...data.coords } : s.gpsCoords,
        connectionStatus: 'connected'
      }));
    };

    syncState();
    const interval = setInterval(syncState, 2000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // 2. Real-time WebSocket Listeners
  useEffect(() => {
    if (!socket) return;

    if (socket.connected) {
      setSharedState({ connectionStatus: 'connected' });
    }

    const onConnect = () => setSharedState({ connectionStatus: 'connected' });
    const onDisconnect = () => setSharedState({ connectionStatus: 'disconnected' });
    const onConnectError = () => setSharedState({ connectionStatus: 'disconnected' });

    const onAlarmTriggered = (data) => {
      const gps = data.gps ? {
        lat: data.gps.latitude || data.gps.lat || 13.044266,
        lng: data.gps.longitude || data.gps.lng || 74.977950,
        speed: data.gps.speed || 0,
        heading: data.gps.heading || 0,
        location_name: data.gps.location_name || '',
        google_maps_url: data.gps.google_maps_url || ''
      } : null;

      setSharedState(s => ({
        ...s,
        alarmActive: true,
        lastIncident: data,
        securityMode: 'ALARM',
        ...(gps ? { gpsCoords: gps } : {})
      }));
      sendLocalNotification('🚨 INTRUDER ALERT!', 'Unauthorized person detected in your vehicle!');
    };

    const onIncidentUpdated = (updatedIncident) => {
      setSharedState(s => ({
        ...s,
        lastIncident: { ...s.lastIncident, ...updatedIncident }
      }));
    };

    const onAlarmSilenced = () => {
      setSharedState({ alarmActive: false });
    };

    const onSecurityStateChange = (data) => {
      const mode = data.state || data.mode;
      if (!mode) return;

      if (mode === 'ALARM') {
        setSharedState({ securityMode: 'ALARM', alarmActive: true });
      } else {
        setSharedState({ securityMode: mode, alarmActive: false });
      }
    };

    const onGpsUpdate = (coords) => {
      setSharedState(s => ({ ...s, gpsCoords: coords }));
    };

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('connect_error', onConnectError);
    socket.on(EVENTS.ALARM_TRIGGERED, onAlarmTriggered);
    socket.on('incident_updated', onIncidentUpdated);
    socket.on(EVENTS.ALARM_SILENCED, onAlarmSilenced);
    socket.on(EVENTS.SECURITY_STATE_CHANGE, onSecurityStateChange);
    socket.on(EVENTS.GPS_UPDATE, onGpsUpdate);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('connect_error', onConnectError);
      socket.off(EVENTS.ALARM_TRIGGERED, onAlarmTriggered);
      socket.off('incident_updated', onIncidentUpdated);
      socket.off(EVENTS.ALARM_SILENCED, onAlarmSilenced);
      socket.off(EVENTS.SECURITY_STATE_CHANGE, onSecurityStateChange);
      socket.off(EVENTS.GPS_UPDATE, onGpsUpdate);
    };
  }, [socket]);

  // 3. Instant Zero-Lag Command Execution
  const sendCommand = (command) => {
    lastUserActionTime = Date.now();

    let targetMode = 'ARMED';
    let targetAlarm = false;

    if (command === 'DISARM') {
      targetMode = 'DISARMED';
      targetAlarm = false;
    } else if (command === 'TRUSTED_DRIVER' || command === 'TRUSTED_DRIVER_ON') {
      targetMode = 'TRUSTED_DRIVER';
      targetAlarm = false;
    } else if (command === 'SILENCE_ALARM') {
      targetMode = 'ARMED';
      targetAlarm = false;
    } else if (command === 'ARM') {
      targetMode = 'ARMED';
      targetAlarm = false;
    }

    // 0ms Instant Local Update across all listening screens & components
    setSharedState({
      securityMode: targetMode,
      alarmActive: targetAlarm
    });

    // Send immediately via WebSocket
    if (socket) {
      socket.emit(EVENTS.OWNER_COMMAND, { command, vehicleId: 'veh_01' });
    }

    // Send immediately via REST (guaranteed delivery)
    postSecurityCommand(command);
  };

  return { ...state, sendCommand };
}


