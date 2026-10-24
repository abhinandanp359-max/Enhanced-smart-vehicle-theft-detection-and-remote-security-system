// app/_layout.jsx
import React, { useEffect } from 'react';
import { Tabs } from 'expo-router';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors } from '../utils/theme';
import { registerForPushNotifications } from '../utils/notifications';
import LocationPin from '../components/LocationPin';

function TabsNavigator() {
  const insets = useSafeAreaInsets();
  // Ensure Android 3-button navigation bar (or home bar) doesn't overlap the tabs
  const bottomInset = Math.max(insets.bottom, Platform.OS === 'android' ? 28 : (Platform.OS === 'ios' ? 22 : 12));
  const tabHeight = 56 + bottomInset;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarHideOnKeyboard: true,
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopColor: '#E5E7EB',
          borderTopWidth: 1,
          height: tabHeight,
          paddingBottom: bottomInset,
          paddingTop: 6,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: -3 },
          shadowOpacity: 0.06,
          shadowRadius: 10,
          elevation: 10,
        },
        tabBarItemStyle: {
          height: 48,
          justifyContent: 'center',
          alignItems: 'center',
          paddingVertical: 2,
        },
        tabBarActiveTintColor: colors.primaryGreen,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '700',
          marginTop: 2,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, focused }) => (
            <View style={styles.iconWrapper} pointerEvents="none">
              <Text style={{ fontSize: 20 }}>🏠</Text>
              {focused ? <View style={styles.activeIndicator} /> : null}
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="map"
        options={{
          title: 'Live Map',
          tabBarIcon: ({ color, focused }) => (
            <View style={styles.iconWrapper} pointerEvents="none">
              <LocationPin size="sm" color={focused ? '#0F5132' : '#9CA3AF'} />
              {focused ? <View style={styles.activeIndicator} /> : null}
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="incidents"
        options={{
          title: 'Evidence',
          tabBarIcon: ({ color, focused }) => (
            <View style={styles.iconWrapper} pointerEvents="none">
              <Text style={{ fontSize: 20 }}>📄</Text>
              {focused ? <View style={styles.activeIndicator} /> : null}
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: 'Settings',
          tabBarIcon: ({ color, focused }) => (
            <View style={styles.iconWrapper} pointerEvents="none">
              <Text style={{ fontSize: 20 }}>⚙️</Text>
              {focused ? <View style={styles.activeIndicator} /> : null}
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="camera"
        options={{
          tabBarButton: () => null,
          title: 'Live Camera',
        }}
      />
    </Tabs>
  );
}

export default function Layout() {
  useEffect(() => {
    registerForPushNotifications();
  }, []);

  return (
    <SafeAreaProvider>
      <TabsNavigator />
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  iconWrapper: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  activeIndicator: {
    width: 18,
    height: 3,
    backgroundColor: colors.primaryGreen,
    borderRadius: 2,
    marginTop: 2,
  },
});
