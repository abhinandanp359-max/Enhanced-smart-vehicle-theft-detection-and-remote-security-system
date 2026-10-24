// utils/notifications.js
import { Platform } from 'react-native';

let Notifications = null;

try {
  // Safely import so Expo Go SDK 53+ does not crash on missing ExpoTopicSubscriptionModule
  Notifications = require('expo-notifications');
} catch (e) {
  console.log('[Notifications] Expo Go fallback active (remote push native module omitted in Expo Go)');
}

// Call this once when app starts
export async function registerForPushNotifications() {
  if (!Notifications || typeof Notifications.requestPermissionsAsync !== 'function') {
    return;
  }
  try {
    const { status } = await Notifications.requestPermissionsAsync();
    if (status !== 'granted') return;

    if (typeof Notifications.setNotificationHandler === 'function') {
      Notifications.setNotificationHandler({
        handleNotification: async () => ({
          shouldShowAlert: true,
          shouldPlaySound: true,
          shouldSetBadge: true,
        }),
      });
    }
  } catch (e) {
    console.log('[Notifications] Permission setup notice:', e.message);
  }
}

// Call this when alarm fires
export async function sendLocalNotification(title, body) {
  if (!Notifications || typeof Notifications.scheduleNotificationAsync !== 'function') {
    console.log(`[Notification Alert]: ${title} - ${body}`);
    return;
  }
  try {
    await Notifications.scheduleNotificationAsync({
      content: { title, body, sound: 'default', color: '#EF4444' },
      trigger: null, // show immediately
    });
  } catch (e) {
    console.log('[Notifications] Local schedule notice:', e.message);
  }
}
