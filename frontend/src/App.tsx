import { ChangeEvent, CSSProperties, FormEvent, useEffect, useMemo, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import {
  Camera,
  CheckCircle2,
  Mail,
  MapPin,
  Minus,
  PackageCheck,
  Phone,
  Plus,
  Save,
  Search,
  Settings,
  ShoppingBag,
  SlidersHorizontal,
  Store,
  Trash2,
  WandSparkles,
  X
} from "lucide-react";
import {
  createModelShot,
  defaultStoreProfile,
  fetchFilters,
  fetchModelShots,
  fetchProductInventory,
  fetchProducts,
  fetchStoreProfile,
  formatMoney,
  resolveMediaUrl,
  submitOrder,
  updateStoreProfile
} from "./api";
import type {
  CartItem,
  CheckoutPayload,
  ModelShot,
  OrderReceipt,
  Product,
  ProductInventory,
  StoreProfile,
  StoreProfileUpdatePayload,
  Variant
} from "./types";

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

type ActiveView = "shop" | "admin";

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
  const [activeView, setActiveView] = useState<ActiveView>("shop");
  const [profile, setProfile] = useState<StoreProfile>(defaultStoreProfile);
  const [profileForm, setProfileForm] = useState<StoreProfileUpdatePayload>(
    toProfilePayload(defaultStoreProfile)
  );
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
    fetchStoreProfile().then((payload) => {
      setProfile(payload);
      setProfileForm(toProfilePayload(payload));
    });
  }, []);

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
  const heroStyle: CSSProperties = {
    backgroundImage: `linear-gradient(90deg, rgba(248, 250, 247, 0.94), rgba(248, 250, 247, 0.72)), url("${resolveMediaUrl(
      profile.hero_image_url
    )}")`
  };

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
      <nav className="view-tabs" aria-label="Demo views">
        <button className={activeView === "shop" ? "active" : ""} onClick={() => setActiveView("shop")} type="button">
          <Store aria-hidden="true" />
          Storefront
        </button>
        <button
          className={activeView === "admin" ? "active" : ""}
          onClick={() => setActiveView("admin")}
          type="button"
        >
          <Settings aria-hidden="true" />
          Admin dashboard
        </button>
      </nav>

      <header className="shop-header" style={heroStyle}>
        <div>
          <p className="eyebrow">{profile.city}, {profile.state}</p>
          <h1>{profile.business_name}</h1>
          <p className="intro">{profile.tagline}</p>
        </div>
        <div className="header-actions" aria-label="Cart summary">
          <ShoppingBag aria-hidden="true" />
          <span>{cartCount} items</span>
          <strong>{formatMoney(cartSubtotal)}</strong>
        </div>
      </header>

      {activeView === "shop" ? (
        <>
          <ContactStrip profile={profile} />
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
        </>
      ) : (
        <AdminDashboard
          form={profileForm}
          profile={profile}
          setForm={setProfileForm}
          onSaved={(savedProfile) => {
            setProfile(savedProfile);
            setProfileForm(toProfilePayload(savedProfile));
          }}
        />
      )}
    </main>
  );
}

function ContactStrip({ profile }: { profile: StoreProfile }) {
  return (
    <section className="contact-strip" aria-label="Store contact information">
      <a href={`tel:${profile.phone}`}>
        <Phone aria-hidden="true" />
        {profile.phone}
      </a>
      <a href={`mailto:${profile.email}`}>
        <Mail aria-hidden="true" />
        {profile.email}
      </a>
      <span>
        <MapPin aria-hidden="true" />
        {profile.city}, {profile.state}
      </span>
    </section>
  );
}

