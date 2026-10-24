// components/ControlButtons.jsx
import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';
import { colors } from '../utils/theme';

const BUTTONS = [
  { id: 'btn-arm',     label: '🔒  ARM VEHICLE',       activeLabel: '🛡️  ARMED (ACTIVE)',       command: 'ARM',               modeKey: 'ARMED',          color: colors.cyan },
  { id: 'btn-disarm',  label: '🔓  DISARM SYSTEM',     activeLabel: '🔓  DISARMED (SAFE)',       command: 'DISARM',            modeKey: 'DISARMED',       color: colors.green },
  { id: 'btn-trusted', label: '👤  TRUSTED DRIVER',    activeLabel: '👤  TRUSTED DRIVER ACTIVE', command: 'TRUSTED_DRIVER_ON', modeKey: 'TRUSTED_DRIVER', color: colors.amber },
];

export default function ControlButtons({ mode, alarm, onCommand }) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>REMOTE VEHICLE CONTROL</Text>
      {BUTTONS.map(btn => {
        const isActive = mode === btn.modeKey || (btn.modeKey === 'TRUSTED_DRIVER' && mode === 'TRUSTED');
        return (
          <TouchableOpacity
            key={btn.id}
            style={[
              styles.btn,
              { borderColor: btn.color },
              isActive && { backgroundColor: btn.color }
            ]}
            onPress={() => onCommand(btn.command)}
            activeOpacity={0.7}
          >
            <Text style={[
              styles.btnText,
              { color: isActive ? '#000' : btn.color }
            ]}>
              {isActive ? btn.activeLabel : btn.label}
            </Text>
          </TouchableOpacity>
        );
      })}

      {alarm && (
        <TouchableOpacity
          style={[styles.btn, styles.silenceBtn]}
          onPress={() => onCommand('SILENCE_ALARM')}
          activeOpacity={0.8}
        >
          <Text style={[styles.btnText, { color: 'white' }]}>🔕  SILENCE CAR SIREN</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 10 },
  label:     { fontSize: 10, fontWeight: '700', color: '#8893AE', letterSpacing: 2, marginBottom: 4 },
  btn:       { borderWidth: 1.5, borderRadius: 12, padding: 15, alignItems: 'center', backgroundColor: colors.bgCard },
  btnText:   { fontSize: 15, fontWeight: '800', letterSpacing: 0.5 },
  silenceBtn: { borderColor: colors.crimson, backgroundColor: colors.crimson },
});
