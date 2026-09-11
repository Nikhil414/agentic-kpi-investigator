SELECT
      review_id,
      severity,
      reviewer,
      decision,
      reviewer_notes,
      reviewed_at
  FROM finance.investigation_reviews
  ORDER BY review_id DESC;