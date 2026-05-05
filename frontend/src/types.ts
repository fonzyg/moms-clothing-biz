export type Variant = {
  id: number;
  size: string;
  color: string;
  stock_quantity: number;
};

export type Product = {
  id: number;
  slug: string;
  name: string;
  category: string;
  description: string;
  price_cents: number;
  image_url: string;
  is_featured: boolean;
  total_stock: number;
  available_sizes: string[];
  available_colors: string[];
  variants?: Variant[];
};

export type ProductFilters = {
  category?: string;
  size?: string;
  q?: string;
};

export type StoreProfile = {
  id: number;
  business_name: string;
  tagline: string;
  contact_name: string;
  email: string;
  phone: string;
  city: string;
  state: string;
  instagram_url: string;
  hero_image_url: string;
  updated_at: string;
};

export type StoreProfileUpdatePayload = Omit<StoreProfile, "id" | "updated_at"> & {
  hero_image_data_url?: string;
};

export type QualityProfile = {
  quality_tier: "premium" | "balanced" | "draft";
  quality_label: string;
  generation_mode: string;
  notes: string;
};

export type ProductInventory = {
  id: number;
  slug: string;
  name: string;
  category: string;
  image_url: string;
  price_cents: number;
  total_stock: number;
  quality_profile: QualityProfile;
};

export type ModelShot = {
  id: number;
  product_id: number;
  product_name: string;
  category: string;
  source_image_url: string;
  generated_image_url: string;
  quality_tier: string;
  quality_label: string;
  generation_mode: string;
  stock_quantity: number;
  status: string;
  notes: string;
  created_at: string;
};

export type ModelShotPayload = {
  product_id: number;
  source_image_url?: string;
  source_image_data_url?: string;
};

export type CartItem = {
  product: Product;
  variant: Variant;
  quantity: number;
};

export type CheckoutPayload = {
  email: string;
  full_name: string;
  city: string;
  state: string;
  items: Array<{
    variant_id: number;
    quantity: number;
  }>;
};

export type OrderReceipt = {
  order_id: number;
  customer_id: number;
  subtotal_cents: number;
  items: Array<{
    product_name: string;
    size: string;
    color: string;
    quantity: number;
    unit_price_cents: number;
  }>;
};
