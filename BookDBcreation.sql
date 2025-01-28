-- WORK BY:
-- Nicolas Puertas (40226395)
-- Somiya Amoroso Colatosti (40190025)
-- Sonia Marrocco (40250575)
-- Tanim Chowdhury (40245607)

-- Table: Authors
CREATE TABLE authors (
    aid VARCHAR(20) PRIMARY KEY,        
    name VARCHAR(255) NOT NULL
);

-- Table: Work
CREATE TABLE work (
    wid VARCHAR(20) PRIMARY KEY,                
    title VARCHAR(255) NOT NULL,               
    first_publish_date VARCHAR(50)              
);

-- Relationship:Work-Authors (many-to-many)
CREATE TABLE work_authors (
    wid VARCHAR(20),                            
    aid VARCHAR(20),                            
    PRIMARY KEY (wid, aid),
    FOREIGN KEY (wid) REFERENCES work(wid) ON DELETE CASCADE,
    FOREIGN KEY (aid) REFERENCES authors(aid) ON DELETE CASCADE
);

-- Table: Bio
CREATE TABLE bio (
    aid VARCHAR(20),
    bid INT GENERATED ALWAYS AS IDENTITY,
    b_text TEXT,
    source VARCHAR(10) NOT NULL,
    PRIMARY KEY(aid,bid), 
    FOREIGN KEY (aid) REFERENCES authors(aid) ON DELETE CASCADE,
    UNIQUE (aid, source)
);

-- Table: Rating
CREATE TABLE rating (
    rid SERIAL PRIMARY KEY,               
    wid VARCHAR(20) NOT NULL,                            
    cnt INT DEFAULT 0,                
    avg_rating DECIMAL(3, 2) DEFAULT NULL, 
    FOREIGN KEY (wid) REFERENCES work(wid) ON DELETE CASCADE
);

-- Table: Edition 
CREATE TABLE edition (
    isbn10 CHAR(10),
    wid VARCHAR(20) NOT NULL,
    publish_date VARCHAR(50),
    PRIMARY KEY (isbn10),
    FOREIGN KEY (wid) REFERENCES work(wid) ON DELETE CASCADE
);

-- Digital
CREATE TABLE digital (
    isbn10 CHAR(10) PRIMARY KEY,
    form VARCHAR(30),                     
    FOREIGN KEY (isbn10) REFERENCES edition(isbn10) ON DELETE CASCADE
);

-- Table: Physical Edition (Specialization of Edition)
CREATE TABLE physical (
    isbn10 CHAR(10) PRIMARY KEY,
    type VARCHAR(30),                                                                        
    FOREIGN KEY (isbn10) REFERENCES edition(isbn10) ON DELETE CASCADE
);

CREATE OR REPLACE FUNCTION validate_isbn10()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.isbn10 !~ '^[0-9]{9}[0-9X]$' THEN
        RAISE EXCEPTION 'Invalid ISBN-10 format. Must be 10 digits or 9 digits followed by X.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER isbn10_trigger
BEFORE INSERT OR UPDATE ON edition
FOR EACH ROW
EXECUTE FUNCTION validate_isbn10();

CREATE INDEX idx_work_authors_wid ON work_authors(wid);
CREATE INDEX idx_bio_aid ON bio(aid);
CREATE INDEX idx_work_title ON work(title);


-- HARD CODED VIEWS
-- Admin View
CREATE VIEW admin_view AS
SELECT 
    w.wid,
    w.title,
    w.first_publish_date,
    r.avg_rating,
    r.cnt,
    e.isbn10
FROM work w
LEFT JOIN rating r ON w.wid = r.wid
LEFT JOIN edition e ON w.wid = e.wid;

--User VIEW
CREATE VIEW user_view AS
SELECT 
    w.title,
    w.first_publish_date,
    r.avg_rating
FROM work w
LEFT JOIN edition e ON w.wid = e.wid
LEFT JOIN rating r ON e.wid = r.wid;
