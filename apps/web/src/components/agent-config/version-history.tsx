'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ConfigVersion } from '@/types'
import { History, RotateCcw, Clock, FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface VersionHistoryProps {
  versions: ConfigVersion[]
  currentVersion?: number
  onRestore: (version: number) => void
  isLoading?: boolean
}

export function VersionHistory({ versions, currentVersion, onRestore, isLoading = false }: VersionHistoryProps) {
  const [expandedVersion, setExpandedVersion] = useState<number | null>(null)
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null)

  const toggleExpand = (version: number) => {
    setExpandedVersion(expandedVersion === version ? null : version)
  }

  const handleRestore = (version: number) => {
    if (confirm(`Are you sure you want to restore to version ${version}? This will create a new version with the previous configuration.`)) {
      onRestore(version)
    }
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true })
    } catch {
      return timestamp
    }
  }

  const getDiffSummary = (changes: string) => {
    // Parse changes if JSON, otherwise return as is
    try {
      const parsed = JSON.parse(changes)
      return Object.keys(parsed).join(', ')
    } catch {
      return changes
    }
  }

  if (versions.length === 0) {
    return (
      <Card className="bg-tactical-black/50 border-tactical-green/30">
        <CardContent className="py-12 text-center">
          <History className="w-12 h-12 mx-auto mb-4 text-tactical-green/50" />
          <p className="text-gray-400 font-mono">No version history available</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card className="bg-tactical-black/50 border-tactical-green/30">
        <CardHeader>
          <CardTitle className="text-tactical-gold font-tactical uppercase tracking-wider flex items-center gap-2">
            <History className="w-5 h-5" />
            Configuration Version History
          </CardTitle>
          <p className="text-sm text-gray-400 font-mono mt-2">
            View and restore previous configuration versions. Each save creates a new version.
          </p>
        </CardHeader>
      </Card>

      {/* Timeline */}
      <div className="space-y-3">
        {versions.map((version, index) => {
          const isExpanded = expandedVersion === version.version
          const isCurrent = currentVersion === version.version
          const isSelected = selectedVersion === version.version

          return (
            <Card
              key={version.version}
              className={`transition-all ${
                isCurrent
                  ? 'bg-tactical-green/10 border-tactical-green'
                  : isSelected
                  ? 'bg-tactical-blue/10 border-tactical-blue'
                  : 'bg-tactical-black/50 border-tactical-green/30 hover:border-tactical-green/50'
              }`}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  {/* Timeline Line */}
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-4 h-4 rounded-full border-2 ${
                        isCurrent
                          ? 'border-tactical-green bg-tactical-green'
                          : 'border-tactical-green/50 bg-tactical-black'
                      }`}
                    />
                    {index < versions.length - 1 && (
                      <div className="w-0.5 h-full min-h-[40px] bg-tactical-green/30 mt-2" />
                    )}
                  </div>

                  {/* Version Info */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-tactical text-lg text-tactical-gold">
                            Version {version.version}
                          </h3>
                          {isCurrent && (
                            <Badge className="bg-tactical-green text-white font-mono text-xs">
                              Current
                            </Badge>
                          )}
                          <Badge variant="outline" className="border-tactical-green/30 text-tactical-green font-mono text-xs">
                            <Clock className="w-3 h-3 mr-1" />
                            {formatTimestamp(version.timestamp)}
                          </Badge>
                        </div>

                        <p className="text-sm text-gray-400 font-mono mb-3">
                          {version.changes || 'No description provided'}
                        </p>

                        {/* Preview Summary */}
                        <div className="flex flex-wrap gap-2 mb-3">
                          {version.config.name && (
                            <Badge variant="outline" className="border-tactical-green/20 text-tactical-green font-mono text-xs">
                              {version.config.name}
                            </Badge>
                          )}
                          {version.config.model?.model && (
                            <Badge variant="outline" className="border-tactical-blue/20 text-tactical-blue font-mono text-xs">
                              {version.config.model.model}
                            </Badge>
                          )}
                          {version.config.functions && version.config.functions.length > 0 && (
                            <Badge variant="outline" className="border-tactical-gold/20 text-tactical-gold font-mono text-xs">
                              {version.config.functions.length} functions
                            </Badge>
                          )}
                        </div>

                        {/* Expanded Details */}
                        {isExpanded && (
                          <Card className="bg-tactical-black/50 border-tactical-green/20 mt-3">
                            <CardContent className="p-3">
                              <pre className="text-xs font-mono text-terminal-green overflow-x-auto">
                                {JSON.stringify(version.config, null, 2)}
                              </pre>
                            </CardContent>
                          </Card>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex flex-col gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => toggleExpand(version.version)}
                          className="border-tactical-green/30 text-tactical-green hover:bg-tactical-green/10 font-mono"
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="w-4 h-4 mr-1" />
                              Hide
                            </>
                          ) : (
                            <>
                              <ChevronDown className="w-4 h-4 mr-1" />
                              View
                            </>
                          )}
                        </Button>
                        {!isCurrent && (
                          <Button
                            size="sm"
                            onClick={() => handleRestore(version.version)}
                            className="bg-tactical-blue hover:bg-tactical-blue/80 text-white font-mono"
                            disabled={isLoading}
                          >
                            <RotateCcw className="w-4 h-4 mr-1" />
                            Restore
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Info Box */}
      <Card className="bg-tactical-black/30 border-tactical-green/20">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <FileText className="w-5 h-5 text-tactical-green mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-mono text-gray-400">
                <strong className="text-tactical-green">Version Control:</strong> Each configuration change
                is automatically versioned. You can restore any previous version, which will create a new
                version with the restored configuration. This ensures you never lose any configuration state.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}