'use client'

import * as React from 'react'
import { X } from 'lucide-react'
import { useToast } from './use-toast'
import { cn } from '@/lib/utils'

export function Toaster() {
  const { toasts, dismiss } = useToast()

  return (
    <div className="fixed bottom-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:bottom-4 sm:right-4 sm:flex-col sm:max-w-[420px]">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            'group pointer-events-auto relative flex w-full items-center justify-between gap-4 overflow-hidden rounded-md border p-4 pr-8 shadow-lg transition-all',
            'animate-in slide-in-from-right-full fade-in-0 duration-300',
            'data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none',
            toast.variant === 'destructive'
              ? 'border-red-600/50 bg-red-950/90 text-red-100'
              : 'border-emerald-600/50 bg-slate-900/95 text-gray-100 backdrop-blur-sm'
          )}
        >
          <div className="flex flex-1 flex-col gap-1">
            {toast.title && (
              <div className={cn(
                'text-sm font-semibold uppercase tracking-wide',
                toast.variant === 'destructive' ? 'text-red-200' : 'text-emerald-400'
              )}>
                {toast.title}
              </div>
            )}
            {toast.description && (
              <div className="text-sm opacity-90">
                {toast.description}
              </div>
            )}
          </div>
          <button
            onClick={() => dismiss(toast.id)}
            className={cn(
              'absolute right-2 top-2 rounded-sm opacity-70 transition-opacity hover:opacity-100',
              'focus:outline-none focus:ring-2 focus:ring-offset-2',
              toast.variant === 'destructive' 
                ? 'focus:ring-red-600' 
                : 'focus:ring-emerald-600'
            )}
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </button>
        </div>
      ))}
    </div>
  )
}