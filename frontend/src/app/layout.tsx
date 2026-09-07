import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/components/Navbar';
import Chatbot from '@/components/Chatbot';

export const metadata: Metadata = {
  title: 'TourismOS — AI Tourism Ecosystem',
  description: 'Discover your perfect journey with AI-powered itinerary planning.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col antialiased bg-white">
        <Navbar />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-400">
          <p>AI Tourism Ecosystem &copy; {new Date().getFullYear()} &bull; Next.js 14 + FastAPI + PostgreSQL 15</p>
        </footer>
        <Chatbot />
      </body>
    </html>
  );
}
