export function platformSupportBox(support) {
  const position = support?.position;
  const width = Number(support?.width);
  const depth = Number(support?.depth);
  const height = Number(support?.height);
  if (!position) return null;
  const x = Number(position.x);
  const y = Number(position.y);
  const z = Number(position.z);
  if (![x, y, z, width, depth, height].every(Number.isFinite)) return null;
  if (!(width > 0 && depth > 0 && height > 0)) return null;
  return {
    width,
    depth,
    height,
    center: {
      x: x + width / 2,
      y: z + height / 2,
      z: y + depth / 2,
    },
  };
}
