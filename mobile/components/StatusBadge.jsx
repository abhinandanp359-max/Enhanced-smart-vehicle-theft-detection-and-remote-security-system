// components/StatusBadge.jsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../utils/theme';

export default function StatusBadge({ mode }) {
  let badgeColor = colors.textSecondary;
  let bgBadge = 'rgba(136, 147, 174, 0.1)';
  let label = mode || 'UNKNOWN';

  const normalized = (mode || '').toUpperCase();

  if (normalized === 'ARMED') {
    badgeColor = colors.cyan;
    bgBadge = 'rgba(0, 242, 254, 0.16)';
    label = '🛡️ ARMED & ACTIVE';
  } else if (normalized === 'DISARMED') {
    badgeColor = colors.green;
    bgBadge = 'rgba(34, 197, 94, 0.16)';
    label = '🔓 DISARMED (SAFE)';
  } else if (normalized === 'ALARM' || normalized === 'ALERT') {
    badgeColor = colors.crimson;
    bgBadge = 'rgba(239, 68, 68, 0.25)';
    label = '🚨 INTRUDER ALARM!';
  } else if (normalized === 'TRUSTED_DRIVER' || normalized === 'TRUSTED') {
    badgeColor = colors.amber;
    bgBadge = 'rgba(245, 158, 11, 0.2)';
    label = '👤 TRUSTED DRIVER ACTIVE';
  }

  return (
    <View style={[styles.badge, { borderColor: badgeColor, backgroundColor: bgBadge }]}>
      <Text style={[styles.badgeText, { color: badgeColor }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderWidth: 1.5,
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    alignSelf: 'flex-start',
  },
  badgeText: {
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 1,
  },
});

