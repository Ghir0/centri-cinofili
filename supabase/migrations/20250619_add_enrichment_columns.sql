-- Add enrichment columns to centri table
ALTER TABLE centri ADD COLUMN IF NOT EXISTS discipline text[] DEFAULT NULL;
ALTER TABLE centri ADD COLUMN IF NOT EXISTS metodologie text[] DEFAULT NULL;
ALTER TABLE centri ADD COLUMN IF NOT EXISTS infrastrutture text[] DEFAULT NULL;
