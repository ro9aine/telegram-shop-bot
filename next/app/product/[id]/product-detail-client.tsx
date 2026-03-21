"use client";

import { Button, Carousel } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import type { CarouselRef } from "antd/es/carousel";
import { useEffect, useRef, useState } from "react";
import { addToBasket, fetchBasket, updateBasketQuantity } from "../../../lib/basket";

type Product = {
  id: number;
  title: string;
  description: string;
  price: string;
  images: string[];
};

type Props = {
  product: Product;
};

export default function ProductDetailClient({ product }: Props) {
  const images = product.images.length ? product.images : [""];
  const [activeIndex, setActiveIndex] = useState(0);
  const [expanded, setExpanded] = useState(false);
  const [quantityInBasket, setQuantityInBasket] = useState(0);
  const carouselRef = useRef<CarouselRef | null>(null);

  useEffect(() => {
    const syncQuantity = async () => {
      const item = (await fetchBasket()).find((entry) => entry.productId === product.id);
      setQuantityInBasket(item?.quantity ?? 0);
    };
    void syncQuantity();

    const onBasketChanged = (event: Event) => {
      const custom = event as CustomEvent<
        Array<{ productId: number; quantity: number }>
      >;
      if (Array.isArray(custom.detail)) {
        const item = custom.detail.find((entry) => entry.productId === product.id);
        setQuantityInBasket(item?.quantity ?? 0);
        return;
      }
      void syncQuantity();
    };

    window.addEventListener("basket:changed", onBasketChanged);
    return () => window.removeEventListener("basket:changed", onBasketChanged);
  }, [product.id]);

  return (
    <main className="product-page">
      <section className="product-shell">
        <div className="product-main-photo">
          <Button
            aria-label="Back to catalog"
            className="product-back-btn product-back-overlay"
            href="/"
            icon={<ArrowLeftOutlined />}
            shape="circle"
            type="default"
          />
          <Carousel
            beforeChange={(_, next) => setActiveIndex(next)}
            dots={false}
            draggable
            infinite={false}
            ref={carouselRef}
            swipeToSlide
          >
            {images.map((image, idx) => (
              <div className="product-slide" key={`${product.id}-slide-${idx}`}>
                {image ? (
                  <img alt={`${product.title} ${idx + 1}`} src={image} />
                ) : (
                  <div className="product-slide-empty">No photo available</div>
                )}
              </div>
            ))}
          </Carousel>
        </div>

        <div className="product-slider" role="tablist" aria-label="Product photos">
          {images.map((image, idx) => (
            <button
              className={idx === activeIndex ? "thumb thumb-active" : "thumb"}
              key={`${product.id}-${idx}`}
              onClick={() => {
                setActiveIndex(idx);
                carouselRef.current?.goTo(idx);
              }}
              type="button"
            >
              {image ? <img alt={`${product.title} thumbnail ${idx + 1}`} src={image} /> : <span>No photo</span>}
            </button>
          ))}
        </div>

        <div className="product-content">
          <h1>{product.title}</h1>
          <div className="product-price">{product.price}</div>
          <div className="product-actions">
            {quantityInBasket > 0 ? (
              <div className="product-qty-controls">
                <Button
                  onClick={async () => {
                    const items = await updateBasketQuantity(product.id, quantityInBasket - 1);
                    const item = items.find((entry) => entry.productId === product.id);
                    setQuantityInBasket(item?.quantity ?? 0);
                  }}
                  type="default"
                >
                  -
                </Button>
                <span className="product-qty-value">{quantityInBasket}</span>
                <Button
                  onClick={async () => {
                    const items = await updateBasketQuantity(product.id, quantityInBasket + 1);
                    const item = items.find((entry) => entry.productId === product.id);
                    setQuantityInBasket(item?.quantity ?? 0);
                  }}
                  type="default"
                >
                  +
                </Button>
              </div>
            ) : (
              <Button
                onClick={async () => {
                  const items = await addToBasket({
                    productId: product.id,
                    title: product.title,
                    price: product.price,
                    image: product.images[0] ?? null,
                  });
                  const item = items.find((entry) => entry.productId === product.id);
                  setQuantityInBasket(item?.quantity ?? 0);
                }}
                type="primary"
              >
                Add to basket
              </Button>
            )}
          </div>
          {product.description ? (
            <>
              <p className={expanded ? "product-description product-description-expanded" : "product-description"}>
                {product.description}
              </p>
              <button className="product-expand-btn" onClick={() => setExpanded((prev) => !prev)} type="button">
                {expanded ? "Hide description" : "Show full description"}
              </button>
            </>
          ) : null}
        </div>
      </section>
    </main>
  );
}
