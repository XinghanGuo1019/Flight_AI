CREATE TABLE tickets (
    ticket_id VARCHAR(13) PRIMARY KEY,  -- 票号（主键）
    passenger_name VARCHAR(50) NOT NULL,  -- 乘客姓名
    birth_date DATE NOT NULL,            -- 生日
    flight_number VARCHAR(10) NOT NULL,   -- 航班号
    
    -- 去程信息
    departure_airport_code CHAR(3) NOT NULL,  -- 出发机场三字码（如 PEK）
    arrival_airport_code CHAR(3) NOT NULL,    -- 到达机场三字码
    departure_date DATE NOT NULL,             -- 出发日期
    departure_time TIME NOT NULL,             -- 出发时间
    arrival_date DATE NOT NULL,               -- 到达日期
    arrival_time TIME NOT NULL,               -- 到达时间
    
    -- 回程信息（可选）
    return_departure_airport_code CHAR(3),     -- 回程出发机场
    return_arrival_airport_code CHAR(3),       -- 回程到达机场
    return_departure_date DATE,
    return_departure_time TIME,
    return_arrival_date DATE,
    return_arrival_time TIME,
    
    price_usd DECIMAL(10, 2) NOT NULL         -- 价格（USD）
);

-- 添加索引加速查询
CREATE INDEX idx_ticket_search ON tickets (ticket_id, passenger_name, birth_date);