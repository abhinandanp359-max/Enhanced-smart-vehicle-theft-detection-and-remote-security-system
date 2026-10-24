/**
 * backend/server.js
 * VehicleGuard AI Real-Time Gateway & REST API
 * Coordinates AI Engine detection events with Mobile App via Socket.io and REST.
 */
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
const server = http.createServer(app);

const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST', 'PATCH', 'OPTIONS'],
  },
  transports: ['websocket', 'polling'],
});

const PORT = process.env.PORT || 5000;
const EVIDENCE_DIR = path.join(__dirname, '..', 'ai_engine', 'evidence');
if (!fs.existsSync(EVIDENCE_DIR)) {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
}

// Multer storage for incoming incident evidence
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, EVIDENCE_DIR),
  filename: (req, file, cb) => {
    // Preserve original filename if provided or generate timestamped name
    cb(null, file.originalname || `incident_${Date.now()}_${file.fieldname}`);
  },
});
const upload = multer({ storage });

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.raw({ type: 'image/jpeg', limit: '10mb' }));

// System Global State
let securityState = 'ARMED'; // ARMED | DISARMED | TRUSTED_DRIVER | ALARM
let alarmActive = false;
let latestCameraFrame = null;
const cameraStreamClients = new Set();
let currentCoords = {
  lat: 13.044074,
  lng: 74.977508,
  latitude: 13.044074,
  longitude: 74.977508,
  heading: 270,
  speed: 0,
  location_name: 'Solapur-Mangalore Highway, Moodabidri, Karnataka',
  google_maps_url: 'https://www.google.com/maps?q=13.044074,74.977508'
};
let incidents = [];

// Load existing incidents from ai_engine/evidence JSON files
function loadSavedIncidents() {
  try {
    if (fs.existsSync(EVIDENCE_DIR)) {
      const files = fs.readdirSync(EVIDENCE_DIR).filter(f => f.endsWith('.json'));
      const list = [];
      for (const file of files) {
        try {
          const raw = fs.readFileSync(path.join(EVIDENCE_DIR, file), 'utf-8');
          const parsed = JSON.parse(raw);
          parsed._id = file.replace('.json', '');
          list.push(parsed);
        } catch (e) {}
      }
      list.sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
      incidents = list;

      // Sync exact GPS coords from most recent incident
      if (incidents.length > 0 && incidents[0].gps) {
        const g = incidents[0].gps;
        const lat = parseFloat(g.latitude || g.lat || 13.044074);
        const lng = parseFloat(g.longitude || g.lng || 74.977508);
        currentCoords = {
          lat,
          lng,
          latitude: lat,
          longitude: lng,
          location_name: g.location_name || 'Solapur-Mangalore Highway, Moodabidri, Karnataka',
          google_maps_url: g.google_maps_url || `https://www.google.com/maps?q=${lat},${lng}`,
          heading: 270,
          speed: 0,
        };
      }

      // Preload initial camera snapshot so phone app shows cabin camera instantly
      if (incidents.length > 0 && incidents[0].image_id) {
        const filePath = path.join(EVIDENCE_DIR, incidents[0].image_id);
        if (fs.existsSync(filePath)) {
          const buf = fs.readFileSync(filePath);
          latestCameraFrame = {
            buffer: buf,
            timestamp: Date.now(),
            isInitialSnapshot: true,
          };
          console.log(`[Backend] Preloaded initial camera snapshot: ${incidents[0].image_id}`);
        }
      }
    }
  } catch (err) {
    console.error('[Backend] Error scanning evidence files:', err.message);
  }
}
loadSavedIncidents();

// --- REST Endpoints ---

// 1. Health check & Security state
app.get('/api/health', (req, res) => {
  res.json({ status: 'online', service: 'VehicleGuard Gateway', securityState });
});

app.get('/api/security/state', (req, res) => {
  res.json({ state: securityState, alarmActive, coords: currentCoords });
});

