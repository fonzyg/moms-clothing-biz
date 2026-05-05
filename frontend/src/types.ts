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
