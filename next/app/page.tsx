"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Skeleton } from "antd";

import { browserApi } from "../lib/http";

type Category = {
  id: number;
  title: string;
  parent_id: number | null;
};

type Product = {
  id: number;
  title: string;
  description: string;
  price: string;
  images: string[];
};

type ProductsPayload = {
  items: Product[];
  pagination: {
    page: number;
    total_pages: number;
  };
};

type ProductDetailPayload = {
  item: Product | null;
};

function truncate(text: string, limit: number): string {
  const normalized = text.trim();
  if (normalized.length <= limit) {
    return normalized;
  }
  return `${normalized.slice(0, Math.max(0, limit - 1)).trimEnd()}…`;
}

function buildCatalogHref(page: number, categoryId: number | null): string {
  const params = new URLSearchParams();
  if (page > 1) {
    params.set("page", String(page));
  }
  if (categoryId !== null) {
    params.set("category", String(categoryId));
  }
  const query = params.toString();
  return query ? `/?${query}` : "/";
}

export default function HomePage() {
  const searchParams = useSearchParams();
  const selectedCategoryIdRaw = searchParams.get("category");
  const pageRaw = searchParams.get("page");
  const selectedProductIdRaw = searchParams.get("product");

  const selectedCategoryId = selectedCategoryIdRaw ? Number(selectedCategoryIdRaw) : null;
  const page = pageRaw ? Math.max(1, Number(pageRaw)) : 1;
  const selectedProductId = selectedProductIdRaw ? Number(selectedProductIdRaw) : null;

  const [categories, setCategories] = useState<Category[]>([]);
  const [productsPayload, setProductsPayload] = useState<ProductsPayload>({
    items: [],
    pagination: { page: 1, total_pages: 1 },
  });
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isCatalogLoading, setIsCatalogLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    setIsCatalogLoading(true);
    const params = new URLSearchParams();
    params.set("page", String(Number.isFinite(page) ? page : 1));
    params.set("page_size", "12");
    if (selectedCategoryId !== null && Number.isFinite(selectedCategoryId)) {
      params.set("category_id", String(selectedCategoryId));
    }

    const productIdForQuery =
      selectedProductId !== null && Number.isFinite(selectedProductId) ? selectedProductId : null;

    Promise.all([
      browserApi.get<{ categories?: Category[] }>("/catalog/categories/", { signal: controller.signal }),
      browserApi.get<ProductsPayload>(`/catalog/products/?${params.toString()}`, { signal: controller.signal }),
      productIdForQuery
        ? browserApi.get<ProductDetailPayload>(`/catalog/products/${productIdForQuery}/`, { signal: controller.signal })
        : Promise.resolve(null),
    ])
      .then(([categoriesResponse, productsResponse, productResponse]) => {
        if (categoriesResponse.status >= 200 && categoriesResponse.status < 300) {
          setCategories(categoriesResponse.data.categories ?? []);
        } else {
          setCategories([]);
        }

        if (productsResponse.status >= 200 && productsResponse.status < 300) {
          setProductsPayload(productsResponse.data);
        } else {
          setProductsPayload({ items: [], pagination: { page: 1, total_pages: 1 } });
        }

        if (productResponse && productResponse.status >= 200 && productResponse.status < 300) {
          setSelectedProduct(productResponse.data.item ?? null);
        } else {
          setSelectedProduct(null);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setCategories([]);
          setProductsPayload({ items: [], pagination: { page: 1, total_pages: 1 } });
          setSelectedProduct(null);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsCatalogLoading(false);
        }
      });

    return () => controller.abort();
  }, [page, selectedCategoryId, selectedProductId]);

  const currentPage = productsPayload.pagination.page || 1;
  const totalPages = productsPayload.pagination.total_pages || 1;

  return (
    <main className="page">
      <header className="hero">
        <h1>Catalog</h1>
        <p>Shop items are synced from Django API.</p>
      </header>

      <section className="filters">
        <Link className={!selectedCategoryId ? "chip chip-active" : "chip"} href="/">
          All
        </Link>
        {categories.map((category) => (
          <Link
            className={selectedCategoryId === category.id ? "chip chip-active" : "chip"}
            href={`/?category=${category.id}`}
            key={category.id}
          >
            {category.title}
          </Link>
        ))}
      </section>

      <section className="grid">
        {isCatalogLoading
          ? Array.from({ length: 6 }).map((_, idx) => (
              <article className="card" key={`skeleton-${idx}`}>
                <Skeleton.Image active style={{ width: "100%", height: "auto", aspectRatio: "16 / 10" }} />
                <div style={{ padding: "12px" }}>
                  <Skeleton active paragraph={{ rows: 1 }} title={false} />
                </div>
              </article>
            ))
          : null}
        {!isCatalogLoading && selectedProduct ? (
          <Link
            className="card card-selected card-clickable"
            href={`/product/${selectedProduct.id}`}
            key={`selected-${selectedProduct.id}`}
          >
            {selectedProduct.images[0] ? (
              <img alt={selectedProduct.title} className="card-image" src={selectedProduct.images[0]} />
            ) : null}
            <h2>{selectedProduct.title}</h2>
            <div className="price">{selectedProduct.price}</div>
          </Link>
        ) : null}
        {!isCatalogLoading &&
          productsPayload.items.map((item) => (
            <Link className="card card-clickable" href={`/product/${item.id}`} key={item.id}>
              {item.images[0] ? <img alt={item.title} className="card-image" src={item.images[0]} /> : null}
              <h2 title={item.title}>{truncate(item.title, 90)}</h2>
              <div className="price">{item.price}</div>
            </Link>
          ))}
      </section>

      <nav className="pager">
        {currentPage > 1 ? (
          <Link
            href={buildCatalogHref(
              currentPage - 1,
              Number.isFinite(selectedCategoryId ?? Number.NaN) ? selectedCategoryId : null,
            )}
          >
            Back
          </Link>
        ) : (
          <span />
        )}
        <span>
          Page {currentPage}/{totalPages}
        </span>
        {currentPage < totalPages ? (
          <Link
            href={buildCatalogHref(
              currentPage + 1,
              Number.isFinite(selectedCategoryId ?? Number.NaN) ? selectedCategoryId : null,
            )}
          >
            Forward
          </Link>
        ) : (
          <span />
        )}
      </nav>
    </main>
  );
}
