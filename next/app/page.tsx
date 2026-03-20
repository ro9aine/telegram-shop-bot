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
  item: Product;
};

const API_BASE = process.env.CATALOG_API_BASE_URL ?? "http://djg:8000";

function truncate(text: string, limit: number): string {
  const normalized = text.trim();
  if (normalized.length <= limit) {
    return normalized;
  }
  return `${normalized.slice(0, Math.max(0, limit - 1)).trimEnd()}…`;
}

async function loadCategories(): Promise<Category[]> {
  const response = await fetch(`${API_BASE}/api/catalog/categories/`, {
    cache: "no-store",
  });
  if (!response.ok) {
    return [];
  }
  const payload = (await response.json()) as { categories?: Category[] };
  return payload.categories ?? [];
}

async function loadProducts(categoryId: number | null, page: number): Promise<ProductsPayload> {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", "12");
  if (categoryId !== null) {
    params.set("category_id", String(categoryId));
  }

  const response = await fetch(`${API_BASE}/api/catalog/products/?${params.toString()}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    return { items: [], pagination: { page: 1, total_pages: 1 } };
  }
  return (await response.json()) as ProductsPayload;
}

async function loadProduct(productId: number | null): Promise<Product | null> {
  if (!productId || !Number.isFinite(productId)) {
    return null;
  }
  const response = await fetch(`${API_BASE}/api/catalog/products/${productId}/`, {
    cache: "no-store",
  });
  if (!response.ok) {
    return null;
  }
  const payload = (await response.json()) as ProductDetailPayload;
  return payload.item ?? null;
}

export default async function HomePage({
  searchParams,
}: {
  searchParams?: Promise<{ category?: string; page?: string; product?: string }>;
}) {
  const params = (await searchParams) ?? {};
  const selectedCategoryId = params.category ? Number(params.category) : null;
  const page = params.page ? Math.max(1, Number(params.page)) : 1;
  const selectedProductId = params.product ? Number(params.product) : null;

  const [categories, productsPayload, selectedProduct] = await Promise.all([
    loadCategories(),
    loadProducts(Number.isFinite(selectedCategoryId) ? selectedCategoryId : null, page),
    loadProduct(Number.isFinite(selectedProductId) ? selectedProductId : null),
  ]);

  const currentPage = productsPayload.pagination.page || 1;
  const totalPages = productsPayload.pagination.total_pages || 1;

  return (
    <main className="page">
      <header className="hero">
        <h1>Catalog</h1>
        <p>Shop items are synced from Django API.</p>
      </header>

      <section className="filters">
        <a className={!selectedCategoryId ? "chip chip-active" : "chip"} href="/">
          All
        </a>
        {categories.map((category) => (
          <a
            className={selectedCategoryId === category.id ? "chip chip-active" : "chip"}
            href={`/?category=${category.id}`}
            key={category.id}
          >
            {category.title}
          </a>
        ))}
      </section>

      <section className="grid">
        {selectedProduct ? (
          <article className="card card-selected" key={`selected-${selectedProduct.id}`}>
            {selectedProduct.images[0] ? (
              <img alt={selectedProduct.title} className="card-image" src={selectedProduct.images[0]} />
            ) : null}
            <h2>{selectedProduct.title}</h2>
            {selectedProduct.description ? <p>{truncate(selectedProduct.description, 120)}</p> : null}
            <div className="price">{selectedProduct.price}</div>
            <div className="card-actions">
              <a className="card-link" href={`/product/${selectedProduct.id}`}>
                Open details
              </a>
            </div>
          </article>
        ) : null}
        {productsPayload.items.map((item) => (
          <article className="card" key={item.id}>
            {item.images[0] ? <img alt={item.title} className="card-image" src={item.images[0]} /> : null}
            <h2>{item.title}</h2>
            {item.description ? <p>{truncate(item.description, 120)}</p> : null}
            <div className="price">{item.price}</div>
            <div className="card-actions">
              <a className="card-link" href={`/product/${item.id}`}>
                Open details
              </a>
            </div>
          </article>
        ))}
      </section>

      <nav className="pager">
        {currentPage > 1 ? (
          <a href={`/?${new URLSearchParams({ page: String(currentPage - 1), ...(selectedCategoryId ? { category: String(selectedCategoryId) } : {}) }).toString()}`}>
            Back
          </a>
        ) : (
          <span />
        )}
        <span>
          Page {currentPage}/{totalPages}
        </span>
        {currentPage < totalPages ? (
          <a href={`/?${new URLSearchParams({ page: String(currentPage + 1), ...(selectedCategoryId ? { category: String(selectedCategoryId) } : {}) }).toString()}`}>
            Forward
          </a>
        ) : (
          <span />
        )}
      </nav>
    </main>
  );
}
