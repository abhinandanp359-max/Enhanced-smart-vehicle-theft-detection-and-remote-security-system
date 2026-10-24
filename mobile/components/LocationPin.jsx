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

  // Symmetrical geometry for consistent map-pin with circular center
  const sizeMap = {
    xs: { head: 14, dot: 4.5, tipWidth: 8, tipHeight: 6, tipOverlap: 3.5, auraOuter: 32, auraInner: 22 },
    sm: { head: 18, dot: 6, tipWidth: 10, tipHeight: 8, tipOverlap: 4.5, auraOuter: 42, auraInner: 28 },
    md: { head: 24, dot: 8, tipWidth: 13, tipHeight: 10, tipOverlap: 6, auraOuter: 56, auraInner: 38 },
    lg: { head: 32, dot: 10.5, tipWidth: 17, tipHeight: 14, tipOverlap: 8, auraOuter: 76, auraInner: 50 },
  };

  const dim = sizeMap[size] || sizeMap.md;

  const pinElement = (
    <View style={[styles.pinWrapper, { width: dim.head, height: dim.head + dim.tipHeight - dim.tipOverlap }]}>
      {/* Circular Pin Head with Circular Center */}
      <View
        style={[
          styles.head,
          {
            width: dim.head,
            height: dim.head,
            borderRadius: dim.head / 2,
            backgroundColor: pinColor,
          },
        ]}
      >
        {/* Circular Center Hole */}
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

      {/* Downward Pointed Tip */}
      <View
        style={[
          styles.tip,
          {
            marginTop: -dim.tipOverlap,
            borderLeftWidth: dim.tipWidth / 2,
            borderRightWidth: dim.tipWidth / 2,
            borderTopWidth: dim.tipHeight,
            borderTopColor: pinColor,
          },
        ]}
      />
    </View>
  );

  if (!withAura) {
    return (
      <View style={[styles.centerContainer, { width: dim.head, height: dim.head + 4 }]}>
        {pinElement}
      </View>
    );
  }

  // Subtle translucent green circular highlight around the pin
  const auraOuterColor = alarm ? 'rgba(220, 38, 38, 0.14)' : 'rgba(15, 81, 50, 0.12)';
  const auraInnerColor = alarm ? 'rgba(220, 38, 38, 0.28)' : 'rgba(15, 81, 50, 0.22)';

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
  centerContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  pinWrapper: {
    alignItems: 'center',
    justifyContent: 'flex-start',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.22,
    shadowRadius: 3,
    elevation: 3,
  },
  head: {
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2,
  },
  dot: {
    backgroundColor: '#FFFFFF',
  },
  tip: {
    width: 0,
    height: 0,
    backgroundColor: 'transparent',
    borderStyle: 'solid',
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    zIndex: 1,
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
