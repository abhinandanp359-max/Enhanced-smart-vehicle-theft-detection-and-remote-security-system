// app/incidents.jsx
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { getIncidents } from '../utils/api';
import IncidentCard from '../components/IncidentCard';
import { colors } from '../utils/theme';

export default function IncidentsScreen() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchIncidents = async () => {
    const data = await getIncidents();
    setIncidents(data);
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchIncidents();
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primaryGreen} />
        <Text style={styles.loadingText}>Fetching Security Evidence...</Text>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      {/* Header Banner */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Evidence & Video Vault</Text>
          <Text style={styles.subTitle}>
            {incidents.length} intrusion incidents logged with photo & video downloads
          </Text>
        </View>
        <TouchableOpacity style={styles.refreshBtn} onPress={onRefresh}>
          <Text style={styles.refreshBtnText}>🔄 Refresh</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        style={styles.list}
        contentContainerStyle={styles.container}
        data={incidents}
        keyExtractor={(item, index) => item._id || item.timestamp || String(index)}
        renderItem={({ item }) => <IncidentCard incident={item} />}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.primaryGreen}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <View style={styles.shieldBig}>
              <Text style={{ fontSize: 36 }}>🛡️</Text>
            </View>
            <Text style={styles.emptyTitle}>No Security Breaches</Text>
            <Text style={styles.emptySubtitle}>
              All clear. No unauthorized intrusions have been recorded.
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#F4F6F8',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 14,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: '#111827',
  },
  subTitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  refreshBtn: {
    backgroundColor: colors.primaryGreenLight,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 10,
  },
  refreshBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.primaryGreen,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F4F6F8',
    gap: 12,
  },
  loadingText: {
    color: colors.textSecondary,
    fontSize: 13,
    fontWeight: '600',
  },
  list: {
    flex: 1,
  },
  container: {
    padding: 16,
    gap: 14,
    paddingBottom: 120,
    maxWidth: 640,
    width: '100%',
    alignSelf: 'center',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 90,
    gap: 10,
  },
  shieldBig: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.primaryGreenLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 6,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  emptySubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: 'center',
    maxWidth: 280,
    lineHeight: 18,
  },
});
