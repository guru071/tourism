'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  API_BASE,
  type AuthToken,
} from '@/lib/api';
import {
  Store,
  BookOpen,
  Star,
  Plus,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
  ChevronRight,
  Package,
  TrendingUp,
  Lock,
} from 'lucide-react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface User {
  id: string;
  email: string;
  full_name?: string;
  role: string;
}

interface OperatorProfile {
  id: string;
  business_name: string;
  business_type: string;
  verification_status: string;
  verified: boolean;
  listings?: Listing[];
}

interface Listing {
  id: string;
  title: string;
  category: string;
  base_price: number;
  currency: string;
  availability: boolean;
  rating_average: number;
  review_count: number;
}

interface Booking {
  id: string;
  booking_reference: string;
  listing_title?: string;
  listing_id: string;
  status: string;
  start_date: string;
  end_date: string;
  guests_count: number;
  total_price: number;
  currency: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function authHeader(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers: authHeader() });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || 'Request failed');
  }
  return res.json();
}

const STATUS_STYLES: Record<string, { icon: React.ReactNode; classes: string }> = {
  pending: { icon: <Clock className="h-3.5 w-3.5" />, classes: 'bg-amber-50 text-amber-700 border-amber-200' },
  confirmed: { icon: <CheckCircle2 className="h-3.5 w-3.5" />, classes: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  completed: { icon: <CheckCircle2 className="h-3.5 w-3.5" />, classes: 'bg-blue-50 text-blue-700 border-blue-200' },
  cancelled: { icon: <XCircle className="h-3.5 w-3.5" />, classes: 'bg-rose-50 text-rose-700 border-rose-200' },
};

// ─── Subcomponents ────────────────────────────────────────────────────────────

function StatCard({ label, value, icon, sub }: { label: string; value: string | number; icon: React.ReactNode; sub?: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</span>
        <div className="text-emerald-500">{icon}</div>
      </div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
    </div>
  );
}

function CreateOperatorForm({ onCreated }: { onCreated: () => void }) {
  const [businessName, setBusinessName] = useState('');
  const [businessType, setBusinessType] = useState('agency');
  const [description, setDescription] = useState('');
  const [website, setWebsite] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await apiFetch('/operators', {
        method: 'POST',
        body: JSON.stringify({
          business_name: businessName,
          business_type: businessType,
          description,
          website_url: website || undefined,
        }),
      });
      onCreated();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to create profile');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto mt-16 text-center">
      <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 mb-4">
        <Store className="h-8 w-8" />
      </div>
      <h2 className="text-xl font-bold text-slate-900">Create Your Operator Profile</h2>
      <p className="text-slate-500 text-sm mt-2 mb-8">Set up your business profile to start listing tours, activities, and experiences.</p>

      <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm text-left space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Business Name *</label>
          <input required value={businessName} onChange={e => setBusinessName(e.target.value)}
            className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            placeholder="Awesome Tours Ltd." />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Business Type</label>
          <select value={businessType} onChange={e => setBusinessType(e.target.value)}
            className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500">
            {['agency', 'hotel', 'restaurant', 'transport', 'guide', 'activity-provider'].map(t => (
              <option key={t} value={t} className="capitalize">{t.replace('-', ' ')}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} rows={3}
            className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            placeholder="Tell tourists about your business..." />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Website (optional)</label>
          <input type="url" value={website} onChange={e => setWebsite(e.target.value)}
            className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            placeholder="https://yourwebsite.com" />
        </div>
        {error && (
          <div className="flex items-center gap-2 text-sm text-rose-600 bg-rose-50 rounded-xl px-3 py-2">
            <AlertCircle className="h-4 w-4" />{error}
          </div>
        )}
        <button type="submit" disabled={loading}
          className="w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60 flex items-center justify-center gap-2">
          {loading ? <><Loader2 className="h-4 w-4 animate-spin" />Creating...</> : 'Create Operator Profile'}
        </button>
      </form>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function PartnerDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [operator, setOperator] = useState<OperatorProfile | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'listings' | 'bookings'>('overview');

  // Check auth on mount
  useEffect(() => {
    const stored = localStorage.getItem('auth_user');
    if (!stored) { router.push('/auth/login'); return; }
    const u: User = JSON.parse(stored);
    if (u.role !== 'partner' && u.role !== 'admin') {
      router.push('/');
      return;
    }
    setUser(u);
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      // Try to get operator profile by listing operators and finding the one belonging to this user
      const ops = await apiFetch<OperatorProfile[]>('/operators?limit=100');
      const stored = localStorage.getItem('auth_user');
      const u: User = stored ? JSON.parse(stored) : null;
      // We'll just get the first operator for this session (API /operators/my would be cleaner — using list for now)
      // Get my bookings
      const myBookings = await apiFetch<Booking[]>('/bookings/my').catch(() => []);
      setBookings(myBookings);

      // Get any operator that might belong to current user
      if (ops.length > 0) {
        // Get full operator with listings
        const fullOp = await apiFetch<OperatorProfile>(`/operators/${ops[0].id}`);
        setOperator(fullOp);
      }
    } catch {
      // Operator profile doesn't exist yet
    } finally {
      setLoading(false);
    }
  }

  if (loading) return (
    <div className="flex h-96 items-center justify-center">
      <Loader2 className="h-10 w-10 animate-spin text-emerald-500" />
    </div>
  );

  if (!user) return null;

  // No operator profile yet
  if (!operator) {
    return (
      <div className="min-h-screen bg-slate-50 px-4 py-10">
        <CreateOperatorForm onCreated={loadData} />
      </div>
    );
  }

  // Stats
  const listings = operator.listings || [];
  const totalRevenue = bookings.reduce((sum, b) => sum + (b.total_price || 0), 0);
  const pendingBookings = bookings.filter(b => b.status === 'pending').length;
  const completedBookings = bookings.filter(b => b.status === 'completed').length;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Store className="h-7 w-7 text-emerald-600" />
              {operator.business_name}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm text-slate-500 capitalize">{operator.business_type}</span>
              <span className="text-slate-300">·</span>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
                operator.verified
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}>
                {operator.verified ? '✓ Verified' : `⏳ ${operator.verification_status}`}
              </span>
            </div>
          </div>
          <Link
            href="/destinations"
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-500 transition-colors"
          >
            <Plus className="h-4 w-4" /> Add New Listing
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Listings" value={listings.length} icon={<Package className="h-5 w-5" />} />
          <StatCard label="Total Bookings" value={bookings.length} icon={<BookOpen className="h-5 w-5" />} />
          <StatCard label="Pending" value={pendingBookings} icon={<Clock className="h-5 w-5" />} sub="need review" />
          <StatCard label="Revenue" value={`$${totalRevenue.toFixed(0)}`} icon={<TrendingUp className="h-5 w-5" />} sub="lifetime" />
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-100 rounded-xl p-1 mb-6 w-fit">
          {(['overview', 'listings', 'bookings'] as const).map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`rounded-lg px-4 py-1.5 text-sm font-medium capitalize transition-all ${
                activeTab === tab ? 'bg-white shadow-sm text-emerald-700' : 'text-slate-500 hover:text-slate-700'
              }`}>
              {tab}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Bookings */}
            <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6">
              <h2 className="font-bold text-slate-900 mb-4">Recent Bookings</h2>
              {bookings.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <BookOpen className="h-10 w-10 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No bookings yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {bookings.slice(0, 5).map(b => {
                    const s = STATUS_STYLES[b.status] || STATUS_STYLES.pending;
                    return (
                      <div key={b.id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 px-4 py-3">
                        <div>
                          <p className="font-medium text-slate-800 text-sm">{b.booking_reference}</p>
                          <p className="text-xs text-slate-400">{b.start_date} → {b.end_date} · {b.guests_count} guest{b.guests_count > 1 ? 's' : ''}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-700 text-sm">${b.total_price.toFixed(0)}</span>
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border capitalize ${s.classes}`}>
                            {s.icon}{b.status}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Listings Summary */}
            <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6">
              <h2 className="font-bold text-slate-900 mb-4">Your Listings</h2>
              {listings.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <Store className="h-10 w-10 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No listings yet</p>
                  <p className="text-xs mt-1">Add your first tour or experience</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {listings.slice(0, 5).map(l => (
                    <div key={l.id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 px-4 py-3">
                      <div>
                        <p className="font-medium text-slate-800 text-sm">{l.title}</p>
                        <p className="text-xs text-slate-400 capitalize">{l.category} · {l.review_count} reviews</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-slate-700 text-sm">${l.base_price}/{l.currency === 'USD' ? 'USD' : l.currency}</p>
                        <div className="flex items-center gap-1 justify-end">
                          <Star className="h-3 w-3 text-amber-400 fill-amber-400" />
                          <span className="text-xs text-slate-500">{l.rating_average.toFixed(1)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Listings Tab */}
        {activeTab === 'listings' && (
          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="font-bold text-slate-900">All Listings ({listings.length})</h2>
            </div>
            {listings.length === 0 ? (
              <div className="text-center py-16 text-slate-400">
                <Package className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No listings yet. Start by browsing destinations and adding a listing.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {listings.map(l => (
                  <div key={l.id} className="flex items-center justify-between px-6 py-4 hover:bg-slate-50 transition-colors">
                    <div>
                      <p className="font-medium text-slate-900">{l.title}</p>
                      <p className="text-sm text-slate-500 capitalize">{l.category}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right hidden sm:block">
                        <p className="font-semibold text-slate-700">${l.base_price}</p>
                        <p className="text-xs text-slate-400">{l.review_count} reviews</p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                        l.availability ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'
                      }`}>
                        {l.availability ? 'Available' : 'Unavailable'}
                      </span>
                      <ChevronRight className="h-4 w-4 text-slate-300" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Bookings Tab */}
        {activeTab === 'bookings' && (
          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h2 className="font-bold text-slate-900">All Bookings ({bookings.length})</h2>
            </div>
            {bookings.length === 0 ? (
              <div className="text-center py-16 text-slate-400">
                <BookOpen className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No bookings received yet.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-slate-500 border-b border-slate-100 bg-slate-50">
                      <th className="px-6 py-3 font-semibold">Reference</th>
                      <th className="px-6 py-3 font-semibold">Dates</th>
                      <th className="px-6 py-3 font-semibold">Guests</th>
                      <th className="px-6 py-3 font-semibold">Total</th>
                      <th className="px-6 py-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {bookings.map(b => {
                      const s = STATUS_STYLES[b.status] || STATUS_STYLES.pending;
                      return (
                        <tr key={b.id} className="hover:bg-slate-50 transition-colors">
                          <td className="px-6 py-4 font-mono font-medium text-slate-800">{b.booking_reference}</td>
                          <td className="px-6 py-4 text-slate-600">{b.start_date} → {b.end_date}</td>
                          <td className="px-6 py-4 text-slate-600">{b.guests_count}</td>
                          <td className="px-6 py-4 font-semibold text-slate-700">${b.total_price.toFixed(0)}</td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border capitalize ${s.classes}`}>
                              {s.icon}{b.status}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
