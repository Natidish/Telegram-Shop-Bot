-- 1. Merchants Table (የሱቆች መረጃ)
CREATE TABLE IF NOT EXISTS merchants (
    id BIGSERIAL PRIMARY KEY,
    store_id TEXT UNIQUE NOT NULL,
    user_id BIGINT UNIQUE NOT NULL,
    store_name TEXT NOT NULL,
    phone TEXT,
    location TEXT,
    payment_info TEXT,
    products JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Orders Table (የትእዛዞች መረጃ)
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    order_id TEXT UNIQUE NOT NULL,
    customer_id BIGINT NOT NULL,
    store_id TEXT NOT NULL,
    store JSONB,
    product JSONB,
    quantity INT DEFAULT 1,
    name TEXT,
    phone TEXT,
    address TEXT,
    status TEXT DEFAULT 'pending',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Ratings Table (የደረጃ መስጫ መረጃ)
CREATE TABLE IF NOT EXISTS ratings (
    id BIGSERIAL PRIMARY KEY,
    store_id TEXT NOT NULL,
    score INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Disputes Table (የቅሬታዎች መረጃ)
CREATE TABLE IF NOT EXISTS disputes (
    id BIGSERIAL PRIMARY KEY,
    dispute_id TEXT UNIQUE NOT NULL,
    order_id TEXT NOT NULL,
    customer_id BIGINT NOT NULL,
    name TEXT,
    phone TEXT,
    store TEXT,
    store_user_id BIGINT,
    reason TEXT,
    proof_file_id TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
