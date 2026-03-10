export interface Bookmark {
  id: string;
  url: string;
  title: string;
  tags?: string[];
  summary?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

export async function addBookmark(url: string): Promise<Bookmark> {
  const res = await fetch(`${API_BASE}/bookmarks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || 'Failed to add bookmark');
  }
  return res.json();
}

export async function listBookmarks(query?: string): Promise<Bookmark[]> {
  const params = query ? `?q=${encodeURIComponent(query)}` : '';
  const res = await fetch(`${API_BASE}/bookmarks${params}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || 'Failed to fetch bookmarks');
  }
  const data = await res.json();
  return data.bookmarks;
}

export async function exportBookmarks(): Promise<Blob> {
  const res = await fetch(`${API_BASE}/bookmarks/export`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || 'Failed to export');
  }
  const json = await res.json();
  return new Blob([JSON.stringify(json, null, 2)], { type: 'application/json' });
}
