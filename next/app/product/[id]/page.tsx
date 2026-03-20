type Product = {
  id: number;
  title: string;
  description: string;
  price: string;
  images: string[];
};

type ProductDetailPayload = {
  item: Product;
};

const API_BASE = process.env.CATALOG_API_BASE_URL ?? "http://djg:8000";

async function loadProduct(id: number): Promise<Product | null> {
  const response = await fetch(`${API_BASE}/api/catalog/products/${id}/`, {
    cache: "no-store",
  });
  if (!response.ok) {
    return null;
  }
  const payload = (await response.json()) as ProductDetailPayload;
  return payload.item ?? null;
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const productId = Number(id);
  if (!Number.isFinite(productId)) {
    return (
      <main className="page">
        <p>Invalid product id.</p>
        <a href="/">Back to catalog</a>
      </main>
    );
  }

  const product = await loadProduct(productId);
  if (!product) {
    return (
      <main className="page">
        <p>Product not found.</p>
        <a href="/">Back to catalog</a>
      </main>
    );
  }

  return (
    <main className="page">
      <a href="/">Back to catalog</a>
      <article className="card card-selected" style={{ marginTop: 12 }}>
        {product.images[0] ? <img alt={product.title} className="card-image" src={product.images[0]} /> : null}
        <h1 style={{ margin: "12px 12px 0", fontSize: 28 }}>{product.title}</h1>
        {product.description ? <p style={{ marginBottom: 0, WebkitLineClamp: "unset" }}>{product.description}</p> : null}
        <div className="price">{product.price}</div>
      </article>

      {product.images.length > 1 ? (
        <section className="grid" style={{ marginTop: 14 }}>
          {product.images.slice(1).map((image, idx) => (
            <article className="card" key={`${product.id}-${idx}`}>
              <img alt={`${product.title} ${idx + 2}`} className="card-image" src={image} />
            </article>
          ))}
        </section>
      ) : null}
    </main>
  );
}
