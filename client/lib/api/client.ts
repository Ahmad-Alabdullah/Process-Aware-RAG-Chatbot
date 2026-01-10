/**
 * API Client - Routes all requests through the secure proxy
 * 
 * SECURITY: API key is handled server-side in /api/proxy route
 * and never exposed to the client-side JavaScript bundle.
 */

// Use proxy route for all API calls (API key handled server-side)
const API_BASE_URL = "/api/proxy";

// Export for backwards compatibility - but now points to proxy
export const API_BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions extends RequestInit {
  retries?: number;
  retryDelay?: number;
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchWithRetry(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { retries = 3, retryDelay = 1000, ...fetchOptions } = options;

  // Only retry GET requests
  const shouldRetry = fetchOptions.method === "GET" || !fetchOptions.method;

  for (let attempt = 0; attempt <= (shouldRetry ? retries : 0); attempt++) {
    try {
      const response = await fetch(url, {
        ...fetchOptions,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new ApiError(
          response.status,
          errorData?.detail || `HTTP error ${response.status}`,
          errorData
        );
      }

      return response;
    } catch (error) {
      if (error instanceof ApiError) throw error;

      if (attempt < retries && shouldRetry) {
        await sleep(retryDelay * (attempt + 1));
        continue;
      }
      throw error;
    }
  }

  throw new Error("Unexpected: fetchWithRetry exhausted attempts");
}

export const apiClient = {
  async get<T>(endpoint: string, options?: FetchOptions): Promise<T> {
    const response = await fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    return response.json();
  },

  async post<T>(
    endpoint: string,
    body: unknown,
    options?: FetchOptions
  ): Promise<T> {
    const response = await fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      ...options,
    });
    return response.json();
  },

  async delete<T>(endpoint: string, options?: FetchOptions): Promise<T> {
    const response = await fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    return response.json();
  },
};

export { ApiError, API_BASE_URL };
