import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.reject(new Error("API unavailable")))
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("renders fallback catalog when the API is offline", async () => {
  render(<App />);

  expect(await screen.findByText("Linen Wrap Blouse")).toBeInTheDocument();
  expect(screen.getByText("Weekend Denim Jacket")).toBeInTheDocument();
});

test("filters the catalog and adds an item to the cart", async () => {
  const user = userEvent.setup();
  render(<App />);

  await screen.findByText("Linen Wrap Blouse");
  await user.selectOptions(screen.getByLabelText("Filter by category"), "Outerwear");

  expect(await screen.findByText("Weekend Denim Jacket")).toBeInTheDocument();
  expect(screen.queryByText("Linen Wrap Blouse")).not.toBeInTheDocument();
  await user.click(screen.getAllByTitle("Add to bag")[0]);

  expect(screen.getByText("1 items")).toBeInTheDocument();
  expect(screen.getAllByText("$98.00").length).toBeGreaterThan(0);
});

test("admin dashboard saves contact info changes", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.includes("/admin/store-profile") && init?.method === "PUT") {
      const body = JSON.parse(String(init.body));
      return jsonResponse({
        id: 1,
        ...body,
        updated_at: "2026-05-05 09:45:00"
      });
    }
    if (url.includes("/store-profile")) {
      return jsonResponse({
        id: 1,
        business_name: "Mom's Clothing Biz",
        tagline: "Small-batch wardrobe staples picked with care.",
        contact_name: "Maria Owner",
        email: "hello@momsclothingbiz.com",
        phone: "(801) 555-0148",
        city: "Salt Lake City",
        state: "UT",
        instagram_url: "https://instagram.com/momsclothingbiz",
        hero_image_url:
          "https://images.unsplash.com/photo-1445205170230-053b83016050?auto=format&fit=crop&w=1800&q=80",
        updated_at: "2026-05-05 09:00:00"
      });
    }
    if (url.includes("/filters")) {
      return jsonResponse({ categories: ["Outerwear"], sizes: ["S", "M", "L"] });
    }
    return jsonResponse([]);
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<App />);

  await user.click(screen.getByRole("button", { name: "Admin dashboard" }));
  await screen.findByLabelText("Business name");
  await user.clear(screen.getByLabelText("Business name"));
  await user.type(screen.getByLabelText("Business name"), "Maria's Closet");
  await user.clear(screen.getByLabelText("Profile phone"));
  await user.type(screen.getByLabelText("Profile phone"), "801-555-0199");
  await user.click(screen.getByRole("button", { name: "Save profile" }));

  expect(await screen.findByText("Saved Maria's Closet")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/admin/store-profile",
    expect.objectContaining({ method: "PUT" })
  );
});

test("admin generates a stock-aware model shot", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.includes("/admin/model-shots") && init?.method === "POST") {
      return jsonResponse({
        id: 1,
        product_id: 5,
        product_name: "Tailored Work Trouser",
        category: "Bottoms",
        source_image_url: "https://example.com/trouser-flatlay.jpg",
        generated_image_url: "https://example.com/trouser-on-model.jpg",
        quality_tier: "premium",
        quality_label: "Premium catalog render",
        generation_mode: "product-to-model-quality",
        stock_quantity: 24,
        status: "ready",
        notes: "High inventory supports spending more generation credits on a campaign-quality image.",
        created_at: "2026-05-05 10:00:00"
      });
    }
    if (url.includes("/admin/model-shots")) {
      return jsonResponse([]);
    }
    if (url.includes("/admin/products/inventory")) {
      return jsonResponse([
        {
          id: 5,
          slug: "tailored-work-trouser",
          name: "Tailored Work Trouser",
          category: "Bottoms",
          image_url: "https://example.com/trouser.jpg",
          price_cents: 7400,
          total_stock: 24,
          quality_profile: {
            quality_tier: "premium",
            quality_label: "Premium catalog render",
            generation_mode: "product-to-model-quality",
            notes: "High inventory supports spending more generation credits on a campaign-quality image."
          }
        }
      ]);
    }
    if (url.includes("/store-profile")) {
      return jsonResponse({
        id: 1,
        business_name: "Mom's Clothing Biz",
        tagline: "Small-batch wardrobe staples picked with care.",
        contact_name: "Maria Owner",
        email: "hello@momsclothingbiz.com",
        phone: "(801) 555-0148",
        city: "Salt Lake City",
        state: "UT",
        instagram_url: "https://instagram.com/momsclothingbiz",
        hero_image_url:
          "https://images.unsplash.com/photo-1445205170230-053b83016050?auto=format&fit=crop&w=1800&q=80",
        updated_at: "2026-05-05 09:00:00"
      });
    }
    if (url.includes("/filters")) {
      return jsonResponse({ categories: ["Bottoms"], sizes: ["S", "M", "L"] });
    }
    return jsonResponse([]);
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<App />);

  await user.click(screen.getByRole("button", { name: "Admin dashboard" }));
  expect(await screen.findByText("Premium catalog render")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Generate model shot" }));

  expect(await screen.findByText("Premium catalog render ready for Tailored Work Trouser")).toBeInTheDocument();
});

function jsonResponse(payload: unknown) {
  return new Response(JSON.stringify(payload), {
    headers: {
      "Content-Type": "application/json"
    },
    status: 200
  });
}
