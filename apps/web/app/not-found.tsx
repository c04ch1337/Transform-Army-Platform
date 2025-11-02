import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ArrowLeft, AlertTriangle, Home, Search } from 'lucide-react'

/**
 * Military-Themed 404 Not Found Page
 * Displays when a route is not found
 */
export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-tactical-black via-tactical-black-light to-tactical-black flex items-center justify-center p-4">
      <Card className="max-w-2xl w-full bg-tactical-black/50 border-terminal-red/30">
        <CardContent className="p-8 md:p-12 text-center">
          {/* Alert Icon */}
          <div className="relative mb-6">
            <div className="absolute inset-0 animate-ping">
              <AlertTriangle className="w-24 h-24 mx-auto text-terminal-red/30" />
            </div>
            <AlertTriangle className="w-24 h-24 mx-auto text-terminal-red relative" />
          </div>

          {/* Error Code */}
          <div className="mb-6">
            <h1 className="font-tactical text-7xl md:text-9xl text-terminal-red font-bold tracking-wider mb-2">
              404
            </h1>
            <div className="font-mono text-sm text-tactical-gold uppercase tracking-widest">
              ERROR CODE: TARGET_NOT_FOUND
            </div>
          </div>

          {/* Message */}
          <div className="mb-8 space-y-3">
            <h2 className="font-tactical text-2xl md:text-3xl text-tactical-gold uppercase">
              Mission Area Not Found
            </h2>
            <p className="text-gray-400 font-mono text-sm max-w-md mx-auto">
              The tactical coordinates you're attempting to reach are not in our operational map. 
              The target may have been relocated or never existed in our systems.
            </p>
          </div>

          {/* Tactical Grid Background Effect */}
          <div className="relative py-6 mb-8">
            <div className="absolute inset-0 tactical-grid opacity-20" />
            <div className="relative space-y-2 font-mono text-xs text-terminal-green/60">
              <div className="scan-lines">
                <p>{'> SCANNING AVAILABLE ROUTES...'}</p>
                <p>{'> CHECKING FALLBACK POSITIONS...'}</p>
                <p>{'> AWAITING OPERATOR INSTRUCTIONS...'}</p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              asChild
              className="bg-tactical-green hover:bg-tactical-green-light text-white font-tactical font-semibold border border-tactical-green-dark shadow-lg hover:shadow-tactical-green/50 transition-all"
            >
              <Link href="/">
                <Home className="w-4 h-4 mr-2" />
                Return to Command Center
              </Link>
            </Button>
            
            <Button
              asChild
              variant="outline"
              className="border-tactical-gold text-tactical-gold hover:bg-tactical-gold/20 font-mono uppercase tracking-wider"
            >
              <Link href="/agents">
                <Search className="w-4 h-4 mr-2" />
                Browse Agents
              </Link>
            </Button>
          </div>

          {/* Additional Help */}
          <div className="mt-8 pt-6 border-t border-tactical-green/20">
            <p className="text-xs text-gray-500 font-mono">
              If you believe this is an error, contact mission control or check your tactical navigation logs.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}