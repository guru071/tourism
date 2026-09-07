'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchDashboard, fetchCongestion, fetchRevenue, fetchUsers, updateUserRole, updateUserStatus, verifyOperator, getApiBaseUrl } from '@/lib/api';
import { Users, BookOpen, MapPin, AlertTriangle, Loader2, BarChart3, ShieldCheck } from 'lucide-react';

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

// Simple fetcher with auth header for admin pages
async function secureFetch(path: string, options?: RequestInit) {
  const token = localStorage.getItem('auth_token');
  const res = await fetch(`${getApiBaseUrl()}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers
    }
  });
  if (!res.ok) throw new Error('API failed');
  return res.json();
}

export default function ControlTowerPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [congestion, setCongestion] = useState<CongestionAlert[]>([]);
  const [revenue, setRevenue] = useState<RevenueMonth[]>([]);
  
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'operators'>('overview');
  const [users, setUsers] = useState<any[]>([]);
  const [operators, setOperators] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  async function loadData() {
    setLoading(true);
    try {
      if (activeTab === 'overview') {
        const [dashData, congData, revData] = await Promise.all([
          fetchDashboard(),
          fetchCongestion(),
          fetchRevenue(),
        ]);
        setStats(dashData as unknown as DashboardStats);
        setCongestion(congData as unknown as CongestionAlert[]);
        setRevenue(revData as unknown as RevenueMonth[]);
      } else if (activeTab === 'users') {
        const data = await fetchUsers();
        setUsers(data);
      } else if (activeTab === 'operators') {
        const data = await secureFetch('/operators?limit=100');
        setOperators(data);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load dashboard. Admin access required.');
    } finally {
      setLoading(false);
    }
  }

  const handleRoleChange = async (userId: string, role: string) => {
    await updateUserRole(userId, role);
    loadData();
  };

  const handleStatusChange = async (userId: string, isActive: boolean) => {
    await updateUserStatus(userId, isActive);
    loadData();
  };

  const handleVerifyOperator = async (operatorId: string, status: string) => {
    await verifyOperator(operatorId, status);
    loadData();
  };

  if (loading && !stats && !users.length && !operators.length) return (
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
            <ShieldCheck className="h-7 w-7 text-emerald-600" />
            Control Tower
          </h1>
          <p className="text-slate-500 text-sm mt-1">System-wide analytics, user management, and health monitoring</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-200 rounded-xl p-1 mb-6 w-fit">
          {(['overview', 'users', 'operators'] as const).map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`rounded-lg px-4 py-2 text-sm font-medium capitalize transition-all ${
                activeTab === tab ? 'bg-white shadow-sm text-emerald-700' : 'text-slate-500 hover:text-slate-700'
              }`}>
              {tab}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && (
          <div className="space-y-8 animate-in fade-in">
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
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="rounded-2xl bg-white border border-slate-200 shadow-sm overflow-hidden animate-in fade-in">
            <div className="p-6 border-b border-slate-100">
              <h2 className="font-bold text-slate-900">User Management</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 border-b border-slate-100 text-xs text-slate-500 uppercase">
                  <tr>
                    <th className="px-6 py-3 font-semibold">Email</th>
                    <th className="px-6 py-3 font-semibold">Role</th>
                    <th className="px-6 py-3 font-semibold">Status</th>
                    <th className="px-6 py-3 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {users.map(u => (
                    <tr key={u.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 font-medium text-slate-900">{u.email}</td>
                      <td className="px-6 py-4">
                        <select 
                          className="border border-slate-200 rounded px-2 py-1 text-sm bg-white"
                          value={u.role}
                          onChange={(e) => handleRoleChange(u.id, e.target.value)}
                        >
                          <option value="tourist">Tourist</option>
                          <option value="partner">Partner</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${u.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                          {u.is_active ? 'Active' : 'Deactivated'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <button 
                          onClick={() => handleStatusChange(u.id, !u.is_active)}
                          className={`text-xs px-3 py-1.5 rounded font-medium border ${u.is_active ? 'border-rose-200 text-rose-600 hover:bg-rose-50' : 'border-emerald-200 text-emerald-600 hover:bg-emerald-50'}`}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Operators Tab */}
        {activeTab === 'operators' && (
          <div className="rounded-2xl bg-white border border-slate-200 shadow-sm overflow-hidden animate-in fade-in">
            <div className="p-6 border-b border-slate-100">
              <h2 className="font-bold text-slate-900">Operator Verification</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 border-b border-slate-100 text-xs text-slate-500 uppercase">
                  <tr>
                    <th className="px-6 py-3 font-semibold">Business Name</th>
                    <th className="px-6 py-3 font-semibold">Type</th>
                    <th className="px-6 py-3 font-semibold">Email</th>
                    <th className="px-6 py-3 font-semibold">Status</th>
                    <th className="px-6 py-3 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {operators.map(op => (
                    <tr key={op.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 font-medium text-slate-900">{op.business_name}</td>
                      <td className="px-6 py-4 text-slate-500 capitalize">{op.business_type}</td>
                      <td className="px-6 py-4 text-slate-500">{op.contact_email}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          op.verification_status === 'approved' ? 'bg-emerald-100 text-emerald-800' :
                          op.verification_status === 'rejected' ? 'bg-rose-100 text-rose-800' :
                          'bg-amber-100 text-amber-800'
                        }`}>
                          {op.verification_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 flex gap-2">
                        {op.verification_status !== 'approved' && (
                          <button 
                            onClick={() => handleVerifyOperator(op.id, 'approved')}
                            className="text-xs px-3 py-1.5 rounded font-medium border border-emerald-200 text-emerald-600 hover:bg-emerald-50"
                          >
                            Approve
                          </button>
                        )}
                        {op.verification_status !== 'rejected' && (
                          <button 
                            onClick={() => handleVerifyOperator(op.id, 'rejected')}
                            className="text-xs px-3 py-1.5 rounded font-medium border border-rose-200 text-rose-600 hover:bg-rose-50"
                          >
                            Reject
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
