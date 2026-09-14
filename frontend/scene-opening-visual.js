const VIEWER_COLORS = Object.freeze({
  beige: 0xd8c2a4,
  dark_gray_brown: 0x2d2926,
});

/**
 * Return the smallest viewer-only composition already proven by the P1 gate.
 *
 * This is deliberately conservative: it never derives panes, layouts, transoms,
 * frame geometry, or architectural depth. Unsupported/incomplete visual truth
 * falls back to the legacy generic opening renderer.
 */
export function composedOpeningVisualPlan(openingVisual) {
  if (!openingVisual) return null;

  const {
    surround_color: surroundColorName,
    surround_relief: surroundRelief,
    glazing_plane: glazingPlane,
    leaf_count: leafCount,
    mullion_count: mullionCount,
    glazing,
    frame_color: frameColorName,
    frame_material: frameMaterial,
  } = openingVisual;

  if (
    leafCount !== 2 ||
    mullionCount !== 1 ||
    glazing !== 'dark_reflective' ||
    surroundRelief !== 'projecting' ||
    glazingPlane !== 'recessed' ||
    frameMaterial !== 'painted_or_dark_joinery' ||
    !surroundColorName ||
    !frameColorName
  ) return null;

  const surroundColor = VIEWER_COLORS[surroundColorName];
  const frameColor = VIEWER_COLORS[frameColorName];
  if (surroundColor === undefined || frameColor === undefined) return null;

  return {
    surroundColor,
    frameColor,
    glazingColor: 0x15191d,
    surroundRelief,
    glazingPlane,
    mullionCount: 1,
  };
}
