import { Inter, JetBrains_Mono, Rajdhani } from 'next/font/google'
import type { Metadata } from 'next'
import './globals.css'
import '@/styles/military-theme.css'
import { TacticalNav } from '@/components/tactical-nav'

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
  description: 'Tactical multi-agent operations platform',
  icons: {
    icon: '/favicon.svg',
    apple: '/favicon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning className={`${inter.variable} ${jetbrainsMono.variable} ${rajdhani.variable}`}>
      <body className={inter.className}>
        <TacticalNav />
        {children}
      </body>
    </html>
  )
}