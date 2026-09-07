'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { fetchItinerary, type Itinerary } from '@/lib/api';
import { ArrowLeft, Loader2, AlertCircle, Printer, Sunrise, Sun, Moon, Clock, MapPin, Lightbulb } from 'lucide-react';

export default function ItineraryPage() {
  const { id } = useParams<{ id: string }>();
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchItinerary(id);
        setItinerary(data);
      } catch {
        setError('Itinerary not found.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) return (
    <div className="flex h-96 items-center justify-center">
      <Loader2 className="h-10 w-10 animate-spin text-emerald-500" />
    </div>
  );

  if (error || !itinerary) return (
    <div className="flex flex-col h-96 items-center justify-center gap-4 text-center px-4">
      <AlertCircle className="h-12 w-12 text-rose-400" />
      <p className="text-slate-600">{error || 'Itinerary not found'}</p>
      <Link href="/" className="text-sm text-emerald-600 underline">← Back to explore</Link>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 print:bg-white">
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between print:hidden">
          <Link href={`/destinations/${itinerary.destination_id}`} className="flex items-center gap-1 text-sm text-slate-500 hover:text-emerald-600">
            <ArrowLeft className="h-4 w-4" /> Back to destination
          </Link>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 shadow-sm"
          >
            <Printer className="h-4 w-4" /> Print Itinerary
          </button>
        </div>

        {/* Title Card */}
        <div className="rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 p-8 text-white mb-8 shadow-lg">
          <h1 className="text-2xl font-extrabold">{itinerary.title}</h1>
          {itinerary.summary && <p className="mt-2 text-emerald-100 text-sm">{itinerary.summary}</p>}
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white/10 rounded-xl p-3 text-center">
              <div className="text-xl font-bold">{itinerary.duration_days}</div>
              <div className="text-xs text-emerald-200">Days</div>
            </div>
            <div className="bg-white/10 rounded-xl p-3 text-center">
              <div className="text-sm font-bold">{itinerary.travel_style}</div>
              <div className="text-xs text-emerald-200">Style</div>
            </div>
            <div className="bg-white/10 rounded-xl p-3 text-center">
              <div className="text-sm font-bold">{itinerary.budget_level}</div>
              <div className="text-xs text-emerald-200">Budget</div>
            </div>
            <div className="bg-white/10 rounded-xl p-3 text-center">
              <div className="text-lg font-bold">${itinerary.total_estimated_cost_usd.toFixed(0)}</div>
              <div className="text-xs text-emerald-200">Est. Total</div>
            </div>
          </div>
        </div>

        {/* Day-by-day */}
        <div className="space-y-6">
          {itinerary.day_plans.map((day) => (
            <section key={day.day} className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
              <div className="flex items-center justify-between bg-emerald-50 border-b border-emerald-100 px-6 py-4">
                <div>
                  <h2 className="font-bold text-emerald-800 text-lg">Day {day.day}</h2>
                  <p className="text-sm text-emerald-600">{day.theme}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-400">Daily estimate</p>
                  <p className="font-semibold text-slate-700">${day.total_estimated_cost_usd.toFixed(0)}</p>
                </div>
              </div>

              <div className="divide-y divide-slate-100">
                {day.activities.map((act, i) => (
                  <div key={i} className="flex gap-4 p-5">
                    {/* Timeline dot */}
                    <div className="flex flex-col items-center">
                      <div className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                        act.time_of_day === 'morning' ? 'bg-amber-100 text-amber-700' :
                        act.time_of_day === 'afternoon' ? 'bg-sky-100 text-sky-700' :
                        'bg-indigo-100 text-indigo-700'
                      }`}>
                        {act.time_of_day === 'morning' ? <Sunrise className="h-4 w-4" /> : act.time_of_day === 'afternoon' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                      </div>
                      {i < day.activities.length - 1 && (
                        <div className="flex-1 w-0.5 bg-slate-100 my-1" />
                      )}
                    </div>
                    <div className="flex-1 pb-2">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-semibold text-slate-900">{act.title}</h3>
                        <span className="flex-shrink-0 text-xs text-slate-400">${act.estimated_cost_usd.toFixed(0)}</span>
                      </div>
                      <p className="text-sm text-slate-500 mt-1">{act.description}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                        <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" /> {act.duration_hours}h</span>
                        {act.location && <span className="inline-flex items-center gap-1"><MapPin className="h-3 w-3" /> {act.location}</span>}
                        <span className="capitalize bg-slate-100 rounded px-1.5 py-0.5">{act.category}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {day.tips && (
                <div className="bg-amber-50 border-t border-amber-100 px-6 py-3 text-sm text-amber-800 flex items-start gap-2">
                  <Lightbulb className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <strong>Local Tip:</strong> {day.tips}
                  </div>
                </div>
              )}
            </section>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-slate-400 print:hidden">
          <p>Generated by Aventis Platform · <Link href="/" className="text-emerald-600 hover:underline">Explore more destinations</Link></p>
        </div>
      </div>
    </div>
  );
}
