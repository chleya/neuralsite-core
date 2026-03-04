# NeuralSite PostGIS Spatial Module

PostgreSQL + PostGIS integration for spatial queries.

## Database Setup

```sql
-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Projects table
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    coordinate_system VARCHAR(50) DEFAULT 'CGCS2000',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Spatial points table (with PostGIS geometry)
CREATE TABLE spatial_points (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    chainage VARCHAR(20),  -- 桩号 K0+500
    point_type VARCHAR(50), -- subgrade, centerline, edge, etc.
    
    -- PostGIS geometry column
    geom GEOMETRY(Point, 4490), -- CGCS2000 SRID
    
    -- Attributes
    elevation FLOAT,
    azimuth FLOAT,
    properties JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index
CREATE INDEX spatial_points_geom_idx ON spatial_points USING GIST(geom);

-- Create chainage index
CREATE INDEX spatial_points_chainage_idx ON spatial_points(chainage);
```

## Install

```bash
pip install psycopg2-binary sqlalchemy geoalchemy2
```
