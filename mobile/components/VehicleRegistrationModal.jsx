// components/VehicleRegistrationModal.jsx
import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Image,
  ScrollView,
  Platform,
} from 'react-native';
import { colors } from '../utils/theme';
import { saveVehicleProfile } from '../utils/api';

const PRESETS = [
  { id: 'suv', name: 'Luxury SUV', image: require('../assets/car_suv.jpg') },
  { id: 'sedan', name: 'Executive Sedan', uri: 'https://images.unsplash.com/photo-1555215695-3004980ad54e?w=500&auto=format&fit=crop&q=60' },
  { id: 'ev', name: 'Cyber EV', uri: 'https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=500&auto=format&fit=crop&q=60' },
  { id: 'sports', name: 'Sports Coupe', uri: 'https://images.unsplash.com/photo-1617788138017-80ad40651399?w=500&auto=format&fit=crop&q=60' },
];

export default function VehicleRegistrationModal({ visible, profile, onClose, onSaved }) {
  const [name, setName] = useState(profile?.name || 'My Vehicle');
  const [vehId, setVehId] = useState(profile?.id || 'VEH_01');
  const [plate, setPlate] = useState(profile?.plate || 'KA-19-MG-2026');
  const [selectedPresetUri, setSelectedPresetUri] = useState(profile?.customImageUri || null);
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    setLoading(true);
    const updated = {
      name,
      id: vehId,
      plate,
      customImageUri: selectedPresetUri,
      lastSync: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    await saveVehicleProfile(updated);
    setLoading(false);
    if (onSaved) onSaved(updated);
    onClose();
  };

  const handleFileUpload = (event) => {
    if (Platform.OS === 'web' && event?.target?.files?.[0]) {
      const file = event.target.files[0];
      const reader = new FileReader();
      reader.onload = () => {
        setSelectedPresetUri(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <Modal visible={visible} animationType="fade" transparent={true}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <View style={styles.headerRow}>
            <Text style={styles.modalTitle}>Vehicle Profile & Registration</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <Text style={styles.closeBtnText}>✕</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.subTitle}>Upload vehicle photo and customize vehicle details</Text>

          <ScrollView style={styles.body} showsVerticalScrollIndicator={false}>
            {/* Current Image Preview */}
            <View style={styles.previewContainer}>
              <Image
                source={
                  selectedPresetUri
                    ? { uri: selectedPresetUri }
                    : require('../assets/car_suv.jpg')
                }
                style={styles.carPreview}
                resizeMode="contain"
              />
            </View>

            {/* Choose or Upload Vehicle Photo */}
            <Text style={styles.sectionTitle}>SELECT OR UPLOAD VEHICLE PHOTO</Text>
            
            {/* File Upload Input for Web */}
            {Platform.OS === 'web' && (
              <TouchableOpacity
                style={styles.uploadBtn}
                onPress={() => {
                  const input = document.createElement('input');
                  input.type = 'file';
                  input.accept = 'image/*';
                  input.onchange = (e) => handleFileUpload(e);
                  input.click();
                }}
                activeOpacity={0.8}
              >
                <Text style={styles.uploadBtnText}>📁  Upload Vehicle Photo from Device</Text>
              </TouchableOpacity>
            )}

            {/* Presets Row */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.presetsRow}>
              {PRESETS.map((p) => {
                const isSelected = selectedPresetUri === (p.uri || null);
                return (
                  <TouchableOpacity
                    key={p.id}
                    style={[styles.presetItem, isSelected && styles.presetSelected]}
                    onPress={() => setSelectedPresetUri(p.uri || null)}
                  >
                    <Image source={p.image || { uri: p.uri }} style={styles.presetThumb} resizeMode="contain" />
                    <Text style={[styles.presetName, isSelected && { color: colors.primaryGreen, fontWeight: '700' }]}>
                      {p.name}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>

            {/* Form Inputs */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>VEHICLE NAME / NICKNAME</Text>
              <TextInput
                style={styles.input}
                value={name}
                onChangeText={setName}
                placeholder="e.g. My Vehicle, Range Rover"
                placeholderTextColor={colors.textMuted}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>VEHICLE ID (CAN BUS)</Text>
              <TextInput
                style={styles.input}
                value={vehId}
                onChangeText={setVehId}
                placeholder="e.g. VEH_01"
                placeholderTextColor={colors.textMuted}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>LICENSE NUMBER PLATE</Text>
              <TextInput
                style={styles.input}
                value={plate}
                onChangeText={setPlate}
                placeholder="e.g. KA-19-MG-2026"
                placeholderTextColor={colors.textMuted}
              />
            </View>

            {/* Save Button */}
            <TouchableOpacity style={styles.saveBtn} onPress={handleSave} disabled={loading}>
              <Text style={styles.saveBtnText}>{loading ? 'Saving Profile...' : 'Save Vehicle Profile'}</Text>
            </TouchableOpacity>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.45)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 20,
    width: '100%',
    maxWidth: 440,
    maxHeight: '90%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.15,
    shadowRadius: 24,
    elevation: 8,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.textPrimary,
  },
  closeBtn: {
    padding: 6,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
  },
  closeBtnText: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '700',
  },
  subTitle: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 4,
    marginBottom: 12,
  },
  body: {
    flexGrow: 0,
  },
  previewContainer: {
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    height: 120,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  carPreview: {
    width: '90%',
    height: '90%',
  },
  sectionTitle: {
    fontSize: 10,
    fontWeight: '800',
    color: colors.textMuted,
    letterSpacing: 1.5,
    marginBottom: 8,
  },
  uploadBtn: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F3F4F6',
    borderWidth: 1.5,
    borderColor: colors.primaryGreen,
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  uploadBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.primaryGreen,
  },
  presetsRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  presetItem: {
    width: 86,
    height: 72,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 6,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  presetSelected: {
    borderColor: colors.primaryGreen,
    backgroundColor: colors.primaryGreenLight,
  },
  presetThumb: {
    width: 60,
    height: 38,
  },
  presetName: {
    fontSize: 9,
    color: colors.textSecondary,
    marginTop: 2,
    fontWeight: '600',
  },
  inputGroup: {
    marginBottom: 12,
  },
  label: {
    fontSize: 10,
    fontWeight: '800',
    color: colors.textSecondary,
    letterSpacing: 1,
    marginBottom: 4,
  },
  input: {
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  saveBtn: {
    backgroundColor: colors.primaryGreen,
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 6,
    marginBottom: 8,
  },
  saveBtnText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '800',
  },
});
