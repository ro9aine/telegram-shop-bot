export default function ProductLoadingSkeleton() {
  return (
    <main className="product-page">
      <section className="product-shell">
        <div className="product-main-photo catalog-skeleton-card">
          <div className="catalog-skeleton-image" />
        </div>

        <div className="product-slider" aria-hidden="true">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div className="thumb catalog-skeleton-card" key={`thumb-skeleton-${idx}`} />
          ))}
        </div>

        <div className="product-content">
          <div className="catalog-skeleton-line" style={{ height: 22, width: "78%" }} />
          <div className="catalog-skeleton-line" style={{ height: 28, marginTop: 12, width: "35%" }} />
          <div className="catalog-skeleton-line" style={{ height: 16, marginTop: 14, width: "92%" }} />
          <div className="catalog-skeleton-line" style={{ height: 16, marginTop: 8, width: "88%" }} />
          <div className="catalog-skeleton-line" style={{ height: 16, marginTop: 8, width: "76%" }} />
        </div>
      </section>
    </main>
  );
}
