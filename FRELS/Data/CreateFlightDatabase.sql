,--CREATE DATABASE flights;
\connect flights

-- liste des aéroports
-- http://stat-computing.org/dataexpo/2009/supplemental-data.html
DROP TABLE IF EXISTS airports;
CREATE TABLE airports (
    iata                CHAR(4) PRIMARY KEY,
    airport             VARCHAR,
    city                VARCHAR,
    state               CHAR(2),
    country             VARCHAR,
    lat                 REAL,
    lon                 REAL);
\COPY airports FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/airports.csv'  DELIMITER ',' CSV HEADER;


-- liste des carriers
-- http://stat-computing.org/dataexpo/2009/supplemental-data.html
DROP TABLE IF EXISTS carriers;
CREATE TABLE carriers (
    code                VARCHAR PRIMARY KEY,
    description         VARCHAR);
\COPY carriers FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/carriers.csv'  DELIMITER ',' CSV HEADER;


-- liste des avions
DROP TABLE IF EXISTS planes;
CREATE TABLE planes (
    tailnum             CHAR(6) PRIMARY KEY,
    type                VARCHAR,
    manufacturer        VARCHAR,
    issue_date          DATE,
    model               VARCHAR,
    status              VARCHAR,
    aircraft_type       VARCHAR,
    engine_type         VARCHAR,
    year                SMALLINT);
SET datestyle TO MDY;
\COPY planes FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/plane-data.csv | fgrep , | sed "s/None//g"'  DELIMITER ',' CSV HEADER;



-- liste des vols
DROP TABLE IF EXISTS flights;
CREATE TABLE flights (
    year                SMALLINT,
    month               SMALLINT,
    dayofmonth          SMALLINT,
    dayofweek           SMALLINT,
    deptime             REAL,
    crsdeptime          REAL,
    arrtime             REAL,
    crsarrtime          REAL,
    uniquecarrier       VARCHAR REFERENCES carriers(code),
    flightnum           INTEGER,
    tailnum             CHAR(6),-- REFERENCES planes(tailnum),
    actualelapsedtime   INTEGER,
    crselapsedtime      INTEGER,
    airtime             INTEGER,
    arrdelay            INTEGER,
    depdelay            INTEGER,
    origin              CHAR(4) REFERENCES airports(iata),
    dest                CHAR(4) REFERENCES airports(iata),
    distance            INTEGER,
    taxiin              INTEGER,
    taxiout             INTEGER,
    cancelled           BOOLEAN,
    cancellationcode    CHAR(1),
    diverted            BOOLEAN,
    carrierdelay        INTEGER,
    weatherdelay        INTEGER,
    nasdelay            INTEGER,
    securitydelay       INTEGER,
    lateaircraftdelay   INTEGER);
-- à faire de 1987 à 2008
\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1987.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1988.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1989.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1990.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1991.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1992.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1993.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1994.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1995.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1996.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1997.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1998.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/1999.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/2000.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/2001.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/2002.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/2003.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/2004.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/2005.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/2006.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/2007.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;
--\COPY flights FROM PROGRAM 'curl -s http://stat-computing.org/dataexpo/2009/2008.csv.bz2 | bzcat | ../Src/./process_flights.py' DELIMITER ',' CSV HEADER;



