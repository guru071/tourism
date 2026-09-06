'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { Compass, Menu, X, LogOut, User } from 'lucide-react';

interface AuthUser {
  id: string;
  email: string;
  full_name?: string;
  role: string;
}

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('auth_user');
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch {}
    }
  }, [pathname]);

  function handleLogout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    setUser(null);
    router.push('/');
  }

  const navLinks = [
    { href: '/', label: 'Explore' },
    ...(user?.role === 'partner' || user?.role === 'admin' ? [{ href: '/partner', label: 'Partner Dashboard' }] : []),
    ...(user?.role === 'admin' ? [{ href: '/control-tower', label: 'Control Tower' }] : []),
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-sm">
            <Compass className="h-5 w-5" />
          </div>
          <span className="font-bold text-slate-900 text-base">TourismOS</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden sm:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                pathname === link.href
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'text-slate-600 hover:text-emerald-600 hover:bg-slate-50'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Auth */}
        <div className="hidden sm:flex items-center gap-2">
          {user ? (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600">
                <User className="h-4 w-4 text-emerald-500" />
                <span className="font-medium max-w-[120px] truncate">{user.full_name || user.email}</span>
                <span className="text-xs text-slate-400 capitalize">({user.role})</span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </div>
          ) : (
            <>
              <Link href="/auth/login" className="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-emerald-600 transition-colors">
                Sign in
              </Link>
              <Link href="/auth/register" className="rounded-lg bg-emerald-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-emerald-500 transition-colors">
                Get started
              </Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="sm:hidden rounded-lg p-2 text-slate-500 hover:bg-slate-100"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="sm:hidden border-t border-slate-200 bg-white px-4 py-4 space-y-2">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="block rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div className="border-t border-slate-100 pt-2 mt-2 space-y-2">
            {user ? (
              <button onClick={handleLogout} className="block w-full text-left rounded-lg px-3 py-2 text-sm text-rose-600 hover:bg-rose-50">
                Logout
              </button>
            ) : (
              <>
                <Link href="/auth/login" className="block rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-50" onClick={() => setMenuOpen(false)}>Sign in</Link>
                <Link href="/auth/register" className="block rounded-lg bg-emerald-600 px-3 py-2 text-sm font-semibold text-white text-center" onClick={() => setMenuOpen(false)}>Get started</Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
