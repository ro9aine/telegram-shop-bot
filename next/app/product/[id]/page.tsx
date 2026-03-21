"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { browserApi } from "../../../lib/http";
import ProductDetailClient from "./product-detail-client";
import ProductLoadingSkeleton from "./product-loading-skeleton";

type Product = {
  id: number;
  title: string;
  description: string;
  price: string;
  images: string[];
};

type ProductDetailPayload = {
  item: Product | null;
};

export default function ProductPage() {
  const params = useParams<{ id: string }>();
  const productId = Number(params.id);
  const [product, setProduct] = useState<Product | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!Number.isFinite(productId)) {
      setNotFound(true);
      setProduct(null);
      return;
    }

    const controller = new AbortController();
    browserApi
      .get<ProductDetailPayload>(`/catalog/products/${productId}/`, { signal: controller.signal })
      .then((response) => {
        if (response.status < 200 || response.status >= 300 || !response.data.item) {
          setNotFound(true);
          setProduct(null);
          return;
        }
        setNotFound(false);
        setProduct(response.data.item);
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setNotFound(true);
          setProduct(null);
        }
      });

    return () => controller.abort();
  }, [productId]);

  if (!Number.isFinite(productId)) {
    return (
      <main className="page">
        <p>Invalid product id.</p>
      </main>
    );
  }

  if (notFound) {
    return (
      <main className="page">
        <p>Product not found.</p>
      </main>
    );
  }

  if (!product) {
    return <ProductLoadingSkeleton />;
  }

  return <ProductDetailClient product={product} />;
}
