DROP TABLE IF EXISTS tickets CASCADE;

CREATE TABLE tickets (
    ticket_number VARCHAR(13) PRIMARY KEY,  -- Ticket number (primary key)
    passenger_name VARCHAR(50) NOT NULL,  -- Passenger name
    passenger_birthday VARCHAR(8),             -- Birth date
    airline_code VARCHAR(10) NOT NULL,    -- Airline code
    
    -- Outbound flight information
    departure_airport CHAR(3) NOT NULL,  -- Departure airport code (e.g., PEK)
    arrival_airport CHAR(3) NOT NULL,    -- Arrival airport code
    departure_date VARCHAR(6),             -- Departure date
    departure_time TIME NOT NULL,             -- Departure time
    arrival_date VARCHAR(6),               -- Arrival date
    arrival_time TIME NOT NULL,               -- Arrival time
    
    -- Return flight information (optional)
    return_departure_airport CHAR(3),    -- Return departure airport
    return_arrival_airport CHAR(3),      -- Return arrival airport
    return_date VARCHAR(6),
    return_departure_time TIME,
    return_arrival_date VARCHAR(6),
    return_arrival_time TIME,
    
    price_usd DECIMAL(10, 2) NOT NULL         -- Price (USD)
);

INSERT INTO tickets (
    ticket_number, passenger_name, passenger_birthday, airline_code,
    departure_airport, arrival_airport,
    departure_date, departure_time, arrival_date, arrival_time,
    return_departure_airport, return_arrival_airport,
    return_date, return_departure_time, return_arrival_date, return_arrival_time,
    price_usd
) VALUES
    ('ABC1234567890', 'Xinghan Guo', '01011992', 'LH726', 'MUC', 'PVG', '250909', '13:30:00', '250910', '06:50:00', 'PVG', 'MUC', '251010', '12:45:00', '251010', '18:20:00', 1200.00),
    ('ABC0123456789', 'Minhao Fei', '01011990', 'LH726', 'MUC', 'PEK', '251111', '13:30:00', '251112', '06:50:00', 'PVG', 'PEK', '251212', '12:45:00', '251212', '18:20:00', 1000.00),
    ('TKT1234567890', 'John Doe', '15071985', 'AA101', 'JFK', 'LAX', '231101', '08:00:00', '231101', '11:00:00', 'LAX', 'JFK', '231105', '18:00:00', '231105', '23:00:00', 450.00),
    ('TKT2345678901', 'Jane Smith', '22031990', 'DL202', 'ATL', 'SFO', '231102', '09:30:00', '231102', '12:30:00', 'SFO', 'ATL', '231106', '19:30:00', '231106', '23:30:00', 500.00),
    ('TKT3456789012', 'Alice Johnson', '05111978', 'UA303', 'ORD', 'DFW', '231103', '10:00:00', '231103', '13:00:00', NULL, NULL, NULL, NULL, NULL, NULL, 300.00),
    ('TKT4567890123', 'Bob Brown', '12091995', 'SW404', 'DEN', 'SEA', '231104', '11:00:00', '231104', '14:00:00', 'SEA', 'DEN', '231108', '20:00:00', '231108', '22:00:00', 350.00),
    ('TKT5678901234', 'Charlie Davis', '18041982', 'BA505', 'LHR', 'CDG', '231105', '12:00:00', '231105', '15:00:00', 'CDG', 'LHR', '231110', '21:00:00', '231110', '22:30:00', 600.00);
-- Create index to speed up search queries
CREATE INDEX idx_ticket_search ON tickets (ticket_number, passenger_name, passenger_birthday);
