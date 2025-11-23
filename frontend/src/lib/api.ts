/**
 * API Configuration
 * 
 * Centralized API URL management for frontend-backend communication.
 * Uses NEXT_PUBLIC_API_URL environment variable in production,
 * falls back to localhost for development.
 * 
 * IMPORTANT: Set NEXT_PUBLIC_API_URL in Vercel environment variables
 * to your Railway backend URL (e.g., https://your-app.up.railway.app)
 */

export const API_BASE_URL = 
  process.env.NEXT_PUBLIC_API_URL || 
  'http://127.0.0.1:8000';

/**
 * Constructs a full API URL from a path
 * @param path - API endpoint path (e.g., '/api/leads' or '/analyze-lead')
 * @returns Full URL to the API endpoint
 */
export function getApiUrl(path: string): string {
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

