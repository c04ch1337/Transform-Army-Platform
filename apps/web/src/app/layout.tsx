import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Transform Army AI',
  description: 'Multi-agent AI platform for business transformation',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}