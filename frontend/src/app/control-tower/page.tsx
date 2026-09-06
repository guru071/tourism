'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchDashboard, fetchCongestion, fetchRevenue } from '@/lib/api';
import { Users, BookOpen, MapPin, AlertTriangle, Loader2, BarChart3 } from 'lucide-react';

interface DashboardStats {
  total_users: number;
  total_bookings: number;
  total_revenue: number;
  active_destinations: number;
  top_destinations: Array<{ id: string; name: string; booking_count: number }>;
  booking_status_breakdown: Record<string, number>;
}

interface CongestionAlert {
  destination_id: string;
  destination_name: string;
  bookings_last_7_days: number;
  congestion_level: string;
  threshold: number;
}

interface RevenueMonth {
  month: string;
  revenue: number;
  booking_count: number;
}

const LEVEL_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-amber-100 text-amber-800 border-amber-200',
  low: 'bg-green-100 text-green-800 border-green-200',
};

export default function ControlTowerPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [congestion, setCongestion] = useState<CongestionAlert[]>([]);
  const [revenue, setRevenue] = useState<RevenueMonth[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [dashData, congData, revData] = await Promise.all([
          fetchDashboard(),
          fetchCongestion(),
          fetchRevenue(),
        ]);
        setStats(dashData as unknown as DashboardStats);
        setCongestion(congData as unknown as CongestionAlert[]);
        setRevenue(revData as unknown as RevenueMonth[]);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Failed to load dashboard. Admin access required.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return (
    <div className="flex h-96 items-center justify-center">
      <Loader2 className="h-10 w-10 animate-spin text-emerald-500" />
    </div>
  );

  if (error) return (
    <div className="flex flex-col h-96 items-center justify-center gap-4 text-center px-4">
      <AlertTriangle className="h-12 w-12 text-amber-400" />
      <p className="text-slate-600 max-w-sm">{error}</p>
      <Link href="/auth/login" className="text-sm text-emerald-600 underline">Login as admin →</Link>
    </div>
  );

  const maxBookings = Math.max(...revenue.map((r) => r.booking_count), 1);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="h-7 w-7 text-emerald-600" />
            Control Tower
          </h1>
          <p className="text-slate-500 text-sm mt-1">System-wide analytics and destination health monitoring</p>
        </div>

        {/* Summary Cards */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Total Users', value: stats.total_users, icon: <Users className="h-5 w-5" />, color: 'text-blue-600 bg-blue-50' },
              { label: 'Total Bookings', value: stats.total_bookings, icon: <BookOpen className="h-5 w-5" />, color: 'text-purple-600 bg-purple-50' },
              { label: 'Active Destinations', value: stats.active_destinations, icon: <MapPin className="h-5 w-5" />, color: 'text-emerald-600 bg-emerald-50' },
              { label: 'Total Revenue', value: `$${stats.total_revenue.toFixed(0)}`, icon: <BarChart3 className="h-5 w-5" />, color: 'text-teal-600 bg-teal-50' },
            ].map((card) => (
              <div key={card.label} className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm">
                <div className={`inline-flex h-10 w-10 items-center justify-center rounded-xl ${card.color} mb-3`}>
                  {card.icon}
                </div>
                <div className="text-2xl font-bold text-slate-900">{card.value}</div>
                <div className="text-sm text-slate-500 mt-0.5">{card.label}</div>
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Destinations */}
          {stats && stats.top_destinations.length > 0 && (
            <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
              <h2 className="font-bold text-slate-900 mb-4">Top Destinations by Bookings</h2>
              <div className="space-y-3">
                {stats.top_destinations.map((d, i) => (
                  <div key={d.id} className="flex items-center gap-3">
                    <span className="text-slate-400 text-sm w-5 text-center font-mono">{i + 1}</span>
                    <div className="flex-1">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium text-slate-800">{d.name}</span>
                        <span className="text-slate-500">{d.booking_count} bookings</span>
                      </div>
                      <div className="mt-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-emerald-500"
                          style={{ width: `${(d.booking_count / (stats.top_destinations[0]?.booking_count || 1)) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Revenue Bar Chart */}
          {revenue.length > 0 && (
            <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
              <h2 className="font-bold text-slate-900 mb-4">Bookings — Last 12 Months</h2>
              <div className="flex items-end gap-1 h-32">
                {revenue.map((r) => (
                  <div key={r.month} className="flex-1 flex flex-col items-center gap-1">
                    <div
                      className="w-full rounded-t bg-emerald-400 hover:bg-emerald-500 transition-colors"
                      style={{ height: `${(r.booking_count / maxBookings) * 100}%`, minHeight: '4px' }}
                      title={`${r.month}: ${r.booking_count} bookings`}
                    />
                    <span className="text-[9px] text-slate-400 truncate w-full text-center">{r.month?.slice(5)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Congestion Alerts */}
        {congestion.length > 0 && (
          <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
            <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Destination Congestion Alerts (Last 7 Days)
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
                    <th className="pb-2 font-semibold">Destination</th>
                    <th className="pb-2 font-semibold">Bookings (7d)</th>
                    <th className="pb-2 font-semibold">Threshold</th>
                    <th className="pb-2 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {congestion.map((alert) => (
                    <tr key={alert.destination_id} className="py-2">
                      <td className="py-2 font-medium text-slate-800">{alert.destination_name}</td>
                      <td className="py-2 text-slate-600">{alert.bookings_last_7_days}</td>
                      <td className="py-2 text-slate-400">{alert.threshold}</td>
                      <td className="py-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border capitalize ${LEVEL_COLORS[alert.congestion_level] || ''}`}>
                          {alert.congestion_level}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Booking Status Breakdown */}
        {stats && Object.keys(stats.booking_status_breakdown).length > 0 && (
          <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
            <h2 className="font-bold text-slate-900 mb-4">Booking Status Breakdown</h2>
            <div className="flex flex-wrap gap-4">
              {Object.entries(stats.booking_status_breakdown).map(([status, count]) => (
                <div key={status} className="rounded-xl border border-slate-200 px-4 py-3 text-center min-w-[100px]">
                  <div className="text-2xl font-bold text-slate-900">{count}</div>
                  <div className="text-xs text-slate-500 capitalize mt-0.5">{status}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
