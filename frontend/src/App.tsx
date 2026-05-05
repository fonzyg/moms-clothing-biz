import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  Minus,
  PackageCheck,
  Plus,
  Search,
  ShoppingBag,
  SlidersHorizontal,
  Trash2,
  X
} from "lucide-react";
import { fetchFilters, fetchProducts, formatMoney, submitOrder } from "./api";
import type { CartItem, CheckoutPayload, OrderReceipt, Product, Variant } from "./types";

type FilterState = {
  category: string;
  size: string;
  q: string;
};

type CheckoutState = {
  full_name: string;
  email: string;
  city: string;
  state: string;
};

const initialFilters: FilterState = {
  category: "",
  size: "",
  q: ""
};

const initialCheckout: CheckoutState = {
  full_name: "",
  email: "",
  city: "",
  state: "UT"
};

export default function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [sizes, setSizes] = useState<string[]>([]);
  const [filters, setFilters] = useState<FilterState>(initialFilters);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [checkout, setCheckout] = useState<CheckoutState>(initialCheckout);
  const [loading, setLoading] = useState(true);
  const [receipt, setReceipt] = useState<OrderReceipt | null>(null);
  const [checkoutError, setCheckoutError] = useState("");

  useEffect(() => {
    fetchFilters().then((payload) => {
      setCategories(payload.categories);
      setSizes(payload.sizes);
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    const timer = window.setTimeout(() => {
      fetchProducts({
        category: filters.category || undefined,
        size: filters.size || undefined,
        q: filters.q || undefined
      })
        .then(setProducts)
        .finally(() => setLoading(false));
    }, 150);

    return () => window.clearTimeout(timer);
  }, [filters]);

  const cartSubtotal = useMemo(
    () => cart.reduce((sum, item) => sum + item.product.price_cents * item.quantity, 0),
    [cart]
  );
  const cartCount = useMemo(() => cart.reduce((sum, item) => sum + item.quantity, 0), [cart]);

  function addToCart(product: Product, variant: Variant) {
    setReceipt(null);
    setCart((current) => {
      const existing = current.find((item) => item.variant.id === variant.id);
      if (existing) {
        return current.map((item) =>
          item.variant.id === variant.id
            ? { ...item, quantity: Math.min(item.quantity + 1, variant.stock_quantity) }
            : item
        );
      }
      return [...current, { product, variant, quantity: 1 }];
    });
  }

  function changeQuantity(variantId: number, delta: number) {
    setCart((current) =>
      current
        .map((item) =>
          item.variant.id === variantId
            ? { ...item, quantity: Math.max(0, Math.min(item.quantity + delta, item.variant.stock_quantity)) }
            : item
        )
        .filter((item) => item.quantity > 0)
    );
  }

  async function handleCheckout(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCheckoutError("");

    const payload: CheckoutPayload = {
      ...checkout,
      items: cart.map((item) => ({
        variant_id: item.variant.id,
        quantity: item.quantity
      }))
    };

    try {
      const order = await submitOrder(payload);
      setReceipt(order);
      setCart([]);
      setCheckout(initialCheckout);
    } catch (error) {
      setCheckoutError(error instanceof Error ? error.message : "Checkout failed");
    }
  }

  return (
    <main>
      <header className="shop-header">
        <div>
          <p className="eyebrow">Small-batch wardrobe staples</p>
          <h1>Mom's Clothing Biz</h1>
          <p className="intro">
            Curated pieces with live inventory, simple checkout, and a Python API behind the counter.
          </p>
        </div>
        <div className="header-actions" aria-label="Cart summary">
          <ShoppingBag aria-hidden="true" />
          <span>{cartCount} items</span>
          <strong>{formatMoney(cartSubtotal)}</strong>
        </div>
      </header>

      <section className="toolbar" aria-label="Store filters">
        <label className="search-field">
          <Search aria-hidden="true" />
          <input
            value={filters.q}
            onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
            placeholder="Search denim, dress, cardigan"
            type="search"
          />
        </label>

        <label>
          <SlidersHorizontal aria-hidden="true" />
          <select
            value={filters.category}
            onChange={(event) => setFilters((current) => ({ ...current, category: event.target.value }))}
            aria-label="Filter by category"
          >
            <option value="">All categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>

        <div className="segmented-control" aria-label="Filter by size">
          <button
            className={!filters.size ? "active" : ""}
            onClick={() => setFilters((current) => ({ ...current, size: "" }))}
            type="button"
          >
            All
          </button>
          {sizes.map((size) => (
            <button
              className={filters.size === size ? "active" : ""}
              key={size}
              onClick={() => setFilters((current) => ({ ...current, size }))}
              type="button"
            >
              {size}
            </button>
          ))}
        </div>
      </section>

      <div className="store-layout">
        <section className="product-section" aria-live="polite">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Available now</p>
              <h2>{products.length} pieces in stock</h2>
            </div>
            {(filters.category || filters.size || filters.q) && (
              <button className="ghost-button" onClick={() => setFilters(initialFilters)} type="button">
                <X aria-hidden="true" />
                Clear
              </button>
            )}
          </div>

          {loading ? (
            <div className="loading-grid" aria-label="Loading products">
              {Array.from({ length: 6 }).map((_, index) => (
                <div className="skeleton-card" key={index} />
              ))}
            </div>
          ) : (
            <div className="product-grid">
              {products.map((product) => (
                <ProductCard key={product.id} onAdd={addToCart} product={product} />
              ))}
            </div>
          )}
        </section>

        <aside className="cart-panel" aria-label="Shopping cart">
          <div className="cart-panel-header">
            <div>
              <p className="eyebrow">Checkout</p>
              <h2>Shopping Bag</h2>
            </div>
            <PackageCheck aria-hidden="true" />
          </div>

          {cart.length === 0 ? (
            <div className="empty-cart">
              {receipt ? (
                <>
                  <CheckCircle2 aria-hidden="true" />
                  <p>Order #{receipt.order_id} placed for {formatMoney(receipt.subtotal_cents)}.</p>
                </>
              ) : (
                <p>Your bag is ready for something good.</p>
              )}
            </div>
          ) : (
            <div className="cart-items">
              {cart.map((item) => (
                <div className="cart-item" key={item.variant.id}>
                  <img alt="" src={item.product.image_url} />
                  <div>
                    <strong>{item.product.name}</strong>
                    <span>
                      {item.variant.size} / {item.variant.color}
                    </span>
                    <span>{formatMoney(item.product.price_cents)}</span>
                  </div>
                  <div className="quantity-controls">
                    <button
                      aria-label={`Decrease ${item.product.name}`}
                      onClick={() => changeQuantity(item.variant.id, -1)}
                      title="Decrease"
                      type="button"
                    >
                      <Minus aria-hidden="true" />
                    </button>
                    <span>{item.quantity}</span>
                    <button
                      aria-label={`Increase ${item.product.name}`}
                      onClick={() => changeQuantity(item.variant.id, 1)}
                      title="Increase"
                      type="button"
                    >
                      <Plus aria-hidden="true" />
                    </button>
                    <button
                      aria-label={`Remove ${item.product.name}`}
                      onClick={() => changeQuantity(item.variant.id, -item.quantity)}
                      title="Remove"
                      type="button"
                    >
                      <Trash2 aria-hidden="true" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="cart-total">
            <span>Subtotal</span>
            <strong>{formatMoney(cartSubtotal)}</strong>
          </div>

          <form className="checkout-form" onSubmit={handleCheckout}>
            <input
              aria-label="Full name"
              disabled={cart.length === 0}
              onChange={(event) => setCheckout((current) => ({ ...current, full_name: event.target.value }))}
              placeholder="Full name"
              required
              value={checkout.full_name}
            />
            <input
              aria-label="Email"
              disabled={cart.length === 0}
              onChange={(event) => setCheckout((current) => ({ ...current, email: event.target.value }))}
              placeholder="Email"
              required
              type="email"
              value={checkout.email}
            />
            <div className="form-row">
              <input
                aria-label="City"
                disabled={cart.length === 0}
                onChange={(event) => setCheckout((current) => ({ ...current, city: event.target.value }))}
                placeholder="City"
                required
                value={checkout.city}
              />
              <input
                aria-label="State"
                disabled={cart.length === 0}
                maxLength={2}
                onChange={(event) => setCheckout((current) => ({ ...current, state: event.target.value }))}
                placeholder="UT"
                required
                value={checkout.state}
              />
            </div>
            {checkoutError && <p className="form-error">{checkoutError}</p>}
            <button className="checkout-button" disabled={cart.length === 0} type="submit">
              <ShoppingBag aria-hidden="true" />
              Place order
            </button>
          </form>
        </aside>
      </div>
    </main>
  );
}

function ProductCard({ product, onAdd }: { product: Product; onAdd: (product: Product, variant: Variant) => void }) {
  const [selectedVariantId, setSelectedVariantId] = useState<number>(product.variants?.[0]?.id ?? 0);
  const variants = product.variants ?? [];
  const selectedVariant = variants.find((variant) => variant.id === selectedVariantId) ?? variants[0];

  useEffect(() => {
    setSelectedVariantId(product.variants?.[0]?.id ?? 0);
  }, [product]);

  return (
    <article className={product.is_featured ? "product-card featured" : "product-card"}>
      <div className="product-image">
        <img alt={product.name} src={product.image_url} />
        {product.is_featured && <span>Featured</span>}
      </div>
      <div className="product-body">
        <div className="product-title-row">
          <div>
            <p>{product.category}</p>
            <h3>{product.name}</h3>
          </div>
          <strong>{formatMoney(product.price_cents)}</strong>
        </div>
        <p className="description">{product.description}</p>
        <div className="swatches" aria-label={`${product.name} colors`}>
          {product.available_colors.map((color) => (
            <span key={color}>{color}</span>
          ))}
        </div>
        <div className="variant-row">
          <select
            aria-label={`Choose ${product.name} variant`}
            onChange={(event) => setSelectedVariantId(Number(event.target.value))}
            value={selectedVariant?.id ?? ""}
          >
            {variants.map((variant) => (
              <option key={variant.id} value={variant.id}>
                {variant.size} / {variant.color}
              </option>
            ))}
          </select>
          <button
            disabled={!selectedVariant}
            onClick={() => selectedVariant && onAdd(product, selectedVariant)}
            title="Add to bag"
            type="button"
          >
            <Plus aria-hidden="true" />
            Add
          </button>
        </div>
      </div>
    </article>
  );
}
