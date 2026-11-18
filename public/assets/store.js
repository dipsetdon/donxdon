"use strict";

const catalogUrl = document.querySelector('meta[name="dxd-catalog"]').content;
const listings = document.querySelector("#listings");
const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function render(products) {
  if (!products.length) return;
  const grid = element("div", "", "product-grid");
  for (const product of products) {
    const card = element("article", "", "product-card");
    if (product.image && /^media\/[A-Za-z0-9][A-Za-z0-9._-]*\.(?:jpe?g|png|webp)$/i.test(product.image)) {
      const image = element("img");
      image.src = product.image;
      image.alt = product.name;
      image.loading = "lazy";
      image.decoding = "async";
      image.width = 480;
      image.height = 600;
      card.append(image);
    }
    const copy = element("div", "", "product-copy");
    const meta = element("div", "", "product-meta");
    meta.append(element("span", product.category), element("span", currency.format(product.price_cents / 100)));
    copy.append(meta, element("h3", product.name));
    if (product.description) copy.append(element("p", product.description));
    card.append(copy);
    grid.append(card);
  }
  listings.replaceChildren(grid);
}

async function load() {
  listings.setAttribute("aria-busy", "true");
  try {
    const response = await fetch(catalogUrl, { cache: "no-cache", credentials: "omit" });
    if (!response.ok) throw new Error("Catalog unavailable");
    const data = await response.json();
    if (!Array.isArray(data)) throw new Error("Invalid catalog");
    render(data);
  } catch {
    const heading = listings.querySelector(".catalog-note h3");
    const copy = listings.querySelector(".catalog-note p");
    if (heading && copy) {
      heading.textContent = "The collection is temporarily unavailable.";
      copy.textContent = "Check back in a bit.";
    }
  } finally {
    listings.setAttribute("aria-busy", "false");
  }
}

if (catalogUrl) load();