function AdminDashboard({
  form,
  profile,
  setForm,
  onSaved
}: {
  form: StoreProfileUpdatePayload;
  profile: StoreProfile;
  setForm: Dispatch<SetStateAction<StoreProfileUpdatePayload>>;
  onSaved: (profile: StoreProfile) => void;
}) {
  const [imageDataUrl, setImageDataUrl] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const previewUrl = imageDataUrl ?? resolveMediaUrl(form.hero_image_url);

  function updateField(field: keyof StoreProfileUpdatePayload, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setMessage("");
    setError("");
  }

  async function handleImageChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setError("Choose a JPG, PNG, or WebP image.");
      return;
    }
    if (file.size > 3_000_000) {
      setError("Choose an image smaller than 3 MB.");
      return;
    }

    setError("");
    setImageDataUrl(await readFileAsDataUrl(file));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    try {
      const savedProfile = await updateStoreProfile({
        ...form,
        hero_image_data_url: imageDataUrl ?? undefined
      });
      onSaved(savedProfile);
      setImageDataUrl(null);
      setMessage(`Saved ${savedProfile.business_name}`);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Profile update failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="admin-dashboard" aria-label="Admin dashboard">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Admin demo</p>
          <h2>Store Profile</h2>
        </div>
        <span className="updated-at">Updated {profile.updated_at}</span>
      </div>

      <ModelShotPanel />

      <div className="admin-layout">
        <form className="admin-form" onSubmit={handleSubmit}>
          <label>
            Business name
            <input
              aria-label="Business name"
              onChange={(event) => updateField("business_name", event.target.value)}
              required
              value={form.business_name}
            />
          </label>
          <label>
            Tagline
            <textarea
              aria-label="Tagline"
              onChange={(event) => updateField("tagline", event.target.value)}
              required
              rows={3}
              value={form.tagline}
            />
          </label>
          <label>
            Contact name
            <input
              aria-label="Contact name"
              onChange={(event) => updateField("contact_name", event.target.value)}
              required
              value={form.contact_name}
            />
          </label>
          <div className="admin-form-row">
            <label>
              Email
              <input
                aria-label="Profile email"
                onChange={(event) => updateField("email", event.target.value)}
                required
                type="email"
                value={form.email}
              />
            </label>
            <label>
              Phone
              <input
                aria-label="Profile phone"
                onChange={(event) => updateField("phone", event.target.value)}
                required
                value={form.phone}
              />
            </label>
          </div>
          <div className="admin-form-row">
            <label>
              City
              <input
                aria-label="Profile city"
                onChange={(event) => updateField("city", event.target.value)}
                required
                value={form.city}
              />
            </label>
            <label>
              State
              <input
                aria-label="Profile state"
                onChange={(event) => updateField("state", event.target.value)}
                required
                value={form.state}
              />
            </label>
          </div>
          <label>
            Instagram
            <input
              aria-label="Instagram"
              onChange={(event) => updateField("instagram_url", event.target.value)}
              required
              type="url"
              value={form.instagram_url}
            />
          </label>
          <label>
            Photo URL
            <input
              aria-label="Photo URL"
              onChange={(event) => updateField("hero_image_url", event.target.value)}
              required
              value={form.hero_image_url}
            />
          </label>
          <label className="file-picker">
            <Camera aria-hidden="true" />
            Upload picture
            <input accept="image/jpeg,image/png,image/webp" aria-label="Upload picture" onChange={handleImageChange} type="file" />
          </label>

          {error && <p className="form-error">{error}</p>}
          {message && <p className="form-success">{message}</p>}

          <button className="checkout-button" disabled={saving} type="submit">
            <Save aria-hidden="true" />
            {saving ? "Saving" : "Save profile"}
          </button>
        </form>

        <aside className="profile-preview" aria-label="Store profile preview">
          <img alt={form.business_name} src={previewUrl} />
          <div>
            <p className="eyebrow">Live preview</p>
            <h3>{form.business_name}</h3>
            <p>{form.tagline}</p>
            <span>{form.contact_name}</span>
            <span>{form.phone}</span>
            <span>{form.email}</span>
          </div>
        </aside>
      </div>
    </section>
  );
}

