import { NextResponse } from "next/server";

import { djangoApi } from "../../../../../lib/http";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  try {
    const response = await djangoApi.get(`/api/catalog/products/${id}/`);
    return NextResponse.json(response.data, { status: response.status });
  } catch {
    return NextResponse.json({ item: null }, { status: 404 });
  }
}
