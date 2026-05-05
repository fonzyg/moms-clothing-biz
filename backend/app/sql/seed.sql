INSERT OR IGNORE INTO products
    (slug, name, category, description, price_cents, image_url, is_featured)
VALUES
    (
        'linen-wrap-blouse',
        'Linen Wrap Blouse',
        'Tops',
        'A breathable wrap blouse with a relaxed waist tie and polished drape.',
        6400,
        'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=900&q=80',
        1
    ),
    (
        'weekend-denim-jacket',
        'Weekend Denim Jacket',
        'Outerwear',
        'Midweight denim with roomy pockets and an easy vintage-inspired fit.',
        9800,
        'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=900&q=80',
        1
    ),
    (
        'soft-rib-knit-set',
        'Soft Rib Knit Set',
        'Sets',
        'Coordinated ribbed tank and wide-leg pant set for travel days and errands.',
        11800,
        'https://images.unsplash.com/photo-1485230895905-ec40ba36b9bc?auto=format&fit=crop&w=900&q=80',
        1
    ),
    (
        'market-day-midi-dress',
        'Market Day Midi Dress',
        'Dresses',
        'A printed midi dress with a flattering square neckline and side pockets.',
        8600,
        'https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=900&q=80',
        0
    ),
    (
        'tailored-work-trouser',
        'Tailored Work Trouser',
        'Bottoms',
        'Stretch suiting trousers with a clean front, tapered leg, and all-day comfort.',
        7400,
        'https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=900&q=80',
        0
    ),
    (
        'cozy-longline-cardigan',
        'Cozy Longline Cardigan',
        'Outerwear',
        'A textured knit cardigan made for layering over dresses, tees, and tanks.',
        7800,
        'https://images.unsplash.com/photo-1520975954732-35dd22299614?auto=format&fit=crop&w=900&q=80',
        0
    );

INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'XS', 'Ivory', 5 FROM products WHERE slug = 'linen-wrap-blouse';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'S', 'Ivory', 8 FROM products WHERE slug = 'linen-wrap-blouse';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'M', 'Sage', 6 FROM products WHERE slug = 'linen-wrap-blouse';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'L', 'Sage', 3 FROM products WHERE slug = 'linen-wrap-blouse';

INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'S', 'Washed Blue', 6 FROM products WHERE slug = 'weekend-denim-jacket';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'M', 'Washed Blue', 9 FROM products WHERE slug = 'weekend-denim-jacket';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'L', 'Dark Indigo', 4 FROM products WHERE slug = 'weekend-denim-jacket';

INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'S', 'Oat', 4 FROM products WHERE slug = 'soft-rib-knit-set';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'M', 'Oat', 7 FROM products WHERE slug = 'soft-rib-knit-set';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'L', 'Charcoal', 4 FROM products WHERE slug = 'soft-rib-knit-set';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'XL', 'Charcoal', 2 FROM products WHERE slug = 'soft-rib-knit-set';

INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'XS', 'Floral Navy', 3 FROM products WHERE slug = 'market-day-midi-dress';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'S', 'Floral Navy', 5 FROM products WHERE slug = 'market-day-midi-dress';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'M', 'Floral Clay', 6 FROM products WHERE slug = 'market-day-midi-dress';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'L', 'Floral Clay', 2 FROM products WHERE slug = 'market-day-midi-dress';

INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'S', 'Black', 8 FROM products WHERE slug = 'tailored-work-trouser';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'M', 'Black', 8 FROM products WHERE slug = 'tailored-work-trouser';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'L', 'Camel', 5 FROM products WHERE slug = 'tailored-work-trouser';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'XL', 'Camel', 3 FROM products WHERE slug = 'tailored-work-trouser';

INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'S', 'Heather Gray', 6 FROM products WHERE slug = 'cozy-longline-cardigan';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'M', 'Heather Gray', 6 FROM products WHERE slug = 'cozy-longline-cardigan';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'L', 'Forest', 4 FROM products WHERE slug = 'cozy-longline-cardigan';
INSERT OR IGNORE INTO variants (product_id, size, color, stock_quantity)
SELECT id, 'XL', 'Forest', 2 FROM products WHERE slug = 'cozy-longline-cardigan';
