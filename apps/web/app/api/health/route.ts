import { NextResponse } from 'next/server'

/**
 * Health Check API Route
 * Used by Docker health checks and monitoring systems
 * GET /api/health
 */
export async function GET() {
  try {
    return NextResponse.json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      service: 'transform-army-web',
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
    })
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        timestamp: new Date().toISOString(),
        error: 'Health check failed',
      },
      { status: 500 }
    )
  }
}