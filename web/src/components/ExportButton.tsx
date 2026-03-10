'use client';

import { exportBookmarks } from '@/lib/api';
import { useState } from 'react';

export default function ExportButton() {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setDownloading(true);
    setError(null);
    try {
      const blob = await exportBookmarks();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'bookmarks.json';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <button
        onClick={handleExport}
        disabled={downloading}
        className="bg-green-600 text-white py-1 px-3 rounded hover:bg-green-700 disabled:opacity-50"
      >
        {downloading ? 'Preparing…' : 'Export Bookmarks'}
      </button>
      {error && <span className="text-red-600">{error}</span>}
    </div>
  );
}
