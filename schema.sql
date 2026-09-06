-- 🎊 TELEGRAM SHOP BOT V4 - DATABASE SCHEMA
-- ================================================
-- Run this SQL in Supabase → SQL Editor
-- All tables, indexes, and constraints

-- ====================== MERCHANTS TABLE ======================
-- Stores merchant/shop information
create table if not exists merchants (
    user_id         bigint primary key,
    username        text,
    store_id        text unique not null,
    store_name      text,
    phone           text,
    location        text,
    payment_method  text,
    products        jsonb default '[]'::jsonb,
    created         timestamptz default now()
);

comment on table merchants is 'ነጋዴዎች - Merchant shops';
comment on column merchants.user_id is 'Telegram user ID (primary key)';
comment on column merchants.store_id is 'Unique store identifier for deep-links';
comment on column merchants.products is 'Array of products: [{name, price, photo_file_id}, ...]';

-- ====================== ORDERS TABLE ======================
-- Stores all customer orders
create table if not exists orders (
    order_id                text primary key,
    store                   jsonb,
    product                 jsonb,
    name                    text,
    phone                   text,
    address                 text,
    customer_id             bigint,
    status                  text,
    payment_choice          text,
    payment_proof_file_id   text,
    stars_amount            int,
    "timestamp"             timestamptz default now()
);

comment on table orders is 'ትዕዛዞች - Customer orders';
comment on column orders.order_id is 'Unique order ID';
comment on column orders.store is 'Full store object (store_id, store_name, user_id, payment_method)';
comment on column orders.product is 'Product object (name, price)';
comment on column orders.status is 'Order status: awaiting_payment_method, awaiting_payment_proof, paid_pending_confirmation, cod_confirmed, stars_paid, delivered';
comment on column orders.payment_choice is 'mobile (screenshot), cod (cash on delivery), stars (telegram stars)';
comment on column orders.payment_proof_file_id is 'Telegram file_id of payment screenshot (if mobile)';
comment on column orders.stars_amount is 'Number of Telegram Stars paid (if stars)';

-- ====================== DISPUTES TABLE ======================
-- Stores customer disputes/complaints
create table if not exists disputes (
    dispute_id      text primary key,
    order_id        text,
    customer_id     bigint,
    name            text,
    phone           text,
    store           text,
    store_user_id   bigint,
    reason          text,
    proof_file_id   text,
    "timestamp"     timestamptz default now()
);

comment on table disputes is 'ቅሬታዎች - Customer disputes/complaints';
comment on column disputes.dispute_id is 'Unique dispute ID';
comment on column disputes.order_id is 'Related order ID';
comment on column disputes.reason is 'Why customer filed dispute (text)';
comment on column disputes.proof_file_id is 'Telegram file_id of evidence photo (if any)';

-- ====================== RATINGS TABLE ======================
-- Stores customer ratings for each store
create table if not exists ratings (
    store_id    text primary key,
    scores      jsonb default '[]'::jsonb
);

comment on table ratings is 'ደረጃዎች - Customer ratings for stores';
comment on column ratings.scores is 'Array of rating scores: [5, 4, 5, 3, ...]';

-- ====================== INDEXES FOR PERFORMANCE ======================
-- Speed up queries by store_id and customer_id
create index if not exists idx_orders_customer_id on orders (customer_id);
create index if not exists idx_orders_store_id on orders ((store->>'store_id'));
create index if not exists idx_disputes_order_id on disputes (order_id);
create index if not exists idx_disputes_customer_id on disputes (customer_id);
create index if not exists idx_merchants_store_id on merchants (store_id);

-- ====================== QUICK REFERENCE ======================
-- 
-- MERCHANTS:
--   user_id: Telegram user ID (primary key)
--   store_id: "store_abc123xyz" (unique, for deep-links)
--   products: [{name: "ጫማ", price: 1500, photo_file_id: "AgAD..."}, ...]
--
-- ORDERS:
--   order_id: "order_xyz789"
--   store: {user_id, store_id, store_name, payment_method}
--   product: {name, price}
--   status: awaiting_payment_method → awaiting_payment_proof → paid_pending_confirmation → delivered
--   payment_choice: "mobile", "cod", or "stars"
--
-- DISPUTES:
--   dispute_id: "disp_abc123"
--   order_id: Related order
--   reason: Customer's complaint text
--   proof_file_id: Screenshot/evidence
--
-- RATINGS:
--   store_id: "store_abc123xyz"
--   scores: [5, 4, 5, 5, 3, ...] — array of 1-5 ratings
--
-- ====================== HOW TO USE ======================
--
-- 1. Go to Supabase → SQL Editor
-- 2. Copy all this code
-- 3. Paste into SQL Editor
-- 4. Click "Run"
-- 5. All tables and indexes created automatically
-- 6. Set SUPABASE_URL and SUPABASE_KEY in bot environment
-- 7. Bot will connect and use these tables
--
-- No manual data entry needed — bot creates records automatically!
--
