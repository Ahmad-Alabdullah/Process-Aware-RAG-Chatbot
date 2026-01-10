import { NextRequest, NextResponse } from "next/server";

/**
 * Secure API Proxy Route
 * 
 * This route acts as a server-side proxy between the client and the backend API.
 * The API key is stored server-side only and never exposed to the client.
 * 
 * Security Best Practice: API keys should never be in NEXT_PUBLIC_ variables
 * because they would be visible in the client-side JavaScript bundle.
 */

const BACKEND_URL = process.env.BACKEND_URL || "http://api:8080";
const API_KEY = process.env.API_KEY || "";

async function proxyRequest(
  request: NextRequest,
  path: string,
  method: string
): Promise<NextResponse> {
  const url = `${BACKEND_URL}${path}`;
  
  // Build headers - add API key server-side
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  
  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }

  try {
    const fetchOptions: RequestInit = {
      method,
      headers,
    };

    // Add body for POST/PUT/PATCH requests
    if (["POST", "PUT", "PATCH"].includes(method)) {
      const body = await request.text();
      if (body) {
        fetchOptions.body = body;
      }
    }

    const response = await fetch(url, fetchOptions);
    
    // Handle streaming responses (SSE)
    if (response.headers.get("content-type")?.includes("text/event-stream")) {
      return new NextResponse(response.body, {
        status: response.status,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          "Connection": "keep-alive",
        },
      });
    }

    // Handle JSON responses
    const data = await response.json().catch(() => null);
    
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Proxy error:", error);
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 502 }
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const fullPath = "/" + path.join("/");
  const searchParams = request.nextUrl.searchParams.toString();
  const pathWithQuery = searchParams ? `${fullPath}?${searchParams}` : fullPath;
  
  return proxyRequest(request, pathWithQuery, "GET");
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const fullPath = "/" + path.join("/");
  
  return proxyRequest(request, fullPath, "POST");
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const fullPath = "/" + path.join("/");
  
  return proxyRequest(request, fullPath, "PUT");
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const fullPath = "/" + path.join("/");
  
  return proxyRequest(request, fullPath, "DELETE");
}
