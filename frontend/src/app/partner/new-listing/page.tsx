'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  API_BASE,
  fetchDestinations,
  createDestination,
  createListing,
  type Destination,
} from '@/lib/api';
import {
  ArrowLeft,
  Building2,
  CalendarCheck,
  Camera,
  Car,
  Check,
  CheckCircle2,
  ChevronDown,
  Clock,
  Compass,
  DollarSign,
  Eye,
  Globe,
  Headphones,
  HeartHandshake,
  HelpCircle,
  Info,
  Layers,
  Loader2,
  Lock,
  MapPin,
  Mountain,
  Package,
  Plus,
  RefreshCw,
  Shield,
  ShieldCheck,
  Smartphone,
  Sparkles,
  Star,
  Ticket,
  Trash2,
  UserCheck,
  Users,
  Utensils,
  Wifi,
  X,
  AlertCircle,
} from 'lucide-react';

// ─── Constants & Reference Data ──────────────────────────────────────────────

interface CategoryOption {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const CATEGORIES: CategoryOption[] = [
  { id: 'tour', name: 'Tour', icon: Compass, description: 'Guided excursions, walks, and city tours' },
  { id: 'activity', name: 'Activity', icon: Mountain, description: 'Adventure sports, hikes, and outdoor thrill' },
  { id: 'accommodation', name: 'Stay', icon: Building2, description: 'Boutique hotels, villas, and stays' },
  { id: 'dining', name: 'Gastronomy', icon: Utensils, description: 'Culinary tours, tastings, and dining' },
  { id: 'transport', name: 'Transit', icon: Car, description: 'Private transfers, charters, and chauffeurs' },
  { id: 'guide', name: 'Guide', icon: UserCheck, description: 'Private personal certified guides' },
  { id: 'experience', name: 'Experience', icon: Sparkles, description: 'Masterclasses, workshops, and crafts' },
  { id: 'wellness', name: 'Wellness', icon: HeartHandshake, description: 'Spa rituals, yoga retreats, and hot springs' },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen' },
  { code: 'CAD', symbol: 'CA$', name: 'Canadian Dollar' },
  { code: 'AUD', symbol: 'AU$', name: 'Australian Dollar' },
  { code: 'CHF', symbol: 'CHF', name: 'Swiss Franc' },
  { code: 'SGD', symbol: 'SG$', name: 'Singapore Dollar' },
  { code: 'AED', symbol: 'AED', name: 'UAE Dirham' },
  { code: 'INR', symbol: '₹', name: 'Indian Rupee' },
];

const PRICING_UNITS = [
  { id: 'person', label: 'Per Person' },
  { id: 'group', label: 'Per Group (Private)' },
  { id: 'night', label: 'Per Night' },
  { id: 'day', label: 'Per Day' },
  { id: 'vehicle', label: 'Per Vehicle' },
];

const STANDARD_AMENITIES = [
  { id: 'pro_guide', label: 'Certified Professional Guide', icon: UserCheck },
  { id: 'hotel_pickup', label: 'Hotel Pickup & Drop-off', icon: Car },
  { id: 'equipment', label: 'All Equipment & Gear Provided', icon: ShieldCheck },
  { id: 'refreshments', label: 'Refreshments & Beverages Included', icon: Utensils },
  { id: 'wifi', label: 'High-Speed Mobile WiFi', icon: Wifi },
  { id: 'audio_headsets', label: 'Audio Headsets for Commentary', icon: Headphones },
  { id: 'free_cancellation', label: 'Free Cancellation (24 Hours Prior)', icon: CalendarCheck },
  { id: 'small_group', label: 'Small Group Guarantee (Max 12)', icon: Users },
  { id: 'mobile_voucher', label: 'Mobile & Digital Tickets Accepted', icon: Smartphone },
  { id: 'wheelchair', label: 'Wheelchair & Accessibility Friendly', icon: CheckCircle2 },
  { id: 'safety_certified', label: 'Safety Certified & Insured', icon: Shield },
  { id: 'photo_package', label: 'Complimentary Photo Package', icon: Camera },
  { id: 'admission', label: 'All Admission & Park Fees Paid', icon: Ticket },
];

const SAMPLE_PRESETS = [
  {
    name: 'Coastal Cruise',
    url: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80',
  },
  {
    name: 'Alpine Trek',
    url: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80',
  },
  {
    name: 'Historic Heritage',
    url: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1200&q=80',
  },
  {
    name: 'Gastronomy Tasting',
    url: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80',
  },
];

// ─── Types ───────────────────────────────────────────────────────────────────

interface OperatorProfile {
  id: string;
  business_name: string;
  business_type: string;
  verified: boolean;
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function CreateListingPage() {
  const router = useRouter();

  // Auth & operator state
  const [loadingAuth, setLoadingAuth] = useState(true);
  const [operator, setOperator] = useState<OperatorProfile | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  // Available destinations from API
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [loadingDestinations, setLoadingDestinations] = useState(true);

  // Form core fields
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('tour');
  const [description, setDescription] = useState('');
  const [basePrice, setBasePrice] = useState<string>('');
  const [currency, setCurrency] = useState('USD');
  const [pricingUnit, setPricingUnit] = useState('person');

  // Location fields
  const [selectedDestinationId, setSelectedDestinationId] = useState<string>('');
  const [isCustomDestination, setIsCustomDestination] = useState(false);
  const [customDestName, setCustomDestName] = useState('');
  const [customDestCountry, setCustomDestCountry] = useState('');
  const [customDestCity, setCustomDestCity] = useState('');
  const [locationAddress, setLocationAddress] = useState('');
  const [latitude, setLatitude] = useState<string>('');
  const [longitude, setLongitude] = useState<string>('');

  // Operational logistics
  const [capacity, setCapacity] = useState<string>('8');
  const [durationHours, setDurationHours] = useState<string>('3.5');
  const [availability, setAvailability] = useState(true);
  const [instantBooking, setInstantBooking] = useState(true);
  const [cancellationPolicy, setCancellationPolicy] = useState('flexible');

  // Imagery
  const [primaryImage, setPrimaryImage] = useState(SAMPLE_PRESETS[0].url);
  const [galleryImages, setGalleryImages] = useState<string[]>([]);
  const [newGalleryInput, setNewGalleryInput] = useState('');

  // Amenities
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([
    'Certified Professional Guide',
    'Free Cancellation (24 Hours Prior)',
    'Mobile & Digital Tickets Accepted',
  ]);
  const [customAmenityInput, setCustomAmenityInput] = useState('');

  // Form submission state
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [createdListing, setCreatedListing] = useState<{ id: string; title: string; slug: string } | null>(null);

  // Active section tracking for UI navigation
  const [activeTab, setActiveTab] = useState<'details' | 'location' | 'pricing' | 'logistics' | 'media' | 'amenities'>('details');

  // ─── Initial Load & Verification ──────────────────────────────────────────

  useEffect(() => {
    async function init() {
      const storedUser = localStorage.getItem('auth_user');
      const storedToken = localStorage.getItem('auth_token');

      if (!storedUser || !storedToken) {
        setAuthError('Authentication required. Please sign in to your Aventis Partner account.');
        setLoadingAuth(false);
        return;
      }

      try {
        const parsed = JSON.parse(storedUser);
        if (parsed.role !== 'partner' && parsed.role !== 'admin') {
          setAuthError('Access restricted. Only verified Partners and Platform Admins can publish listings.');
          setLoadingAuth(false);
          return;
        }

        // Fetch operator profile
        const opRes = await fetch(`${API_BASE}/operators/my`, {
          headers: {
            Authorization: `Bearer ${storedToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!opRes.ok) {
          setAuthError('Operator profile not found. Please establish your operator profile first.');
          setLoadingAuth(false);
          return;
        }

        const opData = await opRes.json();
        setOperator(opData);
      } catch {
        setAuthError('Failed to verify Partner session. Please log in again.');
      } finally {
        setLoadingAuth(false);
      }

      // Fetch destinations
      try {
        setLoadingDestinations(true);
        const destRes = await fetchDestinations({ limit: 50 });
        setDestinations(destRes.items || []);
        if (destRes.items && destRes.items.length > 0) {
          setSelectedDestinationId(destRes.items[0].id);
          if (destRes.items[0].latitude) setLatitude(String(destRes.items[0].latitude));
          if (destRes.items[0].longitude) setLongitude(String(destRes.items[0].longitude));
          if (destRes.items[0].city) setLocationAddress(destRes.items[0].city);
        }
      } catch (err) {
        console.error('Failed to load destinations:', err);
      } finally {
        setLoadingDestinations(false);
      }
    }

    init();
  }, []);

  // When selected destination changes, auto-fill coordinates & location hints if empty
  function handleDestinationSelect(destId: string) {
    if (destId === 'custom') {
      setIsCustomDestination(true);
      setSelectedDestinationId('');
      return;
    }

    setIsCustomDestination(false);
    setSelectedDestinationId(destId);
    const match = destinations.find((d) => d.id === destId);
    if (match) {
      if (match.latitude) setLatitude(String(match.latitude));
      if (match.longitude) setLongitude(String(match.longitude));
      if (match.city && !locationAddress) {
        setLocationAddress(`${match.city}, ${match.country}`);
      }
    }
  }

  // Amenities toggle
  function toggleAmenity(label: string) {
    setSelectedAmenities((prev) =>
      prev.includes(label) ? prev.filter((a) => a !== label) : [...prev, label]
    );
  }

  function addCustomAmenity(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = customAmenityInput.trim();
    if (!trimmed) return;
    if (!selectedAmenities.includes(trimmed)) {
      setSelectedAmenities((prev) => [...prev, trimmed]);
    }
    setCustomAmenityInput('');
  }

  function removeAmenity(label: string) {
    setSelectedAmenities((prev) => prev.filter((a) => a !== label));
  }

  // Gallery image helpers
  function addGalleryImage(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = newGalleryInput.trim();
    if (!trimmed) return;
    if (!galleryImages.includes(trimmed)) {
      setGalleryImages((prev) => [...prev, trimmed]);
    }
    setNewGalleryInput('');
  }

  function removeGalleryImage(idx: number) {
    setGalleryImages((prev) => prev.filter((_, i) => i !== idx));
  }

  // ─── Form Submission ──────────────────────────────────────────────────────

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);

    // Validation
    if (!title.trim()) {
      setFormError('Please provide a listing title.');
      setActiveTab('details');
      return;
    }
    if (!description.trim()) {
      setFormError('Please provide a comprehensive listing description.');
      setActiveTab('details');
      return;
    }
    if (!basePrice || isNaN(Number(basePrice)) || Number(basePrice) < 0) {
      setFormError('Please enter a valid base price greater than or equal to 0.');
      setActiveTab('pricing');
      return;
    }

    setSubmitting(true);

    try {
      let destIdToUse = selectedDestinationId;

      // Handle custom destination creation if user specified one
      if (isCustomDestination) {
        if (!customDestName.trim() || !customDestCountry.trim()) {
          setFormError('Please provide both a destination name and country for the new location.');
          setSubmitting(false);
          setActiveTab('location');
          return;
        }

        const newDest = await createDestination({
          name: customDestName.trim(),
          country: customDestCountry.trim(),
          city: customDestCity.trim() || undefined,
          category: category,
          description: `Partner-listed destination for ${customDestName}`,
          latitude: latitude ? parseFloat(latitude) : undefined,
          longitude: longitude ? parseFloat(longitude) : undefined,
          image_urls: primaryImage ? [primaryImage] : [],
          tags: [category, 'partner-created'],
        });

        destIdToUse = newDest.id;
      }

      if (!destIdToUse) {
        setFormError('Please select or specify a destination location.');
        setSubmitting(false);
        setActiveTab('location');
        return;
      }

      // Compile images
      const allImages = [primaryImage, ...galleryImages].filter(Boolean);

      // Build payload for POST /api/v1/listings
      const payload = {
        destination_id: destIdToUse,
        title: title.trim(),
        category,
        description: description.trim(),
        base_price: parseFloat(basePrice),
        currency,
        capacity: capacity ? parseInt(capacity, 10) : undefined,
        duration_hours: durationHours ? parseFloat(durationHours) : undefined,
        latitude: latitude ? parseFloat(latitude) : undefined,
        longitude: longitude ? parseFloat(longitude) : undefined,
        location: locationAddress.trim() || undefined,
        images: allImages,
        amenities: selectedAmenities,
      };

      const result = await createListing(payload);
      setCreatedListing(result);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'An error occurred while creating the listing.');
    } finally {
      setSubmitting(false);
    }
  }

  // ─── Authentication Guard Screens ──────────────────────────────────────────

  if (loadingAuth) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3 text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
          <span className="text-sm font-medium">Verifying Aventis Partner authorization...</span>
        </div>
      </div>
    );
  }

  if (authError || !operator) {
    return (
      <div className="min-h-screen bg-slate-50 px-4 py-16">
        <div className="mx-auto max-w-lg rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-50 text-rose-600">
            <Lock className="h-7 w-7" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Partner Verification Required</h2>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            {authError || 'An active operator profile is required to list offerings on the Aventis Platform.'}
          </p>
          <div className="mt-6 flex flex-col gap-2">
            <Link
              href="/partner"
              className="w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-emerald-500 transition-colors inline-flex items-center justify-center gap-2"
            >
              <Building2 className="h-4 w-4" /> Go to Partner Dashboard
            </Link>
            <Link
              href="/auth/login"
              className="w-full rounded-xl border border-slate-200 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Switch Account / Sign In
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // ─── Success Screen ───────────────────────────────────────────────────────

  if (createdListing) {
    return (
      <div className="min-h-screen bg-slate-50 px-4 py-16">
        <div className="mx-auto max-w-2xl rounded-3xl border border-emerald-100 bg-white p-8 sm:p-12 text-center shadow-xl">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-emerald-50 text-emerald-600">
            <CheckCircle2 className="h-10 w-10" />
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 border border-emerald-200">
            Aventis Listing Published
          </span>
          <h1 className="mt-4 text-3xl font-bold text-slate-900">{createdListing.title}</h1>
          <p className="mt-3 text-slate-600 text-sm leading-relaxed max-w-md mx-auto">
            Your listing has been successfully compiled, validated, and registered in the Aventis Platform global distribution system.
          </p>

          <div className="mt-6 rounded-2xl bg-slate-50 p-4 border border-slate-100 text-left space-y-2 text-xs font-mono text-slate-600">
            <div className="flex justify-between">
              <span className="text-slate-400">Listing Identifier:</span>
              <span className="font-semibold text-slate-800">{createdListing.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Public Slug:</span>
              <span className="text-emerald-700 font-medium">{createdListing.slug}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Partner Business:</span>
              <span className="text-slate-800">{operator.business_name}</span>
            </div>
          </div>

          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/partner"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-md hover:bg-emerald-500 transition-colors"
            >
              <Package className="h-4 w-4" /> Return to Partner Dashboard
            </Link>
            <button
              type="button"
              onClick={() => {
                setCreatedListing(null);
                setTitle('');
                setDescription('');
                setBasePrice('');
                setGalleryImages([]);
              }}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Plus className="h-4 w-4" /> Create Another Listing
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ─── Main Form UI ──────────────────────────────────────────────────────────

  const activeCurrencySymbol = CURRENCIES.find((c) => c.code === currency)?.symbol || '$';
  const selectedDestObj = destinations.find((d) => d.id === selectedDestinationId);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top Header Bar */}
      <header className="sticky top-16 z-30 border-b border-slate-200 bg-white/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4">
            <Link
              href="/partner"
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Back
            </Link>
            <div className="hidden sm:block h-5 w-px bg-slate-200" />
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-slate-900">Create New Listing</h1>
                <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
                  {operator.business_name}
                </span>
              </div>
              <p className="text-xs text-slate-500">Aventis Platform · Global Partner Inventory</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/partner"
              className="hidden sm:inline-block text-xs font-medium text-slate-500 hover:text-slate-800"
            >
              Cancel
            </Link>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={submitting}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-500 transition-all disabled:opacity-60"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Publishing...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4" />
                  Publish Listing
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Navigation Pills */}
        <div className="mb-8 flex overflow-x-auto gap-2 border-b border-slate-200 pb-3 text-sm font-medium">
          {[
            { id: 'details', label: '1. Overview & Category', icon: Layers },
            { id: 'location', label: '2. Destination & Location', icon: MapPin },
            { id: 'pricing', label: '3. Pricing & Currency', icon: DollarSign },
            { id: 'logistics', label: '4. Capacity & Schedule', icon: Clock },
            { id: 'media', label: '5. Visual Imagery', icon: Camera },
            { id: 'amenities', label: '6. Features & Inclusions', icon: ShieldCheck },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`inline-flex items-center gap-2 whitespace-nowrap rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Global Error Banner */}
        {formError && (
          <div className="mb-6 flex items-center justify-between rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 shadow-sm">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0" />
              <span>{formError}</span>
            </div>
            <button
              type="button"
              onClick={() => setFormError(null)}
              className="text-rose-600 hover:text-rose-800"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Two-Column Grid: Form Left, Sticky Live Preview Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Massive Form (7 cols) */}
          <form onSubmit={handleSubmit} className="lg:col-span-7 space-y-8">
            {/* ─── SECTION 1: OVERVIEW & CATEGORY ─── */}
            <section
              id="details"
              className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <Layers className="h-5 w-5 text-emerald-600" />
                    Listing Overview & Category
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Define the core identity, title, and service classification for the Aventis catalog.
                  </p>
                </div>
                <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">
                  Step 1 of 6
                </span>
              </div>

              <div className="space-y-6">
                {/* Title */}
                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="block text-sm font-semibold text-slate-800">
                      Listing Title <span className="text-rose-500">*</span>
                    </label>
                    <span className="text-xs text-slate-400">{title.length}/100 characters</span>
                  </div>
                  <input
                    type="text"
                    required
                    maxLength={100}
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Exclusive Alpine Helicopter Flight & Glacier Landing"
                    className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all"
                  />
                  <p className="mt-1.5 text-xs text-slate-400">
                    A clear, engaging title drives higher engagement on Aventis discovery.
                  </p>
                </div>

                {/* Category Selection Grid */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 mb-2">
                    Service Category <span className="text-rose-500">*</span>
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {CATEGORIES.map((cat) => {
                      const Icon = cat.icon;
                      const isSelected = category === cat.id;
                      return (
                        <button
                          key={cat.id}
                          type="button"
                          onClick={() => setCategory(cat.id)}
                          className={`flex flex-col items-start p-3 rounded-2xl border text-left transition-all ${
                            isSelected
                              ? 'border-emerald-500 bg-emerald-50/70 text-emerald-900 shadow-sm ring-1 ring-emerald-500'
                              : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                          }`}
                        >
                          <div
                            className={`mb-2 rounded-xl p-2 ${
                              isSelected ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            <Icon className="h-4 w-4" />
                          </div>
                          <span className="text-xs font-bold leading-tight">{cat.name}</span>
                          <span className="text-[10px] text-slate-500 mt-1 line-clamp-2 leading-tight">
                            {cat.description}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Comprehensive Description */}
                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="block text-sm font-semibold text-slate-800">
                      Comprehensive Description <span className="text-rose-500">*</span>
                    </label>
                    <span className="text-xs text-slate-400">{description.length} chars</span>
                  </div>
                  <textarea
                    required
                    rows={6}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Provide a vivid description of what travelers will experience, highlights, unique vantage points, and itinerary flow..."
                    className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all leading-relaxed"
                  />
                  <p className="mt-1.5 text-xs text-slate-400">
                    Include meeting instructions, highlights, inclusions, and physical preparation tips.
                  </p>
                </div>
              </div>
            </section>

            {/* ─── SECTION 2: DESTINATION & LOCATION ─── */}
            <section
              id="location"
              className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <MapPin className="h-5 w-5 text-emerald-600" />
                    Destination & Geographic Location
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Connect this listing to a regional hub or specify exact coordinates for mapping.
                  </p>
                </div>
                <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">
                  Step 2 of 6
                </span>
              </div>

              <div className="space-y-6">
                {/* Destination Selector */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 mb-1.5">
                    Platform Destination Hub <span className="text-rose-500">*</span>
                  </label>
                  {loadingDestinations ? (
                    <div className="flex items-center gap-2 py-3 text-sm text-slate-400">
                      <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />
                      Loading global destination hubs...
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <select
                        value={isCustomDestination ? 'custom' : selectedDestinationId}
                        onChange={(e) => handleDestinationSelect(e.target.value)}
                        className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all bg-white"
                      >
                        <optgroup label="Aventis Catalog Hubs">
                          {destinations.map((d) => (
                            <option key={d.id} value={d.id}>
                              {d.name} ({[d.city, d.country].filter(Boolean).join(', ')})
                            </option>
                          ))}
                        </optgroup>
                        <optgroup label="Other Locations">
                          <option value="custom">+ Register New Destination Hub...</option>
                        </optgroup>
                      </select>

                      {/* Custom Destination Drawer if selected */}
                      {isCustomDestination && (
                        <div className="rounded-2xl bg-emerald-50/50 border border-emerald-200 p-4 space-y-3">
                          <div className="flex items-center gap-2 text-xs font-bold text-emerald-800 uppercase tracking-wider">
                            <Plus className="h-3.5 w-3.5" /> Register New Destination Hub
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <div>
                              <label className="block text-xs font-medium text-slate-700 mb-1">
                                Hub Name *
                              </label>
                              <input
                                type="text"
                                value={customDestName}
                                onChange={(e) => setCustomDestName(e.target.value)}
                                placeholder="e.g. Amalfi Coast"
                                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-medium text-slate-700 mb-1">
                                Country *
                              </label>
                              <input
                                type="text"
                                value={customDestCountry}
                                onChange={(e) => setCustomDestCountry(e.target.value)}
                                placeholder="e.g. Italy"
                                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-medium text-slate-700 mb-1">
                                City
                              </label>
                              <input
                                type="text"
                                value={customDestCity}
                                onChange={(e) => setCustomDestCity(e.target.value)}
                                placeholder="e.g. Positano"
                                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                              />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Specific Location / Address */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 mb-1.5">
                    Meeting Point / Operating Address
                  </label>
                  <input
                    type="text"
                    value={locationAddress}
                    onChange={(e) => setLocationAddress(e.target.value)}
                    placeholder="e.g. Marina Grande Pier 3, 80073 Capri NA, Italy"
                    className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all"
                  />
                  <p className="mt-1.5 text-xs text-slate-400">
                    Exact location travelers will navigate to upon itinerary booking.
                  </p>
                </div>

                {/* Coordinates */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-sm font-semibold text-slate-800">
                      Geographic GPS Coordinates (Optional)
                    </label>
                    {selectedDestObj && (
                      <button
                        type="button"
                        onClick={() => {
                          if (selectedDestObj.latitude) setLatitude(String(selectedDestObj.latitude));
                          if (selectedDestObj.longitude) setLongitude(String(selectedDestObj.longitude));
                        }}
                        className="text-xs font-medium text-emerald-600 hover:text-emerald-700 inline-flex items-center gap-1"
                      >
                        <RefreshCw className="h-3 w-3" /> Sync Hub Coordinates
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <input
                        type="number"
                        step="0.0000001"
                        value={latitude}
                        onChange={(e) => setLatitude(e.target.value)}
                        placeholder="Latitude (e.g. 40.5507)"
                        className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>
                    <div>
                      <input
                        type="number"
                        step="0.0000001"
                        value={longitude}
                        onChange={(e) => setLongitude(e.target.value)}
                        placeholder="Longitude (e.g. 14.2426)"
                        className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* ─── SECTION 3: PRICING & CURRENCY ─── */}
            <section
              id="pricing"
              className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <DollarSign className="h-5 w-5 text-emerald-600" />
                    Pricing Structure & Currency
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Set competitive rates and multi-currency billing parameters for Aventis travelers.
                  </p>
                </div>
                <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">
                  Step 3 of 6
                </span>
              </div>

              <div className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Base Price */}
                  <div>
                    <label className="block text-sm font-semibold text-slate-800 mb-1.5">
                      Base Price <span className="text-rose-500">*</span>
                    </label>
                    <div className="relative">
                      <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4 text-slate-400 font-semibold text-sm">
                        {activeCurrencySymbol}
                      </div>
                      <input
                        type="number"
                        required
                        min="0"
                        step="0.01"
                        value={basePrice}
                        onChange={(e) => setBasePrice(e.target.value)}
                        placeholder="149.00"
                        className="w-full rounded-xl border border-slate-200 pl-9 pr-4 py-3 text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>
                  </div>

                  {/* Currency Selector */}
                  <div>
                    <label className="block text-sm font-semibold text-slate-800 mb-1.5">
                      Billing Currency <span className="text-rose-500">*</span>
                    </label>
                    <select
                      value={currency}
                      onChange={(e) => setCurrency(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
                    >
                      {CURRENCIES.map((c) => (
                        <option key={c.code} value={c.code}>
                          {c.code} ({c.symbol}) — {c.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Pricing Unit */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 mb-2">
                    Rate Basis
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {PRICING_UNITS.map((unit) => (
                      <button
                        key={unit.id}
                        type="button"
                        onClick={() => setPricingUnit(unit.id)}
                        className={`rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                          pricingUnit === unit.id
                            ? 'bg-slate-900 text-white shadow-sm'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {unit.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Instant Booking & Confirmation */}
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">Instant Booking Confirmation</p>
                      <p className="text-xs text-slate-500">
                        Automatically accept reservations without manual Partner approval delays.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setInstantBooking(!instantBooking)}
                      className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        instantBooking ? 'bg-emerald-600' : 'bg-slate-300'
                      }`}
                    >
                      <span
                        className={`inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                          instantBooking ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </div>
            </section>

            {/* ─── SECTION 4: CAPACITY, DURATION & SCHEDULE ─── */}
            <section
              id="logistics"
              className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <Clock className="h-5 w-5 text-emerald-600" />
                    Capacity, Duration & Logistics
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Control guest quotas, experience time commitments, and inventory availability.
                  </p>
                </div>
                <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">
                  Step 4 of 6
                </span>
              </div>

              <div className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Capacity */}
                  <div>
                    <label className="block text-sm font-semibold text-slate-800 mb-1.5">
                      Maximum Capacity (Guests)
                    </label>
                    <div className="relative">
                      <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4 text-slate-400">
                        <Users className="h-4 w-4" />
                      </div>
                      <input
                        type="number"
                        min="1"
                        max="500"
                        value={capacity}
                        onChange={(e) => setCapacity(e.target.value)}
                        placeholder="8"
                        className="w-full rounded-xl border border-slate-200 pl-10 pr-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>
                  </div>

                  {/* Duration */}
                  <div>
                    <label className="block text-sm font-semibold text-slate-800 mb-1.5">
                      Duration (Hours)
                    </label>
                    <div className="relative">
                      <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4 text-slate-400">
                        <Clock className="h-4 w-4" />
                      </div>
                      <input
                        type="number"
                        min="0.5"
                        step="0.5"
                        max="168"
                        value={durationHours}
                        onChange={(e) => setDurationHours(e.target.value)}
                        placeholder="3.5"
                        className="w-full rounded-xl border border-slate-200 pl-10 pr-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Cancellation Policy */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 mb-2">
                    Cancellation & Refund Standard
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {[
                      { id: 'flexible', name: 'Flexible', note: 'Full refund up to 24 hours prior' },
                      { id: 'moderate', name: 'Moderate', note: 'Full refund up to 5 days prior' },
                      { id: 'strict', name: 'Strict', note: '50% refund up to 7 days prior' },
                    ].map((pol) => (
                      <button
                        key={pol.id}
                        type="button"
                        onClick={() => setCancellationPolicy(pol.id)}
                        className={`p-3 rounded-2xl border text-left transition-all ${
                          cancellationPolicy === pol.id
                            ? 'border-emerald-500 bg-emerald-50 text-emerald-900 shadow-sm'
                            : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                        }`}
                      >
                        <p className="text-xs font-bold capitalize">{pol.name}</p>
                        <p className="text-[11px] text-slate-500 mt-1 leading-tight">{pol.note}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Inventory Availability Toggle */}
                <div className="flex items-center justify-between rounded-2xl border border-slate-200 p-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-800">Publish as Available for Immediate Booking</p>
                    <p className="text-xs text-slate-500">
                      If disabled, this listing will remain saved as unlisted draft until ready.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setAvailability(!availability)}
                    className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      availability ? 'bg-emerald-600' : 'bg-slate-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        availability ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </section>

            {/* ─── SECTION 5: VISUAL IMAGERY ─── */}
            <section
              id="media"
              className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <Camera className="h-5 w-5 text-emerald-600" />
                    Visual Imagery & Media Gallery
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    High-definition photography directly elevates traveler conversion across the platform.
                  </p>
                </div>
                <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">
                  Step 5 of 6
                </span>
              </div>

              <div className="space-y-6">
                {/* Primary Cover Image */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 mb-1.5">
                    Primary Cover Image URL <span className="text-rose-500">*</span>
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="url"
                      required
                      value={primaryImage}
                      onChange={(e) => setPrimaryImage(e.target.value)}
                      placeholder="https://images.unsplash.com/..."
                      className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                    />
                  </div>
                </div>

                {/* Preset Quick Fill Samples */}
                <div>
                  <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">
                    Quick Sample Photography Presets:
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {SAMPLE_PRESETS.map((preset) => (
                      <button
                        key={preset.name}
                        type="button"
                        onClick={() => setPrimaryImage(preset.url)}
                        className={`px-3 py-2 rounded-xl text-xs font-medium border text-left truncate transition-all ${
                          primaryImage === preset.url
                            ? 'border-emerald-500 bg-emerald-50 text-emerald-800'
                            : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-white'
                        }`}
                      >
                        {preset.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Gallery Additional URLs */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 mb-1.5">
                    Additional Gallery Images ({galleryImages.length})
                  </label>
                  <div className="flex gap-2 mb-3">
                    <input
                      type="url"
                      value={newGalleryInput}
                      onChange={(e) => setNewGalleryInput(e.target.value)}
                      placeholder="Paste additional image URL and click Add"
                      className="flex-1 rounded-xl border border-slate-200 px-4 py-2 text-xs font-mono text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                    <button
                      type="button"
                      onClick={addGalleryImage}
                      className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition-colors inline-flex items-center gap-1"
                    >
                      <Plus className="h-3.5 w-3.5" /> Add
                    </button>
                  </div>

                  {galleryImages.length > 0 && (
                    <div className="space-y-2">
                      {galleryImages.map((img, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-mono text-slate-600"
                        >
                          <span className="truncate max-w-[80%]">{img}</span>
                          <button
                            type="button"
                            onClick={() => removeGalleryImage(idx)}
                            className="text-rose-500 hover:text-rose-700 p-1"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* ─── SECTION 6: AMENITIES & FEATURES ─── */}
            <section
              id="amenities"
              className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5 text-emerald-600" />
                    Amenities & Included Features
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Select guaranteed inclusions and amenities that distinguish this offering.
                  </p>
                </div>
                <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">
                  Step 6 of 6
                </span>
              </div>

              <div className="space-y-6">
                {/* Standard Amenities Selection */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {STANDARD_AMENITIES.map((am) => {
                    const Icon = am.icon;
                    const isChecked = selectedAmenities.includes(am.label);
                    return (
                      <button
                        key={am.id}
                        type="button"
                        onClick={() => toggleAmenity(am.label)}
                        className={`flex items-center gap-3 p-3 rounded-2xl border text-left transition-all ${
                          isChecked
                            ? 'border-emerald-500 bg-emerald-50/80 text-emerald-900 shadow-sm'
                            : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        <div
                          className={`flex h-8 w-8 items-center justify-center rounded-xl ${
                            isChecked ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                        <span className="text-xs font-medium leading-tight flex-1">{am.label}</span>
                        {isChecked && <Check className="h-4 w-4 text-emerald-600" />}
                      </button>
                    );
                  })}
                </div>

                {/* Custom Amenity Adder */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                    Add Custom Amenity or Special Perk
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={customAmenityInput}
                      onChange={(e) => setCustomAmenityInput(e.target.value)}
                      placeholder="e.g. Complimentary champagne toast at sunset"
                      className="flex-1 rounded-xl border border-slate-200 px-4 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                    <button
                      type="button"
                      onClick={addCustomAmenity}
                      className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition-colors inline-flex items-center gap-1"
                    >
                      <Plus className="h-3.5 w-3.5" /> Add
                    </button>
                  </div>
                </div>

                {/* Active Amenities Chips */}
                {selectedAmenities.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-2">
                    {selectedAmenities.map((am) => (
                      <span
                        key={am}
                        className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700"
                      >
                        {am}
                        <button
                          type="button"
                          onClick={() => removeAmenity(am)}
                          className="text-slate-400 hover:text-slate-600 ml-1"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </section>

            {/* Bottom Actions Bar */}
            <div className="flex items-center justify-between rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div>
                <p className="text-xs font-bold text-slate-800">Ready to distribute on Aventis?</p>
                <p className="text-xs text-slate-500">
                  Your listing will be instantly live and discoverable worldwide.
                </p>
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-md hover:bg-emerald-500 transition-all disabled:opacity-60"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4" />
                    Publish Listing
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Right Column: Real-Time Live Preview Sticky Sidebar (5 cols) */}
          <aside className="lg:col-span-5 sticky top-36 space-y-6">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
                <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
                  <Eye className="h-4 w-4 text-emerald-600" />
                  Live Traveler Preview
                </span>
                <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                  Aventis Network
                </span>
              </div>

              {/* Mock Traveler Card */}
              <div className="group overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-md transition-all">
                {/* Image & Badges */}
                <div className="relative h-48 w-full overflow-hidden bg-slate-100">
                  {primaryImage ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={primaryImage}
                      alt={title || 'Listing Preview'}
                      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = SAMPLE_PRESETS[0].url;
                      }}
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-slate-300">
                      <Camera className="h-10 w-10" />
                    </div>
                  )}

                  {/* Category Badge */}
                  <span className="absolute top-3 left-3 rounded-full bg-white/90 backdrop-blur px-2.5 py-0.5 text-xs font-semibold text-emerald-800 capitalize shadow-sm">
                    {category}
                  </span>

                  {/* Verified Partner Badge */}
                  <span className="absolute top-3 right-3 rounded-full bg-slate-900/80 backdrop-blur px-2 py-0.5 text-[10px] font-semibold text-white inline-flex items-center gap-1 shadow-sm">
                    <ShieldCheck className="h-3 w-3 text-emerald-400" /> Verified
                  </span>
                </div>

                {/* Body Content */}
                <div className="p-5">
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1.5">
                    <MapPin className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                    <span className="truncate">
                      {isCustomDestination
                        ? [customDestCity, customDestCountry].filter(Boolean).join(', ') || 'Custom Location'
                        : selectedDestObj
                        ? `${selectedDestObj.name}, ${selectedDestObj.country}`
                        : 'Select Destination'}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 leading-snug line-clamp-2">
                    {title || 'Your Listing Title Will Appear Here'}
                  </h3>

                  <p className="mt-2 text-xs text-slate-500 line-clamp-2 leading-relaxed">
                    {description ||
                      'Detailed listing description, experience highlights, and traveler itinerary points will display here.'}
                  </p>

                  {/* Badges / Logistics */}
                  <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-slate-500 border-t border-slate-100 pt-3">
                    <span className="inline-flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5 text-slate-400" />
                      {durationHours ? `${durationHours}h` : 'Flexible'}
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Users className="h-3.5 w-3.5 text-slate-400" />
                      {capacity ? `Up to ${capacity} guests` : 'Any group size'}
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Star className="h-3.5 w-3.5 text-amber-400 fill-amber-400" />
                      New Listing
                    </span>
                  </div>

                  {/* Amenities snapshot */}
                  {selectedAmenities.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {selectedAmenities.slice(0, 3).map((a) => (
                        <span
                          key={a}
                          className="rounded-md bg-slate-50 border border-slate-100 px-2 py-0.5 text-[10px] text-slate-600 truncate max-w-[150px]"
                        >
                          {a}
                        </span>
                      ))}
                      {selectedAmenities.length > 3 && (
                        <span className="rounded-md bg-slate-50 border border-slate-100 px-2 py-0.5 text-[10px] text-slate-400">
                          +{selectedAmenities.length - 3} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Price & Mock CTA */}
                  <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">Starting from</span>
                      <div className="flex items-baseline gap-1">
                        <span className="text-xl font-extrabold text-slate-900">
                          {activeCurrencySymbol}
                          {basePrice ? parseFloat(basePrice).toFixed(0) : '0'}
                        </span>
                        <span className="text-xs text-slate-500 font-medium">
                          {currency} / {pricingUnit}
                        </span>
                      </div>
                    </div>
                    <button
                      type="button"
                      disabled
                      className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white opacity-90 cursor-default"
                    >
                      Book Experience
                    </button>
                  </div>
                </div>
              </div>

              {/* Status Note */}
              <div className="mt-4 rounded-xl bg-slate-50 p-3 text-xs text-slate-500 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-slate-700">
                  <Info className="h-3.5 w-3.5 text-emerald-600" />
                  Aventis Quality Guarantee
                </div>
                <p className="text-[11px] leading-relaxed">
                  Listings published through verified Partner portals are immediately indexed for AI itinerary generation and traveler search.
                </p>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
