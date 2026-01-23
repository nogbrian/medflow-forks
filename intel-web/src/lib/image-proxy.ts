/**
 * Converts Instagram CDN URLs to proxy URLs to bypass CORS restrictions.
 * Instagram CDN sends Cross-Origin-Resource-Policy: same-origin headers
 * which blocks direct image loading in browsers.
 */
export function getProxiedImageUrl(url: string | null | undefined): string | null {
  if (!url) return null;

  // Only proxy Instagram CDN URLs
  if (url.includes('cdninstagram.com') || url.includes('fbcdn.net')) {
    return `/api/image-proxy?url=${encodeURIComponent(url)}`;
  }

  return url;
}
