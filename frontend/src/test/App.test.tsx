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
