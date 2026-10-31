const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() || '';

export const API_BASE_URL = configuredBaseUrl.replace(/\/+$/, '');

export function apiUrl(path) {
  if (/^(?:[a-z]+:)?\/\//i.test(path)) return path;

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  if (!API_BASE_URL || !normalizedPath.startsWith('/api/')) return normalizedPath;

  return `${API_BASE_URL}${normalizedPath}`;
}

export async function apiFetch(path, options) {
  const url = apiUrl(path);
  const response = await fetch(url, options);
  const contentType = response.headers.get('content-type') || '';

  if (!contentType.toLowerCase().includes('json')) {
    const message = API_BASE_URL
      ? `The backend at ${API_BASE_URL} returned a web page instead of API data. Check that VITE_API_BASE_URL points to the backend Render service.`
      : 'The deployed frontend is reaching a web page instead of the backend API. Set VITE_API_BASE_URL to your backend Render service URL, then redeploy the frontend.';
    throw new Error(message);
  }

  return response;
}
