import { Inter, JetBrains_Mono, Rajdhani } from 'next/font/google'
import type { Metadata, Viewport } from 'next'
import './globals.css'
import '@/styles/military-theme.css'
import { TacticalHeader } from '@/components/tactical-header'
import { TacticalNav } from '@/components/tactical-nav'
import { ToastProvider } from '@/components/ui/use-toast'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap'
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap'
})

const rajdhani = Rajdhani({
  weight: ['400', '500', '600', '700'],
  subsets: ['latin'],
  variable: '--font-tactical',
  display: 'swap'
})

export const metadata: Metadata = {
  title: 'Transform Army AI - Command Center',
  description: 'Tactical multi-agent operations platform for business automation',
  keywords: ['AI agents', 'automation', 'CRM', 'helpdesk', 'business operations'],
  authors: [{ name: 'Transform Army AI' }],
  icons: {
    icon: '/favicon.svg',
    apple: '/favicon.svg',
  },
  openGraph: {
    title: 'Transform Army AI - Command Center',
    description: 'Tactical multi-agent operations platform',
    type: 'website',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#4A7C59',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning className={`dark ${inter.variable} ${jetbrainsMono.variable} ${rajdhani.variable}`}>
      <body className={`${inter.className} bg-tactical-black text-foreground antialiased`}>
        <ToastProvider>
          <TacticalNav />
          {children}
          <Toaster />
        </ToastProvider>
      </body>
    </html>
  )
}