// Update live GPS coordinates dynamically
app.post('/api/gps', (req, res) => {
  const { lat, lng, latitude, longitude, location_name, speed, heading } = req.body;
  const newLat = parseFloat(lat || latitude || currentCoords.lat);
  const newLng = parseFloat(lng || longitude || currentCoords.lng);
  currentCoords = {
    ...currentCoords,
    lat: newLat,
    lng: newLng,
    latitude: newLat,
    longitude: newLng,
    location_name: location_name || currentCoords.location_name,
    google_maps_url: `https://www.google.com/maps?q=${newLat},${newLng}`,
    speed: speed !== undefined ? speed : currentCoords.speed,
    heading: heading !== undefined ? heading : currentCoords.heading,
  };
  io.emit('gps_update', currentCoords);
  res.json({ success: true, coords: currentCoords });
});

// 2. Remote command via REST (mirrors socket command)
app.post('/api/security/command', (req, res) => {
  const { command } = req.body;
  handleCommand(command);
  res.json({ success: true, state: securityState, alarmActive });
});

// Dedicated Siren Remote Control Endpoint
app.post('/api/security/siren', (req, res) => {
  const { action } = req.body;
  if (action === 'activate') {
    handleCommand('TRIGGER_SIREN');
  } else {
    handleCommand('STOP_SIREN');
  }
  res.json({ success: true, alarmActive, state: securityState });
});

// --- Camera Streaming & Live Monitoring Endpoints ---

