import './globals.css';

export const metadata = {
  title: 'Bookmark Buddy Lite',
  description: 'Fast, private web‑page saver – one click, no frills.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen flex flex-col items-center p-4">
        {children}
      </body>
    </html>
  );
}
