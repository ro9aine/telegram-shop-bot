import type { NextRequest } from "next/server";

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

function normalizeBase(value: string): string {
  return value.replace(/\/+$/, "");
}

function buildTargetUrl(base: string, path: string[], search: string): string {
  const normalizedPath = path.map((segment) => encodeURIComponent(segment)).join("/");
  const withSlash = normalizedPath ? `${normalizedPath}/` : "";
  return `${base}/${withSlash}${search}`;
}

function backendBaseCandidates(): string[] {
  const candidates = [
    process.env.CATALOG_API_BASE_URL,
    process.env.NEXT_PUBLIC_CATALOG_API_BASE_URL,
    "http://djg:8000/api",
    "http://127.0.0.1:8000/api",
    "http://localhost:8000/api",
  ].filter((value): value is string => Boolean(value && value.trim()));

  return Array.from(new Set(candidates.map((value) => normalizeBase(value))));
}

function filterHeaders(headers: Headers): Headers {
  const result = new Headers();
  headers.forEach((value, key) => {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      result.set(key, value);
    }
  });
  return result;
}

async function forward(request: NextRequest, path: string[]): Promise<Response> {
  const method = request.method.toUpperCase();
  const canHaveBody = method !== "GET" && method !== "HEAD";
  const body = canHaveBody ? await request.arrayBuffer() : undefined;
  const headers = filterHeaders(request.headers);

  let lastError: unknown;
  for (const base of backendBaseCandidates()) {
    const targetUrl = buildTargetUrl(base, path, request.nextUrl.search);
    try {
      const upstreamResponse = await fetch(targetUrl, {
        method,
        headers,
        body,
        redirect: "follow",
        cache: "no-store",
      });

      return new Response(upstreamResponse.body, {
        status: upstreamResponse.status,
        statusText: upstreamResponse.statusText,
        headers: filterHeaders(upstreamResponse.headers),
      });
    } catch (error) {
      lastError = error;
    }
  }

  return Response.json(
    {
      error: "Upstream backend is unavailable",
      message: String(lastError),
      tried: backendBaseCandidates(),
    },
    { status: 502 },
  );
}

type RouteContext = {
  params: Promise<{
    path: string[];
  }>;
};

export async function GET(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  return forward(request, path);
}

export async function POST(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  return forward(request, path);
}

export async function PUT(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  return forward(request, path);
}

export async function PATCH(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  return forward(request, path);
}

export async function DELETE(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  return forward(request, path);
}
