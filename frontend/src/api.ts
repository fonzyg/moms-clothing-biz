import type {
  CheckoutPayload,
  ModelShot,
  ModelShotPayload,
  OrderReceipt,
  Product,
  ProductFilters,
  ProductInventory,
  StoreProfile,
  StoreProfileUpdatePayload
} from "./types";

const fallbackProducts: Product[] = [
  {
    id: 1,
    slug: "linen-wrap-blouse",
    name: "Linen Wrap Blouse",
    category: "Tops",
    description: "A breathable wrap blouse with a relaxed waist tie and polished drape.",
    price_cents: 6400,
    image_url: "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=900&q=80",
    is_featured: true,
    total_stock: 22,
    available_sizes: ["XS", "S", "M", "L"],
    available_colors: ["Ivory", "Sage"],
    variants: [
      { id: 1, size: "XS", color: "Ivory", stock_quantity: 5 },
      { id: 2, size: "S", color: "Ivory", stock_quantity: 8 },
      { id: 3, size: "M", color: "Sage", stock_quantity: 6 },
      { id: 4, size: "L", color: "Sage", stock_quantity: 3 }
    ]
  },
  {
    id: 2,
    slug: "weekend-denim-jacket",
    name: "Weekend Denim Jacket",
    category: "Outerwear",
    description: "Midweight denim with roomy pockets and an easy vintage-inspired fit.",
    price_cents: 9800,
    image_url: "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=900&q=80",
    is_featured: true,
    total_stock: 19,
    available_sizes: ["S", "M", "L"],
    available_colors: ["Washed Blue", "Dark Indigo"],
    variants: [
      { id: 5, size: "S", color: "Washed Blue", stock_quantity: 6 },
      { id: 6, size: "M", color: "Washed Blue", stock_quantity: 9 },
      { id: 7, size: "L", color: "Dark Indigo", stock_quantity: 4 }
    ]
  },
  {
    id: 3,
    slug: "soft-rib-knit-set",
    name: "Soft Rib Knit Set",
    category: "Sets",
    description: "Coordinated ribbed tank and wide-leg pant set for travel days and errands.",
    price_cents: 11800,
    image_url: "https://images.unsplash.com/photo-1485230895905-ec40ba36b9bc?auto=format&fit=crop&w=900&q=80",
    is_featured: true,
    total_stock: 17,
    available_sizes: ["S", "M", "L", "XL"],
    available_colors: ["Oat", "Charcoal"],
    variants: [
      { id: 8, size: "S", color: "Oat", stock_quantity: 4 },
      { id: 9, size: "M", color: "Oat", stock_quantity: 7 },
      { id: 10, size: "L", color: "Charcoal", stock_quantity: 4 },
      { id: 11, size: "XL", color: "Charcoal", stock_quantity: 2 }
    ]
  },
  {
    id: 4,
    slug: "market-day-midi-dress",
    name: "Market Day Midi Dress",
    category: "Dresses",
    description: "A printed midi dress with a flattering square neckline and side pockets.",
    price_cents: 8600,
    image_url: "https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=900&q=80",
    is_featured: false,
    total_stock: 16,
    available_sizes: ["XS", "S", "M", "L"],
    available_colors: ["Floral Navy", "Floral Clay"],
    variants: [
      { id: 12, size: "XS", color: "Floral Navy", stock_quantity: 3 },
      { id: 13, size: "S", color: "Floral Navy", stock_quantity: 5 },
      { id: 14, size: "M", color: "Floral Clay", stock_quantity: 6 },
      { id: 15, size: "L", color: "Floral Clay", stock_quantity: 2 }
    ]
  },
  {
    id: 5,
    slug: "tailored-work-trouser",
    name: "Tailored Work Trouser",
    category: "Bottoms",
    description: "Stretch suiting trousers with a clean front, tapered leg, and all-day comfort.",
    price_cents: 7400,
    image_url: "https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=900&q=80",
    is_featured: false,
    total_stock: 24,
    available_sizes: ["S", "M", "L", "XL"],
    available_colors: ["Black", "Camel"],
    variants: [
      { id: 16, size: "S", color: "Black", stock_quantity: 8 },
      { id: 17, size: "M", color: "Black", stock_quantity: 8 },
      { id: 18, size: "L", color: "Camel", stock_quantity: 5 },
      { id: 19, size: "XL", color: "Camel", stock_quantity: 3 }
    ]
  },
  {
    id: 6,
    slug: "cozy-longline-cardigan",
    name: "Cozy Longline Cardigan",
    category: "Outerwear",
    description: "A textured knit cardigan made for layering over dresses, tees, and tanks.",
    price_cents: 7800,
    image_url: "https://images.unsplash.com/photo-1520975954732-35dd22299614?auto=format&fit=crop&w=900&q=80",
    is_featured: false,
    total_stock: 18,
    available_sizes: ["S", "M", "L", "XL"],
    available_colors: ["Heather Gray", "Forest"],
    variants: [
      { id: 20, size: "S", color: "Heather Gray", stock_quantity: 6 },
      { id: 21, size: "M", color: "Heather Gray", stock_quantity: 6 },
      { id: 22, size: "L", color: "Forest", stock_quantity: 4 },
      { id: 23, size: "XL", color: "Forest", stock_quantity: 2 }
    ]
  }
];

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const defaultStoreProfile: StoreProfile = {
  id: 1,
  business_name: "Mom's Clothing Biz",
  tagline: "Small-batch wardrobe staples picked with care.",
  contact_name: "Maria Owner",
  email: "hello@momsclothingbiz.com",
  phone: "(801) 555-0148",
  city: "Salt Lake City",
  state: "UT",
  instagram_url: "https://instagram.com/momsclothingbiz",
  hero_image_url: "https://images.unsplash.com/photo-1445205170230-053b83016050?auto=format&fit=crop&w=1800&q=80",
  updated_at: "Not saved yet"
};

