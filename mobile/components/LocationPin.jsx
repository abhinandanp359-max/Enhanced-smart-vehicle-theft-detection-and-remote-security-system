// components/LocationPin.jsx
import React from 'react';
import { View, StyleSheet } from 'react-native';
import { colors } from '../utils/theme';

export default function LocationPin({
  size = 'md',
  color = '#0F5132',
  withAura = false,
  alarm = false,
}) {
  const pinColor = alarm ? colors.crimson : color;

  const sizeMap = {
    xs: { pin: 14, dot: 4, auraOuter: 36, auraInner: 24, shift: -1 },
    sm: { pin: 18, dot: 5, auraOuter: 46, auraInner: 30, shift: -2 },
    md: { pin: 24, dot: 7, auraOuter: 60, auraInner: 40, shift: -3 },
    lg: { pin: 32, dot: 9, auraOuter: 80, auraInner: 54, shift: -4 },
  };

  const dim = sizeMap[size] || sizeMap.md;

  const pinElement = (
    <View
      style={[
        styles.pin,
        {
          width: dim.pin,
          height: dim.pin,
          backgroundColor: pinColor,
          borderTopLeftRadius: dim.pin / 2,
          borderTopRightRadius: dim.pin / 2,
          borderBottomLeftRadius: dim.pin / 2,
          borderBottomRightRadius: 0,
          transform: [{ rotate: '-45deg' }, { translateY: dim.shift }],
        },
      ]}
    >
      <View
        style={[
          styles.dot,
          {
            width: dim.dot,
            height: dim.dot,
            borderRadius: dim.dot / 2,
          },
        ]}
      />
    </View>
  );

  if (!withAura) {
    return (
      <View style={{ width: dim.pin + 4, height: dim.pin + 4, alignItems: 'center', justifyContent: 'center' }}>
        {pinElement}
      </View>
    );
  }

  const auraOuterColor = alarm ? 'rgba(239, 68, 68, 0.18)' : 'rgba(16, 185, 129, 0.16)';
  const auraInnerColor = alarm ? 'rgba(239, 68, 68, 0.35)' : 'rgba(16, 185, 129, 0.32)';

  return (
    <View
      style={[
        styles.auraOuter,
        {
          width: dim.auraOuter,
          height: dim.auraOuter,
          borderRadius: dim.auraOuter / 2,
          backgroundColor: auraOuterColor,
        },
      ]}
    >
      <View
        style={[
          styles.auraInner,
          {
            width: dim.auraInner,
            height: dim.auraInner,
            borderRadius: dim.auraInner / 2,
            backgroundColor: auraInnerColor,
          },
        ]}
      >
        {pinElement}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  pin: {
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3,
    elevation: 3,
  },
  dot: {
    backgroundColor: '#FFFFFF',
  },
  auraOuter: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  auraInner: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
