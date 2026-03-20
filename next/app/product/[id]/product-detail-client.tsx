"use client";

import { Carousel } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import type { CarouselRef } from "antd/es/carousel";
import Link from "next/link";
import { useRef, useState } from "react";

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
  const carouselRef = useRef<CarouselRef | null>(null);

  return (
    <main className="product-page">
      <section className="product-shell">
        <div className="product-main-photo">
          <Link className="product-back-overlay" href="/">
            <button aria-label="Back to catalog" className="product-back-btn" type="button">
              <ArrowLeftOutlined />
            </button>
          </Link>
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