export async function fetchProducts(filters: ProductFilters): Promise<Product[]> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });

  try {
    const response = await fetch(`${API_BASE_URL}/products?${params.toString()}`);
    if (!response.ok) {
      throw new Error("Could not load products");
    }
    const products = (await response.json()) as Product[];
    return products.map((product) => ({
      ...product,
      variants: fallbackProducts.find((fallback) => fallback.id === product.id)?.variants ?? product.variants
    }));
  } catch {
    return filterFallbackProducts(filters);
  }
}

export async function fetchFilters(): Promise<{ categories: string[]; sizes: string[] }> {
  try {
    const response = await fetch(`${API_BASE_URL}/filters`);
    if (!response.ok) {
      throw new Error("Could not load filters");
    }
    return (await response.json()) as { categories: string[]; sizes: string[] };
  } catch {
    return {
      categories: [...new Set(fallbackProducts.map((product) => product.category))].sort(),
      sizes: ["XS", "S", "M", "L", "XL"]
    };
  }
}

export async function fetchStoreProfile(): Promise<StoreProfile> {
  try {
    const response = await fetch(`${API_BASE_URL}/store-profile`);
    if (!response.ok) {
      throw new Error("Could not load store profile");
    }
    return (await response.json()) as StoreProfile;
  } catch {
    return defaultStoreProfile;
  }
}

export async function updateStoreProfile(payload: StoreProfileUpdatePayload): Promise<StoreProfile> {
  const response = await fetch(`${API_BASE_URL}/admin/store-profile`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const problem = (await response.json().catch(() => undefined)) as { detail?: string } | undefined;
    throw new Error(problem?.detail ?? "Profile update failed");
  }

  return (await response.json()) as StoreProfile;
}

export async function fetchProductInventory(): Promise<ProductInventory[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/products/inventory`);
    if (!response.ok) {
      throw new Error("Could not load inventory");
    }
    return (await response.json()) as ProductInventory[];
  } catch {
    return fallbackProducts.map((product) => {
      const qualityProfile =
        product.total_stock >= 20
          ? {
              quality_tier: "premium" as const,
              quality_label: "Premium catalog render",
              generation_mode: "product-to-model-quality",
              notes: "High inventory supports spending more generation credits on a campaign-quality image."
            }
          : product.total_stock >= 10
            ? {
                quality_tier: "balanced" as const,
                quality_label: "Balanced listing render",
                generation_mode: "product-to-model-balanced",
                notes: "Moderate inventory gets a polished listing image without using the highest-cost mode."
              }
            : {
                quality_tier: "draft" as const,
                quality_label: "Draft low-stock preview",
                generation_mode: "product-to-model-fast",
                notes: "Low inventory gets a fast preview so expensive generation is reserved for better-stocked items."
              };
      return {
        id: product.id,
        slug: product.slug,
        name: product.name,
        category: product.category,
        image_url: product.image_url,
        price_cents: product.price_cents,
        total_stock: product.total_stock,
        quality_profile: qualityProfile
      };
    });
  }
}

export async function fetchModelShots(): Promise<ModelShot[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/model-shots`);
    if (!response.ok) {
      throw new Error("Could not load model shots");
    }
    return (await response.json()) as ModelShot[];
  } catch {
    return [];
  }
}

export async function createModelShot(payload: ModelShotPayload): Promise<ModelShot> {
  const response = await fetch(`${API_BASE_URL}/admin/model-shots`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const problem = (await response.json().catch(() => undefined)) as { detail?: string } | undefined;
    throw new Error(problem?.detail ?? "Model shot generation failed");
  }

  return (await response.json()) as ModelShot;
}

export function resolveMediaUrl(url: string): string {
  if (!url.startsWith("/uploads")) {
    return url;
  }

  if (API_BASE_URL.startsWith("http")) {
    return new URL(url, API_BASE_URL.replace(/\/api\/?$/, "")).toString();
  }

  return url;
}

export async function submitOrder(payload: CheckoutPayload): Promise<OrderReceipt> {
  const response = await fetch(`${API_BASE_URL}/orders`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const problem = (await response.json().catch(() => undefined)) as { detail?: string } | undefined;
    throw new Error(problem?.detail ?? "Checkout failed");
  }

  return (await response.json()) as OrderReceipt;
}

export function formatMoney(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD"
  }).format(cents / 100);
}

function filterFallbackProducts(filters: ProductFilters): Product[] {
  return fallbackProducts.filter((product) => {
    const matchesCategory = !filters.category || product.category === filters.category;
    const matchesSize = !filters.size || product.available_sizes.includes(filters.size);
    const search = filters.q?.trim().toLowerCase();
    const matchesSearch =
      !search ||
      product.name.toLowerCase().includes(search) ||
      product.description.toLowerCase().includes(search);

    return matchesCategory && matchesSize && matchesSearch;
  });
}