// Receive live frame from AI Vision Engine
app.post('/api/camera/frame', (req, res) => {
  try {
    let frameBuf = null;
    if (Buffer.isBuffer(req.body)) {
      frameBuf = req.body;
    } else if (req.body && req.body.image_base64) {
      frameBuf = Buffer.from(req.body.image_base64, 'base64');
    }
    if (frameBuf && frameBuf.length > 100) {
      latestCameraFrame = {
        buffer: frameBuf,
        timestamp: Date.now(),
      };

      // Broadcast live base64 frame to mobile app via WebSocket in real-time
      const base64Data = frameBuf.toString('base64');
      io.emit('camera_frame', {
        image_base64: base64Data,
        timestamp: Date.now(),
      });

      // Also pipe to any active MJPEG stream clients
      for (const clientRes of cameraStreamClients) {
        try {
          clientRes.write(`--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ${frameBuf.length}\r\n\r\n`);
          clientRes.write(frameBuf);
          clientRes.write('\r\n');
        } catch (e) {
          cameraStreamClients.delete(clientRes);
        }
      }
      return res.json({ success: true });
    }
    res.status(400).json({ error: 'Invalid frame payload' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Camera Status Check
app.get('/api/camera/status', (req, res) => {
  const isOnline = latestCameraFrame && (Date.now() - latestCameraFrame.timestamp < 15000);
  res.json({
    connected: Boolean(isOnline),
    source: 'Vehicle Cabin Front Camera (Lens 1)',
    fps: isOnline ? 15 : 0,
    lastFrameTime: latestCameraFrame?.timestamp || null,
    hasLatestSnapshot: (incidents.length > 0 && Boolean(incidents[0].image_id)) || Boolean(latestCameraFrame),
    latestSnapshotId: incidents.length > 0 ? incidents[0].image_id : null,
  });
});

// MJPEG Live Stream
app.get('/api/camera/stream', (req, res) => {
  res.setHeader('Content-Type', 'multipart/x-mixed-replace; boundary=--frame');
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.setHeader('Connection', 'close');
  res.setHeader('Pragma', 'no-cache');

  cameraStreamClients.add(res);

  if (latestCameraFrame && latestCameraFrame.buffer) {
    res.write(`--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ${latestCameraFrame.buffer.length}\r\n\r\n`);
    res.write(latestCameraFrame.buffer);
    res.write('\r\n');
  }

  req.on('close', () => {
    cameraStreamClients.delete(res);
  });
});

// Latest Verified Snapshot or Live Frame
app.get('/api/camera/latest', (req, res) => {
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  if (latestCameraFrame && latestCameraFrame.buffer) {
    res.contentType('image/jpeg');
    return res.send(latestCameraFrame.buffer);
  }
  if (incidents.length > 0 && incidents[0].image_id) {
    const filePath = path.join(EVIDENCE_DIR, incidents[0].image_id);
    if (fs.existsSync(filePath)) {
      res.contentType('image/jpeg');
      return res.sendFile(filePath);
    }
  }
  res.status(404).json({ error: 'No camera frame available' });
});

// Capture Evidence Snapshot on Demand
app.post('/api/camera/capture', (req, res) => {
  const filename = `manual_capture_veh_01_${Date.now()}.jpg`;
  const filePath = path.join(EVIDENCE_DIR, filename);

  if (latestCameraFrame && latestCameraFrame.buffer) {
    fs.writeFileSync(filePath, latestCameraFrame.buffer);
  } else if (incidents.length > 0 && incidents[0].image_id) {
    const src = path.join(EVIDENCE_DIR, incidents[0].image_id);
    if (fs.existsSync(src)) {
      fs.copyFileSync(src, filePath);
    }
  } else {
    return res.status(503).json({ success: false, error: 'Vehicle camera stream is offline. Please start the AI engine first.' });
  }

  const newCapture = {
    _id: filename.replace('.jpg', ''),
    event_type: 'manual_owner_capture',
    security_state: securityState,
    vehicle_id: 'veh_01',
    timestamp: new Date().toISOString(),
    confidence: '1.0',
    duration_seconds: '0.0',
    image_id: filename,
    gps: currentCoords,
    hardware_telemetry: {
      siren: alarmActive ? 'ACTIVE_HIGH_DECIBEL' : 'STANDBY',
      camera: 'MANUAL_SNAPSHOT_TRIGGERED',
    }
  };

  incidents.unshift(newCapture);
  io.emit('incident_alert', newCapture);
  res.json({ success: true, capture: newCapture });
});

// 3. Receive incident alert & evidence from AI Engine
app.post('/api/incidents', upload.any(), (req, res) => {
  try {
    let payload = {};
    if (req.body.payload_json) {
      try {
        payload = JSON.parse(req.body.payload_json);
      } catch (e) {
        payload = req.body;
      }
    } else {
      payload = req.body;
    }

    let imageId = payload.image_id || '';
    let videoId = payload.video_id || '';

    if (Array.isArray(req.files)) {
      const snap = req.files.find(f => f.fieldname === 'snapshot' || f.fieldname === 'image');
      if (snap && snap.filename) imageId = snap.filename;
      const vid = req.files.find(f => f.fieldname === 'video');
      if (vid && vid.filename) videoId = vid.filename;
    }

    const timestamp = payload.timestamp || new Date().toISOString();

    let lat = 13.044266;
    let lng = 74.977950;
    let locationName = 'Solapur-Mangalore Highway, Moodabidri, Karnataka';
    let mapsUrl = 'https://www.google.com/maps?q=13.044266,74.977950';

    if (payload.gps) {
      lat = parseFloat(payload.gps.latitude || payload.gps.lat || lat);
      lng = parseFloat(payload.gps.longitude || payload.gps.lng || lng);
      locationName = payload.gps.location_name || locationName;
      mapsUrl = payload.gps.google_maps_url || `https://www.google.com/maps?q=${lat},${lng}`;
    }

    currentCoords = {
      lat,
      lng,
      latitude: lat,
      longitude: lng,
      location_name: locationName,
      google_maps_url: mapsUrl,
      heading: 0,
      speed: 0
    };
    io.emit('gps_update', currentCoords);

    const newIncident = {
      _id: `incident_${Date.now()}`,
      vehicle_id: payload.vehicle_id || 'veh_01',
      timestamp: timestamp,
      confidence: payload.confidence || '0.95',
      duration_seconds: payload.duration_seconds || '3.0',
      image_id: imageId,
      video_id: videoId,
      gps: currentCoords,
      acknowledged: false,
    };

    incidents.unshift(newIncident);
    securityState = 'ALARM';
    alarmActive = true;

    // Immediately notify all mobile apps via WebSocket
    io.emit('alarm_triggered', newIncident);
    io.to('vehicle:veh_01').emit('alarm_triggered', newIncident);
    io.to('owner:owner_01').emit('alarm_triggered', newIncident);

    console.log(`\n🚨 [Backend Gateway] ALARM TRIGGERED! Dispatched to Mobile Phone:`, newIncident._id);
    res.status(201).json({ success: true, incident: newIncident });
  } catch (err) {
    console.error('[Backend Gateway] Incident error:', err);
    res.status(500).json({ error: err.message });
  }
});

// 3b. Receive 5-Second Video Clip from AI Engine
app.post('/api/incidents/video', upload.any(), (req, res) => {
  try {
    let videoFile = req.files?.find(f => f.fieldname === 'video') || req.files?.[0];
    let videoId = videoFile?.filename || req.body.video_id;

    if (videoId && incidents.length > 0) {
      incidents[0].video_id = videoId;
      console.log(`[Backend Gateway] Video evidence linked: ${videoId}`);
      io.emit('incident_updated', incidents[0]);
    }
    res.json({ success: true, video_id: videoId });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// 4. Fetch list of incidents for mobile history screen
app.get('/api/incidents', (req, res) => {
  res.json(incidents);
});

app.get('/api/incidents/:id', (req, res) => {
  const inc = incidents.find(i => i._id === req.params.id);
  if (inc) res.json(inc);
  else res.status(404).json({ error: 'Incident not found' });
});

app.patch('/api/incidents/:id/acknowledge', (req, res) => {
  const inc = incidents.find(i => i._id === req.params.id);
  if (inc) {
    inc.acknowledged = true;
    res.json(inc);
  } else {
    res.status(404).json({ error: 'Incident not found' });
  }
});

// 5. Static Evidence Serving (Images & Videos)
app.get('/api/evidence/snapshot/:filename', (req, res) => {
  const filePath = path.join(EVIDENCE_DIR, req.params.filename);
  if (fs.existsSync(filePath)) {
    res.sendFile(filePath);
  } else {
    res.status(404).send('Snapshot image not found');
  }
});

app.get('/api/evidence/download/:filename', (req, res) => {
  const filePath = path.join(EVIDENCE_DIR, req.params.filename);
  if (fs.existsSync(filePath)) {
    res.download(filePath, req.params.filename);
  } else {
    res.status(404).send('Evidence file not found');
  }
});

app.get('/api/evidence/video/:filename', (req, res) => {
  const filePath = path.join(EVIDENCE_DIR, req.params.filename);
  if (!fs.existsSync(filePath)) {
    return res.status(404).send('Video clip not found');
  }

  const stat = fs.statSync(filePath);
  const fileSize = stat.size;
  const range = req.headers.range;

  if (range) {
    const parts = range.replace(/bytes=/, '').split('-');
    const start = parseInt(parts[0], 10);
    const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
    const chunksize = end - start + 1;
    const file = fs.createReadStream(filePath, { start, end });
    const head = {
      'Content-Range': `bytes ${start}-${end}/${fileSize}`,
      'Accept-Ranges': 'bytes',
      'Content-Length': chunksize,
      'Content-Type': 'video/mp4',
    };
    res.writeHead(206, head);
    file.pipe(res);
  } else {
    const head = {
      'Content-Length': fileSize,
      'Content-Type': 'video/mp4',
      'Accept-Ranges': 'bytes',
    };
    res.writeHead(200, head);
    fs.createReadStream(filePath).pipe(res);
  }
});

// 6. Vehicle Profile & Photo Registration
let vehicleProfile = {
  name: 'My Vehicle',
  id: 'VEH_01',
  plate: 'KA-19-MG-2026',
  model: 'Modern Luxury SUV',
  image: null,
  lastSync: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
};

app.get('/api/vehicle/profile', (req, res) => {
  res.json(vehicleProfile);
});

app.post('/api/vehicle/profile', upload.any(), (req, res) => {
  try {
    let imgFile = req.files?.find(f => f.fieldname === 'vehicle_image') || req.files?.[0];
    if (imgFile) {
      vehicleProfile.image = imgFile.filename;
    }
    if (req.body.name) vehicleProfile.name = req.body.name;
    if (req.body.id) vehicleProfile.id = req.body.id;
    if (req.body.plate) vehicleProfile.plate = req.body.plate;
    if (req.body.model) vehicleProfile.model = req.body.model;
    vehicleProfile.lastSync = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    io.emit('vehicle_profile_updated', vehicleProfile);
    res.json({ success: true, profile: vehicleProfile });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// --- Command Handler ---
function handleCommand(command) {
  console.log(`[Command] Received owner command: ${command}`);
  if (command === 'ARM') {
    securityState = 'ARMED';
    alarmActive = false;
    io.emit('security_state_change', { state: 'ARMED', alarmActive: false });
  } else if (command === 'DISARM') {
    securityState = 'DISARMED';
    alarmActive = false;
    io.emit('security_state_change', { state: 'DISARMED', alarmActive: false });
  } else if (command === 'TRUSTED_DRIVER_ON' || command === 'TRUSTED_DRIVER' || command === 'TRUSTED') {
    securityState = 'TRUSTED_DRIVER';
    alarmActive = false;
    io.emit('security_state_change', { state: 'TRUSTED_DRIVER', alarmActive: false });
  } else if (command === 'TRIGGER_SIREN' || command === 'ACTIVATE_SIREN') {
    alarmActive = true;
    securityState = 'ALARM';
    io.emit('alarm_triggered', {
      vehicle_id: 'veh_01',
      manual: true,
      reason: 'Manual Siren Triggered by Owner',
      timestamp: new Date().toISOString(),
    });
    io.emit('security_state_change', { state: 'ALARM', alarmActive: true });
  } else if (command === 'SILENCE_ALARM' || command === 'STOP_SIREN') {
    alarmActive = false;
    if (securityState === 'ALARM') {
      securityState = 'ARMED';
    }
    io.emit('alarm_silenced', {});
    io.emit('security_state_change', { state: securityState, alarmActive: false });
  }
}

// --- Socket.io Gateway ---
io.on('connection', (socket) => {
  console.log(`[Socket.io] Client connected: ${socket.id}`);

  // Send current state on connect
  socket.emit('security_state_change', { state: securityState });
  socket.emit('gps_update', currentCoords);

  if (latestCameraFrame && latestCameraFrame.buffer) {
    socket.emit('camera_frame', {
      image_base64: latestCameraFrame.buffer.toString('base64'),
      timestamp: latestCameraFrame.timestamp,
      isInitialSnapshot: Boolean(latestCameraFrame.isInitialSnapshot),
    });
  }

  socket.on('request_camera_frame', () => {
    if (latestCameraFrame && latestCameraFrame.buffer) {
      socket.emit('camera_frame', {
        image_base64: latestCameraFrame.buffer.toString('base64'),
        timestamp: latestCameraFrame.timestamp,
        isInitialSnapshot: Boolean(latestCameraFrame.isInitialSnapshot),
      });
    }
  });

  socket.on('join_room', (room) => {
    socket.join(room);
    console.log(`[Socket.io] ${socket.id} joined room: ${room}`);
  });

  socket.on('leave_room', (room) => {
    socket.leave(room);
  });

  socket.on('owner_command', (data) => {
    const cmd = data.command;
    handleCommand(cmd);
  });

  socket.on('disconnect', () => {
    console.log(`[Socket.io] Client disconnected: ${socket.id}`);
  });
});

// Start listening on all network interfaces (0.0.0.0)
server.listen(PORT, '0.0.0.0', () => {
  console.log(`\n======================================================`);
  console.log(`  🛡️  VehicleGuard AI Gateway Server Running`);
  console.log(`  Local:   http://localhost:${PORT}`);
  console.log(`  Network: http://10.118.199.170:${PORT}`);
  console.log(`  Socket:  WebSocket & HTTP Ready (Port ${PORT})`);
  console.log(`======================================================\n`);
});
