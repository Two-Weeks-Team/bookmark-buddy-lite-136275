'use client';

import BookmarkForm from '@/components/BookmarkForm';
import BookmarkList from '@/components/BookmarkList';
import ExportButton from '@/components/ExportButton';

export default function HomePage() {
  return (
    <main className="w-full max-w-2xl space-y-8">
      <h1 className="text-3xl font-bold text-center mb-4">Bookmark Buddy Lite</h1>
      <BookmarkForm />
      <ExportButton />
      <BookmarkList />
    </main>
  );
}
