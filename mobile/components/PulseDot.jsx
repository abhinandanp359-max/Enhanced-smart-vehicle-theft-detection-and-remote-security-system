// components/PulseDot.jsx
import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { colors } from '../utils/theme';

export default function PulseDot({ active = true, label = 'LIVE' }) {
  const anim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (!active) return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1.4, duration: 750, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 1.0, duration: 750, useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [active]);

  const dotColor = active ? colors.green : colors.crimson;

  return (
    <View style={styles.container}>
      <View style={styles.dotWrapper}>
        {active && (
          <Animated.View
            style={[
              styles.pulseRing,
              { backgroundColor: dotColor, transform: [{ scale: anim }] }
            ]}
          />
        )}
        <View style={[styles.dot, { backgroundColor: dotColor }]} />
      </View>
      <Text style={[styles.label, { color: active ? colors.green : colors.textSecondary }]}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  dotWrapper: { width: 14, height: 14, alignItems: 'center', justifyContent: 'center' },
  dot: { width: 8, height: 8, borderRadius: 4 },
  pulseRing: {
    position: 'absolute',
    width: 14,
    height: 14,
    borderRadius: 7,
    opacity: 0.35,
  },
  label: { fontSize: 11, fontWeight: '700', letterSpacing: 1 },
});