function ModelShotPanel() {
  const [inventory, setInventory] = useState<ProductInventory[]>([]);
  const [shots, setShots] = useState<ModelShot[]>([]);
  const [productId, setProductId] = useState(0);
  const [sourceImageUrl, setSourceImageUrl] = useState("");
  const [sourceImageDataUrl, setSourceImageDataUrl] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchProductInventory().then((items) => {
      setInventory(items);
      setProductId((current) => current || items[0]?.id || 0);
    });
    fetchModelShots().then(setShots);
  }, []);

  const selectedProduct = inventory.find((item) => item.id === productId);
  const qualityProfile = selectedProduct?.quality_profile;
  const sourcePreview = sourceImageDataUrl ?? (sourceImageUrl || selectedProduct?.image_url || "");

  async function handleShotImageChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setError("Choose a JPG, PNG, or WebP image.");
      return;
    }
    if (file.size > 3_000_000) {
      setError("Choose an image smaller than 3 MB.");
      return;
    }

    setError("");
    setMessage("");
    setSourceImageDataUrl(await readFileAsDataUrl(file));
  }

  async function handleGenerateShot(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProduct) {
      setError("Choose a product first.");
      return;
    }

    setGenerating(true);
    setError("");
    setMessage("");

    try {
      const generatedShot = await createModelShot({
        product_id: selectedProduct.id,
        source_image_url: sourceImageUrl || selectedProduct.image_url,
        source_image_data_url: sourceImageDataUrl ?? undefined
      });
      setShots((current) => [generatedShot, ...current]);
      setSourceImageDataUrl(null);
      setSourceImageUrl("");
      setMessage(`${generatedShot.quality_label} ready for ${generatedShot.product_name}`);
    } catch (shotError) {
      setError(shotError instanceof Error ? shotError.message : "Model shot generation failed");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <section className="model-shot-panel" aria-label="AI model shot generator">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Stock-aware AI</p>
          <h2>Model Shots</h2>
        </div>
        {qualityProfile && <span className={`quality-badge ${qualityProfile.quality_tier}`}>{qualityProfile.quality_label}</span>}
      </div>

      <div className="model-shot-grid">
        <form className="admin-form model-shot-form" onSubmit={handleGenerateShot}>
          <label>
            Product
            <select
              aria-label="Product for model shot"
              onChange={(event) => setProductId(Number(event.target.value))}
              required
              value={productId}
            >
              {inventory.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} - {item.total_stock} in stock
                </option>
              ))}
            </select>
          </label>

          <div className="stock-card">
            <span>Stock</span>
            <strong>{selectedProduct?.total_stock ?? 0}</strong>
            <span>Mode</span>
            <strong>{qualityProfile?.generation_mode ?? "pending"}</strong>
          </div>

          <label>
            Clothing photo URL
            <input
              aria-label="Clothing photo URL"
              onChange={(event) => {
                setSourceImageUrl(event.target.value);
                setSourceImageDataUrl(null);
                setMessage("");
                setError("");
              }}
              placeholder={selectedProduct?.image_url}
              value={sourceImageUrl}
            />
          </label>

          <label className="file-picker">
            <Camera aria-hidden="true" />
            Upload clothing photo
            <input
              accept="image/jpeg,image/png,image/webp"
              aria-label="Upload clothing photo"
              onChange={handleShotImageChange}
              type="file"
            />
          </label>

          {qualityProfile && <p className="quality-notes">{qualityProfile.notes}</p>}
          {error && <p className="form-error">{error}</p>}
          {message && <p className="form-success">{message}</p>}

          <button className="checkout-button" disabled={generating || !selectedProduct} type="submit">
            <WandSparkles aria-hidden="true" />
            {generating ? "Generating" : "Generate model shot"}
          </button>
        </form>

        <div className="model-shot-preview" aria-label="Model shot preview">
          <div>
            <p className="eyebrow">Source</p>
            {sourcePreview ? <img alt="Source clothing" src={resolveMediaUrl(sourcePreview)} /> : <div className="blank-preview" />}
          </div>
          <div>
            <p className="eyebrow">Generated</p>
            {shots[0] ? (
              <img alt={shots[0].product_name} src={resolveMediaUrl(shots[0].generated_image_url)} />
            ) : selectedProduct ? (
              <img alt={selectedProduct.name} src={resolveMediaUrl(selectedProduct.image_url)} />
            ) : (
              <div className="blank-preview" />
            )}
          </div>
        </div>
      </div>

      {shots.length > 0 && (
        <div className="model-shot-history" aria-label="Generated model shots">
          {shots.slice(0, 4).map((shot) => (
            <article key={shot.id}>
              <img alt={shot.product_name} src={resolveMediaUrl(shot.generated_image_url)} />
              <div>
                <strong>{shot.product_name}</strong>
                <span>{shot.stock_quantity} in stock</span>
                <span>{shot.quality_label}</span>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
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

function toProfilePayload(profile: StoreProfile): StoreProfileUpdatePayload {
  return {
    business_name: profile.business_name,
    tagline: profile.tagline,
    contact_name: profile.contact_name,
    email: profile.email,
    phone: profile.phone,
    city: profile.city,
    state: profile.state,
    instagram_url: profile.instagram_url,
    hero_image_url: profile.hero_image_url
  };
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("Could not read image file"));
    reader.readAsDataURL(file);
  });
}
