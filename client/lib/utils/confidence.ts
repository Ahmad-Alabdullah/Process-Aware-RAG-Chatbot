import type { EvidenceChunk, ConfidenceInfo } from "@/types";

/**
 * Sigmoid normalization for cross-encoder rerank scores
 * Maps any real number to [0, 1]
 */
export function sigmoidNormalize(score: number): number {
  return 1 / (1 + Math.exp(-score));
}

/**
 * Clamp cosine similarity to [0, 1]
 */
export function clampCosine(score: number): number {
  return Math.max(0, Math.min(1, score));
}

/**
 * Get confidence score from a single evidence chunk
 * Prefers rerank_score (cross-encoder) over score (dense retrieval)
 */
export function getChunkConfidence(chunk: EvidenceChunk): number {
  if (chunk.rerank_score !== undefined) {
    return sigmoidNormalize(chunk.rerank_score);
  }
  if (chunk.score !== undefined) {
    return clampCosine(chunk.score);
  }
  return 0;
}

/**
 * Compute aggregate answer confidence from evidence chunks
 * Uses max of top-3 chunks for robustness
 */
export function computeAnswerConfidence(
  evidence: EvidenceChunk[]
): ConfidenceInfo {
  if (!evidence || evidence.length === 0) {
    return {
      score: 0,
      level: "low",
      label: "Keine Quellen",
      color: "red",
    };
  }

  // Get confidence scores for all chunks
  const scores = evidence.map(getChunkConfidence);

  // Sort descending and take top 3
  const topScores = scores.sort((a, b) => b - a).slice(0, 3);

  // Use max of top-3 (more robust than average)
  const score = Math.max(...topScores);

  return getConfidenceBadge(score);
}

/**
 * Get badge properties based on confidence score
 */
export function getConfidenceBadge(score: number): ConfidenceInfo {
  if (score >= 0.75) {
    return {
      score,
      level: "high",
      label: "Hoch",
      color: "green",
    };
  }
  if (score >= 0.5) {
    return {
      score,
      level: "medium",
      label: "Mittel",
      color: "amber",
    };
  }
  return {
    score,
    level: "low",
    label: "Niedrig",
    color: "red",
  };
}
