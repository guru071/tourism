'use client';

import React, { useEffect, useState, useCallback, useRef } from 'react';
import Link from 'next/link';
import { fetchDestinations, generateItinerary, type Destination, type DestinationFilters } from '@/lib/api';
import { MapPin, Star, Search, Loader2, AlertCircle } from 'lucide-react';

const CATEGORIES = ['All', 'Beach', 'Mountain', 'Cultural', 'Adventure', 'City', 'Wildlife'];
const PLACEHOLDER_IMAGES = [
  'https://picsum.photos/seed/beach1/800/500',
  'https://picsum.photos/seed/mountain2/800/500',
  'https://picsum.photos/seed/city3/800/500',
  'https://picsum.photos/seed/forest4/800/500',
  'https://picsum.photos/seed/desert5/800/500',
  'https://picsum.photos/seed/lake6/800/500',
];

function StarRating({ rating }: { rating?: number }) {
  if (!rating) return <span className="text-xs text-slate-400">No rating yet</span>;
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((s) => (
        <Star key={s} className={`h-3.5 w-3.5 ${s <= Math.round(rating) ? 'text-amber-400 fill-amber-400' : 'text-slate-200'}`} />
      ))}
      <span className="text-xs text-slate-500 ml-1">{rating.toFixed(1)}</span>
    </div>
  );
}

function DestinationCard({ dest, index }: { dest: Destination; index: number }) {
  const img = dest.image_urls?.[0] || PLACEHOLDER_IMAGES[index % PLACEHOLDER_IMAGES.length];
  return (
    <div className="group relative flex flex-col rounded-2xl border border-slate-200 bg-white shadow-sm hover:shadow-lg transition-all overflow-hidden">
      <Link href={`/destinations/${dest.id}`} className="block">
        <div className="relative h-48 overflow-hidden bg-slate-100">
          <img
            src={img}
            alt={dest.name}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            onError={(e) => { (e.target as HTMLImageElement).src = PLACEHOLDER_IMAGES[index % PLACEHOLDER_IMAGES.length]; }}
          />
          {dest.category && (
            <span className="absolute top-3 left-3 rounded-full bg-white/90 backdrop-blur px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
              {dest.category}
            </span>
          )}
        </div>
        <div className="p-4">
          <h3 className="font-bold text-slate-900 text-base leading-tight">{dest.name}</h3>
          <div className="flex items-center gap-1 text-slate-500 text-xs mt-1">
            <MapPin className="h-3 w-3" />
            <span>{[dest.city, dest.country].filter(Boolean).join(', ')}</span>
          </div>
          <div className="mt-2">
            <StarRating rating={dest.avg_rating} />
          </div>
          {dest.description && (
            <p className="mt-2 text-xs text-slate-500 line-clamp-2">{dest.description}</p>
          )}
        </div>
      </Link>
      <div className="px-4 pb-4 mt-auto">
        <Link
          href={`/destinations/${dest.id}`}
          className="block w-full text-center rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 transition-colors"
        >
          Plan Itinerary
        </Link>
      </div>
    </div>
  );
}

export default function ExplorePage() {
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const load = useCallback(async (filters: DestinationFilters) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchDestinations({ ...filters, limit: 24 });
      setDestinations(res.items);
      setTotal(res.total);
    } catch {
      setError('Could not load destinations. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      load({
        q: search || undefined,
        category: category !== 'All' ? category : undefined,
      });
    }, 300);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [search, category, load]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 to-white">
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-emerald-700 via-teal-600 to-cyan-700 text-white py-20 px-4">
        <div className="absolute inset-0 bg-[url('https://picsum.photos/seed/hero-tourism/1920/600')] bg-cover bg-center opacity-20" />
        <div className="relative mx-auto max-w-3xl text-center space-y-6">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-6xl drop-shadow-md">
            Discover Your Perfect Journey
          </h1>
          <p className="text-lg text-emerald-100 max-w-xl mx-auto">
            AI-powered itineraries tailored to your travel style, budget, and dreams.
          </p>
          {/* Search bar */}
          <div className="relative max-w-lg mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search destinations, countries, cities..."
              className="w-full rounded-2xl border-0 bg-white pl-12 pr-4 py-4 text-slate-900 shadow-xl placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>
      </section>

      {/* Content */}
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        {/* Category Filters */}
        <div className="flex flex-wrap gap-2 mb-8">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition-all ${
                category === cat
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'bg-white border border-slate-200 text-slate-600 hover:border-emerald-400 hover:text-emerald-600'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Results count */}
        {!loading && !error && (
          <p className="text-sm text-slate-500 mb-6">
            {total} destination{total !== 1 ? 's' : ''} found
            {search && ` for "${search}"`}
            {category !== 'All' && ` in ${category}`}
          </p>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="h-10 w-10 animate-spin text-emerald-500" />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
            <AlertCircle className="h-12 w-12 text-rose-400" />
            <p className="text-slate-600 max-w-md">{error}</p>
          </div>
        )}

        {/* Empty */}
        {!loading && !error && destinations.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
            <MapPin className="h-12 w-12 text-slate-300" />
            <p className="text-slate-500">No destinations found. Try a different search.</p>
          </div>
        )}

        {/* Destination Grid */}
        {!loading && !error && destinations.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {destinations.map((dest, i) => (
              <DestinationCard key={dest.id} dest={dest} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
