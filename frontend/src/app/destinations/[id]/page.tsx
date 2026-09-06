'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchDestination, generateItinerary, type Destination, type Itinerary } from '@/lib/api';
import { MapPin, ArrowLeft, Loader2, Calendar, Wallet, Sparkles, AlertCircle } from 'lucide-react';

const TRAVEL_STYLES = ['Relaxed', 'Cultural', 'Adventure', 'Luxury'];
const BUDGET_LEVELS = ['Budget', 'Mid-range', 'Luxury'];

function ItineraryView({ itinerary }: { itinerary: Itinerary }) {
  return (
    <div className="mt-8 space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 p-6 text-white">
        <h2 className="text-xl font-bold">{itinerary.title}</h2>
        {itinerary.summary && <p className="mt-1 text-emerald-100 text-sm">{itinerary.summary}</p>}
        <div className="mt-3 flex flex-wrap gap-4 text-sm text-emerald-100">
          <span>📅 {itinerary.duration_days} days</span>
          <span>🎯 {itinerary.travel_style}</span>
          <span>💰 {itinerary.budget_level}</span>
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
                  <div className="flex gap-4 mt-1 text-xs text-slate-400">
                    <span>⏱ {act.duration_hours}h</span>
                    <span>💵 ${act.estimated_cost_usd.toFixed(0)}</span>
                    {act.category && <span className="capitalize">#{act.category}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
          {day.tips && (
            <div className="bg-amber-50 border-t border-amber-100 px-5 py-3 text-xs text-amber-800">
              💡 <strong>Tip:</strong> {day.tips}
            </div>
          )}
        </div>
      ))}

      <div className="text-center pt-4">
        <Link
          href={`/itineraries/${itinerary.id}`}
          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800 transition-colors"
        >
          View Full Itinerary Page →
        </Link>
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
    load();
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

  if (loading) return (
    <div className="flex h-96 items-center justify-center">
      <Loader2 className="h-10 w-10 animate-spin text-emerald-500" />
    </div>
  );

  if (error || !destination) return (
    <div className="flex flex-col h-96 items-center justify-center gap-4 text-center px-4">
      <AlertCircle className="h-12 w-12 text-rose-400" />
      <p className="text-slate-600">{error || 'Destination not found'}</p>
      <Link href="/" className="text-sm text-emerald-600 underline">← Back to explore</Link>
    </div>
  );

  const heroImg = destination.image_urls?.[0] || `https://picsum.photos/seed/${destination.id}/1200/600`;

  return (
    <div className="min-h-screen bg-white">
      {/* Hero */}
      <div className="relative h-72 sm:h-96 overflow-hidden bg-slate-900">
        <img src={heroImg} alt={destination.name} className="h-full w-full object-cover opacity-70" />
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
      </div>
    </div>
  );
}
