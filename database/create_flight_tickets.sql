DROP TABLE IF EXISTS tickets CASCADE;

CREATE TABLE tickets (
    ticket_number VARCHAR(13) PRIMARY KEY,
    passenger_name VARCHAR(50) NOT NULL,
    passenger_birthday VARCHAR(8),
    airline_code VARCHAR(10) NOT NULL,
    
    departure_airport CHAR(3) NOT NULL,
    arrival_airport CHAR(3) NOT NULL,
    departure_date VARCHAR(8),  
    departure_time TIME NOT NULL,
    arrival_date VARCHAR(8),   
    arrival_time TIME NOT NULL,
    

    return_departure_airport CHAR(3),
    return_arrival_airport CHAR(3),
    return_date VARCHAR(8),   
    return_departure_time TIME,
    return_arrival_date VARCHAR(8), 
    return_arrival_time TIME,
    
    price_usd DECIMAL(10, 2) NOT NULL
);

INSERT INTO tickets VALUES
    ('ABC1234567890', 'Xinghan Guo', '01011992', 'LH726', 'MUC', 'PVG', 
     '09092025', '13:30:00', '10092025', '06:50:00',  
     'PVG', 'MUC', '10102025', '12:45:00', '10102025', '18:20:00', 1200.00),  
    
    ('ABC0123456789', 'Minhao Fei', '01011990', 'LH730', 'MUC', 'PEK', 
     '11112025', '13:30:00', '12112025', '06:50:00',  
     'PEK', 'MUC', '12122025', '12:45:00', '12122025', '18:20:00', 1000.00), 
    
    ('TKT1234567890', 'John Doe', '15071985', 'AA101', 'JFK', 'LAX', 
     '01112023', '08:00:00', '01112023', '11:00:00',  
     'LAX', 'JFK', '05112023', '18:00:00', '05112023', '23:00:00', 450.00), 
    
    ('TKT2345678901', 'Jane Smith', '22031990', 'DL202', 'ATL', 'SFO',
     '02112023', '09:30:00', '02112023', '12:30:00',  
     'SFO', 'ATL', '06112023', '19:30:00', '06112023', '23:30:00', 500.00),  
    
    ('TKT3456789012', 'Alice Johnson', '05111978', 'UA303', 'ORD', 'DFW',
     '03112023', '10:00:00', '03112023', '13:00:00',  
     NULL, NULL, NULL, NULL, NULL, NULL, 300.00),
    
    ('TKT4567890123', 'Bob Brown', '12091995', 'SW404', 'DEN', 'SEA',
     '04112023', '11:00:00', '04112023', '14:00:00',  
     'SEA', 'DEN', '08112023', '20:00:00', '08112023', '22:00:00', 350.00), 
    
    ('TKT5678901234', 'Charlie Davis', '18041982', 'BA505', 'LHR', 'CDG',
     '05112023', '12:00:00', '05112023', '15:00:00',  
     'CDG', 'LHR', '10112023', '21:00:00', '10112023', '22:30:00', 600.00);  

CREATE INDEX idx_ticket_search ON tickets (ticket_number, passenger_name, passenger_birthday);