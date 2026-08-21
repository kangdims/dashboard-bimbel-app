import React, { useState, useEffect, useMemo } from 'react';
import { 
  DollarSign, UserPlus, MapPin, Tag, BarChart3, Wallet, RefreshCw, School
} from 'lucide-react';

// ==========================================
// TYPES & MOCK DATA
// ==========================================

export interface FilterState {
  ta: string;
  lokasi: string;
  kecamatan: string;
  kelurahan: string;
  diskon: string;
}

const TA_OPTIONS = ['2025/2026', '2024/2025', '2023/2024', '2022/2023'];
const LOKASI_OPTIONS = ['Semua Lokasi', 'Kampus Utama', 'Kampus Barat', 'Kampus Timur'];
const DISKON_OPTIONS = ['Semua Diskon', 'Prestasi Akademik', 'Yatim/Piatu', 'Saudara Kandung', 'Tahfizh'];

const DOMISILI_DATA: Record<string, string[]> = {
  'Semua Kecamatan': ['Semua Kelurahan'],
  'Kebayoran Baru': ['Semua Kelurahan', 'Gandaria Utara', 'Cipete Utara', 'Pulo', 'Kramat Pela'],
  'Cilandak': ['Semua Kelurahan', 'Cilandak Barat', 'Lebak Bulus', 'Pondok Labu'],
  'Tebet': ['Semua Kelurahan', 'Tebet Barat', 'Tebet Timur', 'Menteng Dalam'],
};

// ==========================================
// MAIN COMPONENT
// ==========================================

