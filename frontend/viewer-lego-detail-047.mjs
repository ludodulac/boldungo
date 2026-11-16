// M047 — bounded, deterministic selection of small real-style LEGO bricks.
// Geometry selection affects appearance only: the BrickHouse export is immutable.
export function legoDetailFootprint(part) {
  if (!part || !['brick', 'plate', 'facade_detail'].includes(part.category)) return null;
  if (typeof part.part_id !== 'string' || /SLOPED|ROOF|WEDGE/i.test(part.part_id)) return null;
  const match = /^(?:BRICK|PLATE)_(\d+)X(\d+)(?:_|$)/.exec(part.part_id);
  if (!match) return null;
  const originalWidth = part.width_studs ?? Number(match[1]);
  const originalLength = part.length_studs ?? Number(match[2]);
  const rotated = Number(part.rotation_quarter_turns || 0) % 2 !== 0;
  const width = rotated ? originalLength : originalWidth;
  const length = rotated ? originalWidth : originalLength;
  if (!Number.isInteger(width) || !Number.isInteger(length) ||
      width <= 0 || length <= 0 || width * length > 8) return null;
  return { width, length };
}

export function legoStudOffsets(width, length) {
  if (!Number.isInteger(width) || !Number.isInteger(length) ||
      width < 1 || length < 1 || width * length > 8) return [];
  const positions = [];
  for (let x = 0; x < width; x++)
    for (let z = 0; z < length; z++)
      positions.push([x - (width - 1) / 2, z - (length - 1) / 2]);
  return positions;
}

export function selectLegoDetailIds(parts, budget = 64) {
  if (!Array.isArray(parts) || budget < 1) return [];
  const windows = parts.filter(p => p?.category === 'window_pane' || p?.category === 'window_frame');
  // A single opening anchors a LOCAL demonstration, not a global remesh.
  const anchor = windows.find(p => p.facade === 'front') || windows[0] || null;
  const candidates = [];
  parts.forEach((part, index) => {
    const shape = legoDetailFootprint(part);
    if (!shape || typeof part.placement_id !== 'string') return;
    const dx = anchor ? (part.x_studs || 0) - (anchor.x_studs || 0) : 0;
    const dy = anchor ? (part.y_studs || 0) - (anchor.y_studs || 0) : 0;
    const dz = anchor ? ((part.z_plates || 0) - (anchor.z_plates || 0)) / 3 : 0;
    // No opening? Prefer the front facade in the original deterministic order.
    const score = anchor
      ? dx * dx + dy * dy + dz * dz + (part.category === 'plate' ? 5 : 0)
      : (part.facade === 'front' ? 0 : 1000) + (part.category === 'plate' ? 10 : 0);
    candidates.push({ id: part.placement_id, index, score });
  });
  candidates.sort((a, b) => a.score - b.score || a.index - b.index);
  return [...new Set(candidates.slice(0, Math.floor(budget)).map(p => p.id))];
}

export const LEGO_DETAIL_M047_BUDGET = Object.freeze({ mobile: 48, desktop: 144 });
