CREATE TABLE tickets (
    ticket_no VARCHAR(13) PRIMARY KEY,  -- 票号（主键）
    passenger_name VARCHAR(50) NOT NULL,  -- 乘客姓名
    birth_date DATE NOT NULL,            -- 生日
    airline_code VARCHAR(10) NOT NULL,   -- 航班号
    
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

INSERT INTO tickets (
    ticket_no, passenger_name, birth_date, airline_code,
    departure_airport_code, arrival_airport_code,
    departure_date, departure_time, arrival_date, arrival_time,
    return_departure_airport_code, return_arrival_airport_code,
    return_departure_date, return_departure_time, return_arrival_date, return_arrival_time,
    price_usd
) VALUES
    ('TKT1234567890', 'John Doe', '1985-07-15', 'AA101', 'JFK', 'LAX', '2023-11-01', '08:00:00', '2023-11-01', '11:00:00', 'LAX', 'JFK', '2023-11-05', '18:00:00', '2023-11-05', '23:00:00', 450.00),
    ('TKT2345678901', 'Jane Smith', '1990-03-22', 'DL202', 'ATL', 'SFO', '2023-11-02', '09:30:00', '2023-11-02', '12:30:00', 'SFO', 'ATL', '2023-11-06', '19:30:00', '2023-11-06', '23:30:00', 500.00),
    ('TKT3456789012', 'Alice Johnson', '1978-11-05', 'UA303', 'ORD', 'DFW', '2023-11-03', '10:00:00', '2023-11-03', '13:00:00', NULL, NULL, NULL, NULL, NULL, NULL, 300.00),
    ('TKT4567890123', 'Bob Brown', '1995-09-12', 'SW404', 'DEN', 'SEA', '2023-11-04', '11:00:00', '2023-11-04', '14:00:00', 'SEA', 'DEN', '2023-11-08', '20:00:00', '2023-11-08', '22:00:00', 350.00),
    ('TKT5678901234', 'Charlie Davis', '1982-04-18', 'BA505', 'LHR', 'CDG', '2023-11-05', '12:00:00', '2023-11-05', '15:00:00', 'CDG', 'LHR', '2023-11-10', '21:00:00', '2023-11-10', '22:30:00', 600.00);
-- 添加索引加速查询
CREATE INDEX idx_ticket_search ON tickets (ticket_no, passenger_name, birth_date);