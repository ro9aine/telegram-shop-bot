import { NextResponse } from "next/server";

import { djangoApi } from "../../../../lib/http";

export async function GET() {
  try {
    const response = await djangoApi.get("/api/catalog/categories/");
    return NextResponse.json(response.data, { status: response.status });
  } catch {
    return NextResponse.json({ categories: [] }, { status: 200 });
  }
}
