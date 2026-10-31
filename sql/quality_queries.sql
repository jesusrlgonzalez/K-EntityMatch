-- For SQLite outputs/demo/i24_review.sqlite. This is NON-PRODUCTION SYNTHETIC evidence.
SELECT quality_disposition, COUNT(*) AS n FROM triage GROUP BY quality_disposition;
SELECT triage_status,COUNT(*) AS n FROM triage GROUP BY triage_status;
SELECT reference_source,COUNT(*) AS candidate_pairs FROM matches GROUP BY reference_source;
SELECT client_id,reference_id,score,priority FROM matches WHERE priority='HIGH_PRIORITY_REVIEW' ORDER BY score DESC LIMIT 25;
-- ABSENCE of a row DOES NOT mean clear of sanctions.
