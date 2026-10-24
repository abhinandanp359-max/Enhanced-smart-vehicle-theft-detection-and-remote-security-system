// Learn more https://docs.expo.dev/guides/customizing-metro
const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Limit workers to 2 to prevent Zone Allocation memory spikes on Windows
config.maxWorkers = 2;

module.exports = config;
