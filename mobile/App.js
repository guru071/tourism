import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  StyleSheet,
  Text,
  View,
  FlatList,
  ActivityIndicator,
  RefreshControl,
  TouchableOpacity,
  TextInput,
  Image,
  SafeAreaView,
  Platform,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';

const API_ENDPOINT = 'http://localhost:8000/api/v1/destinations';

const REFERENCE_DATA = [
  {
    id: 'dest-001',
    name: 'Kyoto Cultural Heritage District',
    country: 'Japan',
    city: 'Kyoto',
    region: 'Kansai',
    category: 'Cultural',
    description:
      'Historic district featuring preserved temples, traditional wooden architecture, and curated botanical gardens.',
    latitude: 35.0116,
    longitude: 135.7681,
    timezone: 'Asia/Tokyo',
    avg_rating: 4.9,
    review_count: 320,
    tags: ['Historic', 'Architecture', 'Gardens', 'UNESCO'],
    image_urls: [
      'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=800&q=80',
    ],
  },
  {
    id: 'dest-002',
    name: 'Reykjavik Geothermal Gateway',
    country: 'Iceland',
    city: 'Reykjavik',
    region: 'Capital Region',
    category: 'Adventure',
    description:
      'Hub for Nordic geological expeditions, volcanic geothermal springs, and coastal wilderness excursions.',
    latitude: 64.1466,
    longitude: -21.9426,
    timezone: 'Atlantic/Reykjavik',
    avg_rating: 4.8,
    review_count: 245,
    tags: ['Geothermal', 'Northern Lights', 'Coastal', 'Eco-Tourism'],
    image_urls: [
      'https://images.unsplash.com/photo-1504893524553-b855bce32c67?auto=format&fit=crop&w=800&q=80',
    ],
  },
  {
    id: 'dest-003',
    name: 'Zermatt Alpine Sanctuary',
    country: 'Switzerland',
    city: 'Zermatt',
    region: 'Valais',
    category: 'Nature',
    description:
      'High-altitude alpine sanctuary situated below the Matterhorn peak with year-round outdoor trails and rail transit.',
    latitude: 45.9765,
    longitude: 7.7491,
    timezone: 'Europe/Zurich',
    avg_rating: 4.9,
    review_count: 410,
    tags: ['Alpine', 'Skiing', 'Hiking', 'High Altitude'],
    image_urls: [
      'https://images.unsplash.com/photo-1530122037265-a5f1f91d3b99?auto=format&fit=crop&w=800&q=80',
    ],
  },
  {
    id: 'dest-004',
    name: 'Singapore Urban Botanical Center',
    country: 'Singapore',
    city: 'Singapore',
    region: 'Central',
    category: 'Urban',
    description:
      'Modern metropolis showcase highlighting high-density sustainable architectural structures and floral conservatories.',
    latitude: 1.2816,
    longitude: 103.8636,
    timezone: 'Asia/Singapore',
    avg_rating: 4.7,
    review_count: 580,
    tags: ['Futuristic', 'Conservatory', 'Sustainability', 'Metropolitan'],
    image_urls: [
      'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?auto=format&fit=crop&w=800&q=80',
    ],
  },
];

const CATEGORY_FILTERS = ['All', 'Cultural', 'Adventure', 'Nature', 'Urban'];

