CREATE TABLE IF NOT EXISTS products (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  brand TEXT NOT NULL,
  base_price INTEGER NOT NULL,
  tags_json TEXT NOT NULL,
  specs_json TEXT NOT NULL,
  student_scenario_score INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory (
  product_id TEXT PRIMARY KEY,
  available_stock INTEGER NOT NULL,
  locked_stock INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS coupons (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  coupon_type TEXT NOT NULL,
  target_category TEXT,
  target_product_id TEXT,
  threshold_amount INTEGER,
  discount_amount INTEGER NOT NULL,
  stack_group TEXT NOT NULL,
  is_student_only INTEGER NOT NULL,
  is_active INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS coupon_locks (
  order_id TEXT NOT NULL,
  coupon_id TEXT NOT NULL,
  status TEXT NOT NULL,
  PRIMARY KEY (order_id, coupon_id)
);

CREATE TABLE IF NOT EXISTS carts (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  items_json TEXT NOT NULL,
  selected_coupon_ids_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  status TEXT NOT NULL,
  items_json TEXT NOT NULL,
  coupon_plan_json TEXT NOT NULL,
  total_amount INTEGER NOT NULL,
  discount_amount INTEGER NOT NULL,
  payable_amount INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id TEXT NOT NULL,
  status TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  context_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);