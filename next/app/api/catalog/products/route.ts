import { NextRequest, NextResponse } from "next/server";

import { djangoApi } from "../../../../lib/http";

export async function GET(request: NextRequest) {
  try {
    const response = await djangoApi.get("/api/catalog/products/", {
      params: Object.fromEntries(request.nextUrl.searchParams.entries()),
    });
    return NextResponse.json(response.data, { status: response.status });
  } catch {
    return NextResponse.json(
      { items: [], pagination: { page: 1, total_pages: 1 } },
      { status: 200 },
    );
  }
}