export default function App() {
  const [destinations, setDestinations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isUsingReferenceData, setIsUsingReferenceData] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  const fetchDestinations = useCallback(async () => {
    try {
      setErrorMessage(null);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);

      const response = await fetch(API_ENDPOINT, {
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Server returned HTTP status ${response.status}`);
      }

      const payload = await response.json();
      let records = [];

      if (Array.isArray(payload)) {
        records = payload;
      } else if (payload && Array.isArray(payload.items)) {
        records = payload.items;
      } else if (payload && Array.isArray(payload.data)) {
        records = payload.data;
      }

      if (records.length > 0) {
        setDestinations(records);
        setIsUsingReferenceData(false);
      } else {
        setDestinations(REFERENCE_DATA);
        setIsUsingReferenceData(true);
      }
    } catch (err) {
      setErrorMessage(
        'Unable to connect to ' + API_ENDPOINT + '. Displaying local reference catalog.'
      );
      setDestinations(REFERENCE_DATA);
      setIsUsingReferenceData(true);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchDestinations();
  }, [fetchDestinations]);

  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    fetchDestinations();
  }, [fetchDestinations]);

  const filteredDestinations = useMemo(() => {
    return destinations.filter((dest) => {
      const matchesCategory =
        selectedCategory === 'All' ||
        (dest.category && dest.category.toLowerCase() === selectedCategory.toLowerCase());

      const query = searchQuery.trim().toLowerCase();
      if (!query) {
        return matchesCategory;
      }

      const matchesSearch =
        (dest.name && dest.name.toLowerCase().includes(query)) ||
        (dest.country && dest.country.toLowerCase().includes(query)) ||
        (dest.city && dest.city.toLowerCase().includes(query)) ||
        (dest.description && dest.description.toLowerCase().includes(query));

      return matchesCategory && matchesSearch;
    });
  }, [destinations, selectedCategory, searchQuery]);

  const renderHeader = () => (
    <View style={styles.headerContainer}>
      <View style={styles.appBar}>
        <View>
          <Text style={styles.appTitle}>Tourism Operating System</Text>
          <Text style={styles.appSubtitle}>Destination Directory</Text>
        </View>
        <View style={styles.statusBadge}>
          <View
            style={[
              styles.statusIndicator,
              isUsingReferenceData ? styles.statusOffline : styles.statusOnline,
            ]}
          />
          <Text style={styles.statusBadgeText}>
            {isUsingReferenceData ? 'Offline Mode' : 'Connected'}
          </Text>
        </View>
      </View>

      {errorMessage ? (
        <View style={styles.alertBanner}>
          <Text style={styles.alertTitle}>Notice</Text>
          <Text style={styles.alertDescription}>{errorMessage}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={() => {
              setIsLoading(true);
              fetchDestinations();
            }}
          >
            <Text style={styles.retryButtonText}>Retry Connection</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      <View style={styles.searchSection}>
        <TextInput
          style={styles.searchInput}
          placeholder="Filter by name, country, or keyword..."
          placeholderTextColor="#94A3B8"
          value={searchQuery}
          onChangeText={setSearchQuery}
          clearButtonMode="while-editing"
        />
      </View>

      <View style={styles.filterSection}>
        {CATEGORY_FILTERS.map((cat) => {
          const isSelected = selectedCategory === cat;
          return (
            <TouchableOpacity
              key={cat}
              style={[
                styles.categoryChip,
                isSelected ? styles.categoryChipActive : styles.categoryChipInactive,
              ]}
              onPress={() => setSelectedCategory(cat)}
            >
              <Text
                style={[
                  styles.categoryChipText,
                  isSelected ? styles.categoryChipTextActive : styles.categoryChipTextInactive,
                ]}
              >
                {cat}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <View style={styles.summaryBar}>
        <Text style={styles.summaryText}>
          Total Records: {filteredDestinations.length} of {destinations.length}
        </Text>
        <Text style={styles.summarySubtext}>Protocol: HTTP REST API</Text>
      </View>
    </View>
  );

  const renderDestinationCard = ({ item }) => {
    const imageUrl =
      item.image_urls && item.image_urls.length > 0 ? item.image_urls[0] : null;

    return (
      <View style={styles.card}>
        {imageUrl ? (
          <Image
            source={{ uri: imageUrl }}
            style={styles.cardImage}
            resizeMode="cover"
          />
        ) : null}

        <View style={styles.cardContent}>
          <View style={styles.cardMetaRow}>
            <View style={styles.categoryBadge}>
              <Text style={styles.categoryBadgeText}>
                {item.category ? item.category.toUpperCase() : 'GENERAL'}
              </Text>
            </View>
            {item.avg_rating ? (
              <View style={styles.ratingBadge}>
                <Text style={styles.ratingBadgeText}>
                  Score: {Number(item.avg_rating).toFixed(1)} / 5.0
                </Text>
              </View>
            ) : null}
          </View>

          <Text style={styles.cardTitle}>{item.name}</Text>

          <Text style={styles.cardLocation}>
            {[item.city, item.region, item.country].filter(Boolean).join(', ')}
          </Text>

          {item.description ? (
            <Text style={styles.cardDescription} numberOfLines={3}>
              {item.description}
            </Text>
          ) : null}

          {item.tags && item.tags.length > 0 ? (
            <View style={styles.tagsContainer}>
              {item.tags.map((tag, idx) => (
                <View key={idx} style={styles.tagItem}>
                  <Text style={styles.tagText}>{tag}</Text>
                </View>
              ))}
            </View>
          ) : null}

          <View style={styles.cardFooter}>
            <View style={styles.metricsGroup}>
              {item.review_count ? (
                <Text style={styles.metricLabel}>
                  Reviews: {item.review_count}
                </Text>
              ) : null}
              {item.timezone ? (
                <Text style={styles.metricLabel}>Zone: {item.timezone}</Text>
              ) : null}
            </View>

            <TouchableOpacity style={styles.detailButton}>
              <Text style={styles.detailButtonText}>Inspect Specifications</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  };

  const renderEmpty = () => {
    if (isLoading) {
      return null;
    }
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyTitle}>No Destinations Found</Text>
        <Text style={styles.emptyDescription}>
          No destination records match the specified query parameters.
        </Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      {isLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#0284C7" />
          <Text style={styles.loadingText}>Retrieving Destination Records...</Text>
          <Text style={styles.loadingSubtext}>{API_ENDPOINT}</Text>
        </View>
      ) : (
        <FlatList
          data={filteredDestinations}
          keyExtractor={(item, index) => item.id || String(index)}
          renderItem={renderDestinationCard}
          ListHeaderComponent={renderHeader}
          ListEmptyComponent={renderEmpty}
          contentContainerStyle={styles.listContainer}
          refreshControl={
            <RefreshControl
              refreshing={isRefreshing}
              onRefresh={handleRefresh}
              tintColor="#0284C7"
              colors={['#0284C7']}
            />
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  listContainer: {
    backgroundColor: '#F8FAFC',
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    fontWeight: '600',
    color: '#0F172A',
  },
  loadingSubtext: {
    marginTop: 6,
    fontSize: 12,
    color: '#64748B',
  },
  headerContainer: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    paddingTop: Platform.OS === 'android' ? 36 : 16,
    paddingBottom: 16,
  },
  appBar: {
    backgroundColor: '#0F172A',
    paddingHorizontal: 20,
    paddingVertical: 18,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  appTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  appSubtitle: {
    fontSize: 12,
    fontWeight: '500',
    color: '#94A3B8',
    marginTop: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#334155',
  },
  statusIndicator: {
    width: 7,
    height: 7,
    borderRadius: 4,
    marginRight: 6,
  },
  statusOnline: {
    backgroundColor: '#10B981',
  },
  statusOffline: {
    backgroundColor: '#F59E0B',
  },
  statusBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#E2E8F0',
  },
  alertBanner: {
    backgroundColor: '#FEF3C7',
    borderLeftWidth: 4,
    borderLeftColor: '#D97706',
    marginHorizontal: 16,
    marginTop: 14,
    padding: 12,
    borderRadius: 4,
  },
  alertTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#92400E',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  alertDescription: {
    fontSize: 12,
    color: '#78350F',
    marginTop: 2,
    lineHeight: 18,
  },
  retryButton: {
    alignSelf: 'flex-start',
    backgroundColor: '#92400E',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
    marginTop: 8,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '600',
  },
  searchSection: {
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  searchInput: {
    backgroundColor: '#F1F5F9',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 14,
    color: '#0F172A',
  },
  filterSection: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingTop: 12,
    gap: 8,
  },
  categoryChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
  },
  categoryChipActive: {
    backgroundColor: '#0F172A',
    borderColor: '#0F172A',
  },
  categoryChipInactive: {
    backgroundColor: '#FFFFFF',
    borderColor: '#CBD5E1',
  },
  categoryChipText: {
    fontSize: 12,
    fontWeight: '600',
  },
  categoryChipTextActive: {
    color: '#FFFFFF',
  },
  categoryChipTextInactive: {
    color: '#475569',
  },
  summaryBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 14,
  },
  summaryText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
  },
  summarySubtext: {
    fontSize: 11,
    color: '#94A3B8',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    marginHorizontal: 16,
    marginTop: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    overflow: 'hidden',
  },
  cardImage: {
    width: '100%',
    height: 180,
    backgroundColor: '#E2E8F0',
  },
  cardContent: {
    padding: 16,
  },
  cardMetaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  categoryBadge: {
    backgroundColor: '#E0F2FE',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#BAE6FD',
  },
  categoryBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0369A1',
    letterSpacing: 0.5,
  },
  ratingBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  ratingBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#334155',
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#0F172A',
    lineHeight: 22,
  },
  cardLocation: {
    fontSize: 13,
    fontWeight: '500',
    color: '#0284C7',
    marginTop: 4,
  },
  cardDescription: {
    fontSize: 13,
    color: '#475569',
    marginTop: 8,
    lineHeight: 19,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 12,
  },
  tagItem: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 4,
  },
  tagText: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  metricsGroup: {
    flexDirection: 'row',
    gap: 12,
  },
  metricLabel: {
    fontSize: 11,
    color: '#64748B',
  },
  detailButton: {
    backgroundColor: '#0F172A',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 6,
  },
  detailButtonText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '600',
  },
  emptyContainer: {
    padding: 36,
    alignItems: 'center',
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F172A',
  },
  emptyDescription: {
    fontSize: 13,
    color: '#64748B',
    textAlign: 'center',
    marginTop: 6,
    lineHeight: 18,
  },
});