export default function DashboardApp() {
  const [activeTab, setActiveTab] = useState<string>('keuangan');

  // State Filter Global
  const [filters, setFilters] = useState<FilterState>(() => {
    const params = new URLSearchParams(window.location.search);
    return {
      ta: params.get('ta') || '2025/2026',
      lokasi: params.get('lokasi') || 'Semua Lokasi',
      kecamatan: params.get('kecamatan') || 'Semua Kecamatan',
      kelurahan: params.get('kelurahan') || 'Semua Kelurahan',
      diskon: params.get('diskon') || 'Semua Diskon',
    };
  });

  // Sinkronisasi Filter ke URL Query String
  useEffect(() => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, '', newUrl);
  }, [filters]);

  // Handler Perubahan Filter
  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters((prev) => {
      const next = { ...prev, [key]: value };
      if (key === 'kecamatan') {
        next.kelurahan = 'Semua Kelurahan';
      }
      return next;
    });
  };

  const handleResetFilter = () => {
    setFilters({
      ta: '2025/2026',
      lokasi: 'Semua Lokasi',
      kecamatan: 'Semua Kecamatan',
      kelurahan: 'Semua Kelurahan',
      diskon: 'Semua Diskon',
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
      {/* HEADER & GLOBAL FILTER BAR */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="p-4 max-w-7xl mx-auto space-y-3">
          <div className="flex justify-between items-center">
            <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <School className="w-6 h-6 text-indigo-600" />
              Sistem Informasi Executive Dashboard
            </h1>
            <button
              onClick={handleResetFilter}
              className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-indigo-600 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-md transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Reset Filter
            </button>
          </div>

          {/* Panel Filter Global */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 bg-slate-100/70 p-3 rounded-lg border border-slate-200">
            {/* Filter 1: Tahun Ajaran */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Tahun Ajaran</label>
              <select
                value={filters.ta}
                onChange={(e) => handleFilterChange('ta', e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs focus:ring-2 focus:ring-indigo-500 outline-none"
              >
                {TA_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>

            {/* Filter 2: Lokasi Belajar */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Lokasi Belajar</label>
              <select
                value={filters.lokasi}
                onChange={(e) => handleFilterChange('lokasi', e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs focus:ring-2 focus:ring-indigo-500 outline-none"
              >
                {LOKASI_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>

            {/* Filter 3: Kecamatan */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Kecamatan</label>
              <select
                value={filters.kecamatan}
                onChange={(e) => handleFilterChange('kecamatan', e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs focus:ring-2 focus:ring-indigo-500 outline-none"
              >
                {Object.keys(DOMISILI_DATA).map((kec) => (
                  <option key={kec} value={kec}>{kec}</option>
                ))}
              </select>
            </div>

            {/* Filter 4: Kelurahan (Cascading) */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Kelurahan</label>
              <select
                value={filters.kelurahan}
                onChange={(e) => handleFilterChange('kelurahan', e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs focus:ring-2 focus:ring-indigo-500 outline-none"
              >
                {(DOMISILI_DATA[filters.kecamatan] || ['Semua Kelurahan']).map((kel) => (
                  <option key={kel} value={kel}>{kel}</option>
                ))}
              </select>
            </div>

            {/* Filter 5: Jenis Diskon */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Jenis Diskon</label>
              <select
                value={filters.diskon}
                onChange={(e) => handleFilterChange('diskon', e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs focus:ring-2 focus:ring-indigo-500 outline-none"
              >
                {DISKON_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </header>

      {/* BODY / MAIN CONTENT */}
      <div className="flex-1 max-w-7xl w-full mx-auto flex flex-col md:flex-row gap-6 p-4">
        {/* SIDEBAR NAVIGATION */}
        <aside className="w-full md:w-64 shrink-0">
          <nav className="bg-white rounded-lg border border-slate-200 p-2 space-y-1">
            {[
              { id: 'keuangan', label: 'Keuangan Transaksi', icon: DollarSign },
              { id: 'pendaftaran', label: 'Pendaftaran Siswa', icon: UserPlus },
              { id: 'sekolah_domisili', label: 'Sekolah & Domisili', icon: MapPin },
              { id: 'siswa_diskon', label: 'Siswa Diskon Khusus', icon: Tag },
              { id: 'perbandingan_3ta', label: 'Perbandingan 3 TA', icon: BarChart3 },
              { id: 'status_bayar_domisili', label: 'Status Bayar Domisili', icon: Wallet },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-md text-xs font-medium transition ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700 font-semibold'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* VIEW CONTAINER */}
        <main className="flex-1 bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
          <ActiveViewRender activeTab={activeTab} filters={filters} />
        </main>
      </div>
    </div>
  );
}

// ==========================================
// MENU ROUTER & VIEWS IMPLEMENTATION
// ==========================================

function ActiveViewRender({ activeTab, filters }: { activeTab: string; filters: FilterState }) {
  switch (activeTab) {
    case 'keuangan':
      return <KeuanganTransaksiView filters={filters} />;
    case 'pendaftaran':
      return <PendaftaranSiswaView filters={filters} />;
    case 'sekolah_domisili':
      return <SekolahDomisiliView filters={filters} />;
    case 'siswa_diskon':
      return <SiswaDiskonKhususView filters={filters} />;
    case 'perbandingan_3ta':
      return <Perbandingan3TAView filters={filters} />;
    case 'status_bayar_domisili':
      return <StatusBayarDomisiliView filters={filters} />;
    default:
      return null;
  }
}

// Helper Card Filter Status Bar
function FilterBadgeSummary({ filters }: { filters: FilterState }) {
  return (
    <div className="mb-4 p-3 bg-indigo-50/50 rounded-md border border-indigo-100 flex flex-wrap gap-2 text-xs text-indigo-900">
      <span className="font-semibold">Filter Aktif:</span>
      <span className="bg-white px-2 py-0.5 rounded border border-indigo-200">TA: {filters.ta}</span>
      <span className="bg-white px-2 py-0.5 rounded border border-indigo-200">Lokasi: {filters.lokasi}</span>
      <span className="bg-white px-2 py-0.5 rounded border border-indigo-200">Kec: {filters.kecamatan}</span>
      <span className="bg-white px-2 py-0.5 rounded border border-indigo-200">Kel: {filters.kelurahan}</span>
      <span className="bg-white px-2 py-0.5 rounded border border-indigo-200">Diskon: {filters.diskon}</span>
    </div>
  );
}

// 1. Menu Keuangan Transaksi
function KeuanganTransaksiView({ filters }: { filters: FilterState }) {
  return (
    <div>
      <h2 className="text-lg font-bold mb-1">Keuangan & Transaksi</h2>
      <p className="text-xs text-slate-500 mb-4">Ringkasan arus kas, pelunasan, dan tunggakan biaya siswa.</p>
      <FilterBadgeSummary filters={filters} />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
          <p className="text-xs text-emerald-600 font-medium">Total Penerimaan</p>
          <p className="text-xl font-bold text-emerald-900 mt-1">Rp 1.450.000.000</p>
        </div>
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-xs text-amber-600 font-medium">Sisa Piutang/Tunggakan</p>
          <p className="text-xl font-bold text-amber-900 mt-1">Rp 185.000.000</p>
        </div>
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs text-blue-600 font-medium">Capaian Pelunasan</p>
          <p className="text-xl font-bold text-blue-900 mt-1">88.7%</p>
        </div>
      </div>
    </div>
  );
}

// 2. Menu Pendaftaran Siswa
function PendaftaranSiswaView({ filters }: { filters: FilterState }) {
  return (
    <div>
      <h2 className="text-lg font-bold mb-1">Pendaftaran Siswa Baru</h2>
      <p className="text-xs text-slate-500 mb-4">Statistik pendaftar, status lulus seleksi, dan registrasi ulang.</p>
      <FilterBadgeSummary filters={filters} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 border rounded-lg">
          <p className="text-xs font-semibold text-slate-500">Total Pendaftar ({filters.ta})</p>
          <p className="text-2xl font-bold text-indigo-600">420 Siswa</p>
        </div>
        <div className="p-4 border rounded-lg">
          <p className="text-xs font-semibold text-slate-500">Siswa Terverifikasi</p>
          <p className="text-2xl font-bold text-emerald-600">385 Siswa</p>
        </div>
      </div>
    </div>
  );
}

// 3. Menu Sekolah & Domisili
function SekolahDomisiliView({ filters }: { filters: FilterState }) {
  return (
    <div>
      <h2 className="text-lg font-bold mb-1">Sekolah Asal & Sebaran Domisili</h2>
      <p className="text-xs text-slate-500 mb-4">Pemetaan wilayah tinggal siswa dan asal sekolah pendaftar.</p>
      <FilterBadgeSummary filters={filters} />

      <div className="p-4 border border-dashed rounded-lg text-center bg-slate-50">
        <p className="text-xs text-slate-600">
          Menampilkan sebaran geografis untuk <b>{filters.kecamatan}</b> - <b>{filters.kelurahan}</b> pada unit <b>{filters.lokasi}</b>.
        </p>
      </div>
    </div>
  );
}

// 4. Menu Siswa Diskon Khusus
function SiswaDiskonKhususView({ filters }: { filters: FilterState }) {
  return (
    <div>
      <h2 className="text-lg font-bold mb-1">Penerima Diskon & Beasiswa</h2>
      <p className="text-xs text-slate-500 mb-4">Rincian penerima beasiswa berdasarkan skema khusus.</p>
      <FilterBadgeSummary filters={filters} />

      <table className="w-full text-xs text-left border-collapse border border-slate-200 mt-2">
        <thead className="bg-slate-100">
          <tr>
            <th className="p-2 border">Kategori Diskon</th>
            <th className="p-2 border">Lokasi</th>
            <th className="p-2 border">Wilayah</th>
            <th className="p-2 border">Jumlah Penerima</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="p-2 border font-medium">{filters.diskon}</td>
            <td className="p-2 border">{filters.lokasi}</td>
            <td className="p-2 border">{filters.kecamatan}</td>
            <td className="p-2 border font-bold">64 Siswa</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

// 5. Menu Perbandingan 3 TA
function Perbandingan3TAView({ filters }: { filters: FilterState }) {
  const years = useMemo(() => {
    const baseYear = parseInt(filters.ta.split('/')[0]) || 2025;
    return [
      `${baseYear}/${baseYear + 1}`,
      `${baseYear - 1}/${baseYear}`,
      `${baseYear - 2}/${baseYear - 1}`,
    ];
  }, [filters.ta]);

  return (
    <div>
      <h2 className="text-lg font-bold mb-1">Perbandingan Multi-Tahun Ajaran</h2>
      <p className="text-xs text-slate-500 mb-4">Analisis tren 3 tahun berturut-turut berpatokan pada {filters.ta}.</p>
      <FilterBadgeSummary filters={filters} />

      <div className="grid grid-cols-3 gap-4 text-center">
        {years.map((y, idx) => (
          <div key={y} className={`p-4 rounded-lg border ${idx === 0 ? 'bg-indigo-50 border-indigo-300' : 'bg-slate-50 border-slate-200'}`}>
            <p className="text-xs font-semibold text-slate-500">{idx === 0 ? 'Anchor Year (TA Active)' : `TA ${y}`}</p>
            <p className="text-base font-bold text-slate-800 mt-1">{y}</p>
            <p className="text-xs text-slate-600 mt-2">Pendaftar: {350 - idx * 25} Siswa</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// 6. Menu Status Bayar Domisili
function StatusBayarDomisiliView({ filters }: { filters: FilterState }) {
  return (
    <div>
      <h2 className="text-lg font-bold mb-1">Status Pembayaran per Domisili</h2>
      <p className="text-xs text-slate-500 mb-4">Matriks pelunasan SPP/Pangkal berbasis wilayah domisili.</p>
      <FilterBadgeSummary filters={filters} />

      <div className="p-4 border rounded-lg space-y-2">
        <div className="flex justify-between text-xs font-medium">
          <span>Kecamatan {filters.kecamatan}</span>
          <span className="text-emerald-600 font-bold">91.2% Lunas</span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-2">
          <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '91.2%' }}></div>
        </div>
      </div>
    </div>
  );
}
