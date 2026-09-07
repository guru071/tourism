'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import {
  fetchDestination,
  generateItinerary,
  fetchListings,
  createBooking,
  createCheckoutSession,
  type Destination,
  type Itinerary,
  type Listing,
} from '@/lib/api';
import {
  MapPin,
  ArrowLeft,
  Loader2,
  Calendar,
  Wallet,
  Sparkles,
  AlertCircle,
  Compass,
  Clock,
  Banknote,
  Lightbulb,
  Building2,
  Users,
  Star,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Tag,
} from 'lucide-react';

const TRAVEL_STYLES = ['Relaxed', 'Cultural', 'Adventure', 'Luxury'];
const BUDGET_LEVELS = ['Budget', 'Mid-range', 'Luxury'];

function ItineraryView({ itinerary }: { itinerary: Itinerary }) {
  return (
    <div className="mt-8 space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 p-6 text-white">
        <h2 className="text-xl font-bold">{itinerary.title}</h2>
        {itinerary.summary && <p className="mt-1 text-emerald-100 text-sm">{itinerary.summary}</p>}
        <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-emerald-100">
          <span className="flex items-center gap-1"><Calendar className="h-4 w-4" /> {itinerary.duration_days} days</span>
          <span className="flex items-center gap-1"><Compass className="h-4 w-4" /> {itinerary.travel_style}</span>
          <span className="flex items-center gap-1"><Wallet className="h-4 w-4" /> {itinerary.budget_level}</span>
          <span className="font-semibold text-white">Est. Total: ${itinerary.total_estimated_cost_usd.toFixed(0)}</span>
        </div>
      </div>

      {itinerary.day_plans.map((day) => (
        <div key={day.day} className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-5 py-3 flex items-center justify-between">
            <div>
              <span className="font-bold text-emerald-700">Day {day.day}</span>
              <span className="text-slate-500 text-sm ml-2">— {day.theme}</span>
            </div>
            <span className="text-xs text-slate-500">${day.total_estimated_cost_usd.toFixed(0)} est.</span>
          </div>
          <div className="divide-y divide-slate-100">
            {day.activities.map((act, i) => (
              <div key={i} className="px-5 py-4 flex gap-4">
                <div className="flex-shrink-0 w-20">
                  <span className={`text-xs font-semibold uppercase px-2 py-0.5 rounded-full ${
                    act.time_of_day === 'morning' ? 'bg-amber-50 text-amber-700' :
                    act.time_of_day === 'afternoon' ? 'bg-blue-50 text-blue-700' :
                    'bg-indigo-50 text-indigo-700'
                  }`}>
                    {act.time_of_day}
                  </span>
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-slate-900 text-sm">{act.title}</h4>
                  <p className="text-xs text-slate-500 mt-0.5">{act.description}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                    <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5 text-slate-400" /> {act.duration_hours}h</span>
                    <span className="flex items-center gap-1"><Banknote className="h-3.5 w-3.5 text-slate-400" /> ${act.estimated_cost_usd.toFixed(0)}</span>
                    {act.category && <span className="capitalize px-2 py-0.5 bg-slate-100 rounded-md text-slate-600">{act.category}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
          {day.tips && (
            <div className="bg-slate-50 border-t border-slate-100 px-5 py-3 text-xs text-slate-600 flex gap-2">
              <Lightbulb className="h-4 w-4 text-amber-500 flex-shrink-0" />
              <div><strong className="text-slate-900 font-medium">Tip:</strong> {day.tips}</div>
            </div>
          )}
        </div>
      ))}

      <div className="text-center pt-4">
        <Link
          href={`/itineraries/${itinerary.id}`}
          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800 transition-colors"
        >
          View Full Itinerary Page
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}

function ListingCard({
  listing,
  onBook,
  isBooking,
  disabled,
}: {
  listing: Listing;
  onBook: (listing: Listing) => void;
  isBooking: boolean;
  disabled: boolean;
}) {
  const imageUrl = listing.images?.[0] || `https://picsum.photos/seed/${listing.id}/800/500`;

  return (
    <div className="group rounded-2xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden flex flex-col">
      {/* Visual Header */}
      <div className="relative h-48 w-full bg-slate-100 overflow-hidden">
        <Image
          src={imageUrl}
          alt={listing.title}
          fill
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          className="object-cover group-hover:scale-105 transition-transform duration-300"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-transparent to-transparent" />

        {/* Category Pill */}
        <div className="absolute top-3 left-3">
          <span className="inline-flex items-center gap-1 rounded-lg bg-white/95 backdrop-blur-sm px-2.5 py-1 text-xs font-semibold text-slate-800 shadow-sm capitalize">
            <Tag className="h-3 w-3 text-emerald-600" />
            {listing.category}
          </span>
        </div>

        {/* Verification Pill */}
        <div className="absolute top-3 right-3">
          <span className="inline-flex items-center gap-1 rounded-lg bg-emerald-600/90 backdrop-blur-sm px-2.5 py-1 text-xs font-medium text-white shadow-sm">
            <ShieldCheck className="h-3.5 w-3.5" />
            Partner Verified
          </span>
        </div>

        {/* Rating preview */}
        <div className="absolute bottom-3 left-3 flex items-center gap-1 text-white text-xs font-medium drop-shadow">
          <Star className="h-3.5 w-3.5 text-amber-400 fill-amber-400" />
          <span>{(listing.rating_average || 5.0).toFixed(1)}</span>
          <span className="text-white/80">({listing.review_count || 0} reviews)</span>
        </div>
      </div>

      {/* Content */}
      <div className="p-5 flex-1 flex flex-col justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-900 group-hover:text-emerald-700 transition-colors line-clamp-1">
            {listing.title}
          </h3>

          <p className="mt-1.5 text-xs text-slate-500 line-clamp-2 leading-relaxed">
            {listing.description || 'Curated experience managed by verified local operators.'}
          </p>

          {/* Quick Specifications */}
          <div className="mt-3.5 flex flex-wrap items-center gap-3 text-xs text-slate-500">
            {listing.duration_hours && (
              <span className="inline-flex items-center gap-1">
                <Clock className="h-3.5 w-3.5 text-slate-400" />
                {listing.duration_hours}h duration
              </span>
            )}
            {listing.capacity && (
              <span className="inline-flex items-center gap-1">
                <Users className="h-3.5 w-3.5 text-slate-400" />
                Up to {listing.capacity} guests
              </span>
            )}
            <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
              Instant Booking
            </span>
          </div>

          {/* Amenities Tags */}
          {listing.amenities && listing.amenities.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {listing.amenities.slice(0, 3).map((amenity, idx) => (
                <span
                  key={idx}
                  className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600"
                >
                  {amenity}
                </span>
              ))}
              {listing.amenities.length > 3 && (
                <span className="text-[11px] text-slate-400 self-center">
                  +{listing.amenities.length - 3} more
                </span>
              )}
            </div>
          )}
        </div>

        {/* Action Row */}
        <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Base Price
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                ${listing.base_price.toFixed(0)}
              </span>
              <span className="text-xs text-slate-500 font-medium">
                {listing.currency || 'USD'}
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onBook(listing)}
            disabled={disabled || isBooking}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isBooking ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Booking...
              </>
            ) : (
              <>
                Book Experience
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DestinationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [destination, setDestination] = useState<Destination | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Generator form state
  const [durationDays, setDurationDays] = useState(3);
  const [travelStyle, setTravelStyle] = useState('Cultural');
  const [budgetLevel, setBudgetLevel] = useState('Mid-range');
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);

  // Listings state
  const [listings, setListings] = useState<Listing[]>([]);
  const [listingsLoading, setListingsLoading] = useState(true);
  const [bookingListingId, setBookingListingId] = useState<string | null>(null);
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [bookingSuccess, setBookingSuccess] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const dest = await fetchDestination(id);
        setDestination(dest);
      } catch {
        setError('Destination not found.');
      } finally {
        setLoading(false);
      }
    }

    async function loadListings() {
      try {
        setListingsLoading(true);
        const data = await fetchListings(id);
        setListings(data);
      } catch (err) {
        console.error('Failed to load listings:', err);
      } finally {
        setListingsLoading(false);
      }
    }

    if (id) {
      load();
      loadListings();
    }
  }, [id]);

  async function handleGenerate() {
    if (!destination) return;
    setGenerating(true);
    setGenError(null);
    setItinerary(null);
    try {
      const result = await generateItinerary({
        destination_id: destination.id,
        duration_days: durationDays,
        travel_style: travelStyle,
        budget_level: budgetLevel,
      });
      setItinerary(result);
    } catch (e: unknown) {
      setGenError(e instanceof Error ? e.message : 'Failed to generate itinerary.');
    } finally {
      setGenerating(false);
    }
  }

  async function handleBookExperience(listing: Listing) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (!token) {
      setBookingError('Authentication required. Please sign in to book this partner experience.');
      return;
    }

    setBookingListingId(listing.id);
    setBookingError(null);
    setBookingSuccess(null);

    try {
      // Calculate sensible booking dates based on itinerary duration or standard 3-day window
      const checkInDate = new Date();
      checkInDate.setDate(checkInDate.getDate() + 1);
      const checkOutDate = new Date(checkInDate);
      const stayDays = itinerary?.duration_days || durationDays || 3;
      checkOutDate.setDate(checkInDate.getDate() + Math.max(1, stayDays));

      const booking = await createBooking(listing.id, {
        check_in_date: checkInDate.toISOString().split('T')[0],
        check_out_date: checkOutDate.toISOString().split('T')[0],
        num_guests: 1,
        special_requests: 'Booked via Aventis Platform destination portal',
      });

      const session = await createCheckoutSession(booking.id);
      if (session && session.checkout_url) {
        setBookingSuccess('Booking initiated. Redirecting to Stripe secure checkout...');
        if (session.checkout_url.startsWith('http')) {
          window.location.href = session.checkout_url;
        } else {
          router.push(session.checkout_url);
        }
      } else {
        throw new Error('Could not retrieve checkout session URL.');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'An error occurred during booking. Please try again.';
      setBookingError(msg);
      setBookingListingId(null);
    }
  }

  if (loading) return (
    <div className="flex h-96 items-center justify-center">
      <Loader2 className="h-10 w-10 animate-spin text-emerald-500" />
    </div>
  );

  if (error || !destination) return (
    <div className="flex flex-col h-96 items-center justify-center gap-4 text-center px-4">
      <AlertCircle className="h-12 w-12 text-rose-400" />
      <p className="text-slate-600">{error || 'Destination not found'}</p>
      <Link href="/" className="inline-flex items-center gap-1 text-sm text-emerald-600 underline">
        <ArrowLeft className="h-4 w-4" /> Back to explore
      </Link>
    </div>
  );

  const heroImg = destination.image_urls?.[0] || `https://picsum.photos/seed/${destination.id}/1200/600`;

  return (
    <div className="min-h-screen bg-white">
      {/* Hero */}
      <div className="relative h-72 sm:h-96 overflow-hidden bg-slate-900">
        <Image src={heroImg} alt={destination.name} fill sizes="100vw" className="object-cover opacity-70" priority />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 to-transparent" />
        <div className="absolute bottom-6 left-6 text-white">
          <Link href="/" className="inline-flex items-center gap-1 text-xs text-white/80 hover:text-white mb-2">
            <ArrowLeft className="h-3 w-3" /> Back to explore
          </Link>
          <h1 className="text-3xl font-extrabold drop-shadow-md">{destination.name}</h1>
          <div className="flex items-center gap-2 text-sm text-white/80 mt-1">
            <MapPin className="h-4 w-4" />
            <span>{[destination.city, destination.country].filter(Boolean).join(', ')}</span>
            {destination.category && (
              <span className="ml-2 rounded-full bg-white/20 px-2 py-0.5 text-xs">{destination.category}</span>
            )}
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        {/* Description */}
        {destination.description && (
          <p className="text-slate-600 leading-relaxed mb-8">{destination.description}</p>
        )}

        {/* Itinerary Generator */}
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-4">
            <Sparkles className="h-5 w-5 text-emerald-500" />
            Generate Your Itinerary
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
            {/* Duration */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                <Calendar className="inline h-3.5 w-3.5 mr-1" />Duration (days)
              </label>
              <input
                type="number"
                min={1}
                max={14}
                value={durationDays}
                onChange={(e) => setDurationDays(Math.min(14, Math.max(1, parseInt(e.target.value) || 1)))}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            {/* Travel Style */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Travel Style</label>
              <select
                value={travelStyle}
                onChange={(e) => setTravelStyle(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                {TRAVEL_STYLES.map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
            {/* Budget */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                <Wallet className="inline h-3.5 w-3.5 mr-1" />Budget Level
              </label>
              <select
                value={budgetLevel}
                onChange={(e) => setBudgetLevel(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                {BUDGET_LEVELS.map((b) => <option key={b}>{b}</option>)}
              </select>
            </div>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="w-full rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60 flex items-center justify-center gap-2 transition-colors"
          >
            {generating ? <><Loader2 className="h-4 w-4 animate-spin" /> Generating...</> : <><Sparkles className="h-4 w-4" /> Generate My Itinerary</>}
          </button>
          {genError && (
            <p className="mt-3 text-sm text-rose-600 flex items-center gap-1">
              <AlertCircle className="h-4 w-4" />{genError}
            </p>
          )}
        </div>

        {/* Generated Itinerary */}
        {itinerary && <ItineraryView itinerary={itinerary} />}

        {/* Partner Listings Section */}
        <div className="mt-14 pt-10 border-t border-slate-200">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6">
            <div>
              <div className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-800 mb-2">
                <Building2 className="h-3.5 w-3.5 text-emerald-600" />
                Partner Experiences
              </div>
              <h2 className="text-2xl font-bold text-slate-900">Available Partner Listings</h2>
              <p className="text-slate-500 text-sm mt-1">
                Book verified tours, guided activities, and accommodations for this destination.
              </p>
            </div>
            {listings.length > 0 && (
              <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-3 py-1.5 rounded-xl self-start sm:self-auto">
                {listings.length} available experience{listings.length === 1 ? '' : 's'}
              </span>
            )}
          </div>

          {/* Booking Error Notification */}
          {bookingError && (
            <div className="mb-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-800 flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5">
                <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <span className="font-semibold">Booking Notice: </span>
                  {bookingError}
                </div>
              </div>
              {(bookingError.toLowerCase().includes('sign in') || bookingError.toLowerCase().includes('auth')) && (
                <Link
                  href="/auth/login"
                  className="flex-shrink-0 inline-flex items-center gap-1 rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-500 transition-colors"
                >
                  Sign In
                  <ArrowRight className="h-3 w-3" />
                </Link>
              )}
            </div>
          )}

          {/* Booking Redirect Notification */}
          {bookingSuccess && (
            <div className="mb-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800 flex items-center gap-3">
              <Loader2 className="h-5 w-5 text-emerald-600 animate-spin flex-shrink-0" />
              <div className="text-sm font-medium">{bookingSuccess}</div>
            </div>
          )}

          {/* Listings List / Grid */}
          {listingsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2].map((n) => (
                <div key={n} className="rounded-2xl border border-slate-200 bg-white p-5 animate-pulse space-y-4">
                  <div className="h-44 bg-slate-100 rounded-xl" />
                  <div className="h-4 bg-slate-100 rounded w-3/4" />
                  <div className="h-3 bg-slate-100 rounded w-1/2" />
                  <div className="h-10 bg-slate-100 rounded-xl mt-4" />
                </div>
              ))}
            </div>
          ) : listings.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 p-10 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-400 mb-3">
                <Building2 className="h-6 w-6" />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">No Partner Listings Available Yet</h3>
              <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto">
                Verified operators have not published experiences for this destination yet. Check back soon for curated local tours and activities.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {listings.map((item) => (
                <ListingCard
                  key={item.id}
                  listing={item}
                  onBook={handleBookExperience}
                  isBooking={bookingListingId === item.id}
                  disabled={bookingListingId !== null}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
