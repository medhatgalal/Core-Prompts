// PUBLIC contract: finite half-open intervals; empty intervals do not overlap.
// Reversed bounds throw RangeError. No additional type coercion is promised.
export function overlaps([a, b], [c, d]) {
  if (a > b || c > d) throw new RangeError('reversed bounds');
  if (a === b || c === d) return false;
  return a < d && c < b;
}
