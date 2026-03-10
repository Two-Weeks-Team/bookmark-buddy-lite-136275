'use client';

import { useEffect, useState, useCallback } from 'react';
import { listBookmarks, Bookmark } from '@/lib/api';

export default function BookmarkList() {
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBookmarks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listBookmarks(query);
      setBookmarks(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    fetchBookmarks();
  }, [fetchBookmarks]);

  return (
    <section>
      <h2 className="text-2xl font-semibold mb-4">Saved Bookmarks</h2>
      <input
        type="text"
        placeholder="Search…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="border rounded p-2 w-full mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      {loading && <p>Loading…</p>}
      {error && <p className="text-red-600">{error}</p>}
      <ul className="space-y-3">
        {bookmarks.map((bm) => (
          <li key={bm.id} className="p-3 border rounded bg-white">
            <a href={bm.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
              {bm.title}
            </a>
            {bm.tags && bm.tags.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {bm.tags.map((tag) => (
                  <span key={tag} className="bg-gray-200 text-gray-800 px-2 py-0.5 rounded text-sm">
                    {tag}
                  </span>
                ))}
              </div>
            )}
            {bm.summary && (
              <p className="mt-2 text-sm text-gray-600">{bm.summary}</p>
            )}
          </li>
        ))}
        {bookmarks.length === 0 && !loading && <p>No bookmarks found.</p>}
      </ul>
    </section>
  );
}
