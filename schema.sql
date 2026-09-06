-- ==========================================================
-- Telegram Shop Bot — Supabase schema
-- Run this once in Supabase → SQL Editor → New query → Run
-- ==========================================================

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

create table if not exists ratings (
    store_id    text primary key,
    scores      jsonb default '[]'::jsonb
);

-- Helpful indexes
create index if not exists idx_orders_customer_id on orders (customer_id);
create index if not exists idx_orders_store_id on orders ((store->>'store_id'));

-- Row Level Security: the bot connects with the SERVICE ROLE key
-- (not the anon key), which bypasses RLS. If you enable RLS on
-- these tables for extra safety, no additional policies are
-- required as long as SUPABASE_KEY is the service_role key.
-- alter table merchants enable row level security;
-- alter table orders enable row level security;
-- alter table disputes enable row level security;
-- alter table ratings enable row level security;
