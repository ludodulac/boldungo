export function gableRoofTriangles({
  x,
  y,
  z,
  width,
  depth,
  height,
  pitchDegrees,
  overhang = 0,
  ridgeDirection,
}) {
  const values = [x, y, z, width, depth, height, pitchDegrees, overhang].map(Number);
  if (!values.every(Number.isFinite)) return null;
  const [px, py, pz, w, d, h, pitch, oh] = values;
  if (!(w > 0) || !(d > 0) || !(h > 0) || !(pitch > 0 && pitch < 90) || oh < 0) return null;
  if (ridgeDirection !== 'depth' && ridgeDirection !== 'width') return null;

  const top = pz + h;
  const x0 = px - oh;
  const x1 = px + w + oh;
  const y0 = py - oh;
  const y1 = py + d + oh;

  let ridgeA;
  let ridgeB;
  let eaveA0;
  let eaveA1;
  let eaveB0;
  let eaveB1;
  let halfRun;

  if (ridgeDirection === 'depth') {
    const ridgeX = px + w / 2;
    halfRun = (w + 2 * oh) / 2;
    ridgeA = [ridgeX, y0];
    ridgeB = [ridgeX, y1];
    eaveA0 = [x0, y0];
    eaveA1 = [x0, y1];
    eaveB0 = [x1, y0];
    eaveB1 = [x1, y1];
  } else {
    const ridgeY = py + d / 2;
    halfRun = (d + 2 * oh) / 2;
    ridgeA = [x0, ridgeY];
    ridgeB = [x1, ridgeY];
    eaveA0 = [x0, y0];
    eaveA1 = [x1, y0];
    eaveB0 = [x0, y1];
    eaveB1 = [x1, y1];
  }

  const ridgeZ = top + Math.tan((pitch * Math.PI) / 180) * halfRun;
  const v = ([vx, vy], vz) => [vx, vz, vy]; // architectural x/y/z -> THREE x/y/z
  const a0 = v(eaveA0, top);
  const a1 = v(eaveA1, top);
  const b0 = v(eaveB0, top);
  const b1 = v(eaveB1, top);
  const r0 = v(ridgeA, ridgeZ);
  const r1 = v(ridgeB, ridgeZ);

  return {
    ridgeDirection,
    topElevation: top,
    ridgeElevation: ridgeZ,
    vertices: [
      ...a0, ...a1, ...r1,
      ...a0, ...r1, ...r0,
      ...b0, ...r0, ...r1,
      ...b0, ...r1, ...b1,
    ],
  };
}
