'use client'

import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AgentConfig } from '@/types'
import { Save, RotateCcw, AlertCircle, CheckCircle, Code } from 'lucide-react'

interface JsonEditorProps {
  config: AgentConfig | null
  onSave: (config: AgentConfig) => void
  onCancel: () => void
  onValidate?: (config: any) => Promise<{ is_valid: boolean; errors: string[] }>
  isLoading?: boolean
}

export function JsonEditor({ config, onSave, onCancel, onValidate, isLoading = false }: JsonEditorProps) {
  const [editorValue, setEditorValue] = useState<string>('')
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const [isValid, setIsValid] = useState<boolean>(true)
  const [isValidating, setIsValidating] = useState<boolean>(false)

  useEffect(() => {
    if (config) {
      setEditorValue(JSON.stringify(config, null, 2))
      setValidationErrors([])
      setIsValid(true)
    }
  }, [config])

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setEditorValue(value)
      // Clear validation errors when user types
      if (validationErrors.length > 0) {
        setValidationErrors([])
      }
    }
  }

  const validateJson = async () => {
    try {
      const parsed = JSON.parse(editorValue)
      
      // Client-side validation
      const errors: string[] = []
      
      if (!parsed.name) errors.push('Agent name is required')
      if (!parsed.model?.model) errors.push('Model configuration is required')
      if (!parsed.systemPrompt) errors.push('System prompt is required')
      if (!parsed.firstMessage) errors.push('First message is required')

      if (errors.length > 0) {
        setValidationErrors(errors)
        setIsValid(false)
        return false
      }

      // Server-side validation if available
      if (onValidate) {
        setIsValidating(true)
        try {
          const result = await onValidate(parsed)
          setValidationErrors(result.errors)
          setIsValid(result.is_valid)
          return result.is_valid
        } catch (error) {
          setValidationErrors(['Failed to validate configuration on server'])
          setIsValid(false)
          return false
        } finally {
          setIsValidating(false)
        }
      }

      setIsValid(true)
      return true
    } catch (error) {
      setValidationErrors(['Invalid JSON format. Please check syntax.'])
      setIsValid(false)
      return false
    }
  }

  const handleSave = async () => {
    const valid = await validateJson()
    if (valid) {
      try {
        const parsed = JSON.parse(editorValue)
        onSave(parsed)
      } catch (error) {
        setValidationErrors(['Failed to parse JSON'])
      }
    }
  }

  const handleFormat = () => {
    try {
      const parsed = JSON.parse(editorValue)
      setEditorValue(JSON.stringify(parsed, null, 2))
      setValidationErrors([])
      setIsValid(true)
    } catch (error) {
      setValidationErrors(['Cannot format invalid JSON'])
    }
  }

  const handleReset = () => {
    if (config) {
      setEditorValue(JSON.stringify(config, null, 2))
      setValidationErrors([])
      setIsValid(true)
    }
  }

  return (
    <div className="space-y-4">
      {/* Validation Status */}
      {validationErrors.length > 0 && (
        <Card className="bg-terminal-red/10 border-terminal-red/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-terminal-red font-mono text-sm uppercase">
              <AlertCircle className="w-4 h-4" />
              Validation Errors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {validationErrors.map((error, idx) => (
                <li key={idx} className="text-sm text-terminal-red font-mono flex items-start gap-2">
                  <span className="text-terminal-red mt-0.5">●</span>
                  <span>{error}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {isValid && validationErrors.length === 0 && editorValue && (
        <Card className="bg-terminal-green/10 border-terminal-green/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-terminal-green font-mono text-sm">
              <CheckCircle className="w-4 h-4" />
              Configuration is valid
            </div>
          </CardContent>
        </Card>
      )}

      {/* Editor */}
      <Card className="bg-tactical-black/50 border-tactical-green/30">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-tactical-gold font-tactical uppercase tracking-wider flex items-center gap-2">
              <Code className="w-5 h-5" />
              JSON Configuration Editor
            </CardTitle>
            <div className="flex gap-2">
              <Badge 
                variant="outline" 
                className={`font-mono text-xs ${
                  isValid 
                    ? 'border-terminal-green text-terminal-green' 
                    : 'border-terminal-red text-terminal-red'
                }`}
              >
                {isValid ? 'Valid' : 'Invalid'}
              </Badge>
              <Button
                size="sm"
                variant="outline"
                onClick={handleFormat}
                className="border-tactical-green/30 text-tactical-green hover:bg-tactical-green/10 font-mono"
                disabled={isLoading}
              >
                Format
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="border-t border-tactical-green/20">
            <Editor
              height="600px"
              defaultLanguage="json"
              value={editorValue}
              onChange={handleEditorChange}
              theme="vs-dark"
              options={{
                fontSize: 14,
                fontFamily: "'Courier New', monospace",
                lineNumbers: 'on',
                minimap: { enabled: true },
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                automaticLayout: true,
                formatOnPaste: true,
                formatOnType: true,
                tabSize: 2,
                insertSpaces: true,
                detectIndentation: false,
                renderValidationDecorations: 'on',
                quickSuggestions: true,
                suggestOnTriggerCharacters: true,
                acceptSuggestionOnEnter: 'on',
                snippetSuggestions: 'inline',
                colorDecorators: true,
                bracketPairColorization: {
                  enabled: true
                },
              }}
              loading={
                <div className="flex items-center justify-center h-[600px] bg-tactical-black">
                  <div className="text-tactical-green font-mono">Loading editor...</div>
                </div>
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Editor Guide */}
      <Card className="bg-tactical-black/30 border-tactical-green/20">
        <CardHeader>
          <CardTitle className="text-tactical-green font-mono text-sm uppercase tracking-wider">
            Editor Shortcuts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm font-mono">
            <div>
              <span className="text-tactical-gold">Ctrl/Cmd + S:</span>
              <span className="text-gray-400 ml-2">Save</span>
            </div>
            <div>
              <span className="text-tactical-gold">Ctrl/Cmd + F:</span>
              <span className="text-gray-400 ml-2">Find</span>
            </div>
            <div>
              <span className="text-tactical-gold">Ctrl/Cmd + H:</span>
              <span className="text-gray-400 ml-2">Replace</span>
            </div>
            <div>
              <span className="text-tactical-gold">Alt + Shift + F:</span>
              <span className="text-gray-400 ml-2">Format</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-end gap-4 pt-4 border-t border-tactical-green/20">
        <Button
          variant="outline"
          onClick={handleReset}
          className="border-tactical-green/30 text-tactical-green hover:bg-tactical-green/10 font-mono"
          disabled={isLoading || isValidating}
        >
          <RotateCcw className="w-4 h-4 mr-2" />
          Reset
        </Button>
        <Button
          variant="outline"
          onClick={onCancel}
          className="border-tactical-green/30 text-white hover:bg-tactical-black-light font-mono"
          disabled={isLoading || isValidating}
        >
          Cancel
        </Button>
        <Button
          variant="outline"
          onClick={validateJson}
          className="border-tactical-blue/30 text-tactical-blue hover:bg-tactical-blue/10 font-mono"
          disabled={isLoading || isValidating}
        >
          {isValidating ? 'Validating...' : 'Validate'}
        </Button>
        <Button
          onClick={handleSave}
          className="bg-tactical-green hover:bg-tactical-green-light text-white font-tactical font-semibold"
          disabled={isLoading || isValidating}
        >
          <Save className="w-4 h-4 mr-2" />
          {isLoading ? 'Saving...' : 'Save Configuration'}
        </Button>
      </div>
    </div>
  )
}