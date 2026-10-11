// SHAPES: the three forms the dot cloud changes between.
// Each shape is a long list of numbers: x, y, z for every dot.
// The methods are "static", so they are used straight from the class (Shapes.human(n)), without "new".
class Shapes {
  // Makes all three shapes with n dots each
  static all(n) {
    return {
      human: Shapes.human(n),
      machine: Shapes.machine(n),
      hybrid: Shapes.hybrid(n),
    };
  }

  // 1. HUMAN: a soft, organic, slightly folded form
  static human(n) {
    const p = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const [x, y, z] = Shapes.sphereDirection(i, n);
      const folds =
        0.1 * Math.sin(3 * x + 2 * y) +
        0.08 * Math.sin(4 * y - 3 * z + 1.3) +
        0.05 * Math.sin(7 * z + 5 * x + 0.7) +
        0.025 * Math.sin(13 * x + 11 * y + 9 * z);
      const r = 1 + folds;
      p.set([x * r, y * r, z * r], i * 3);
    }
    return Shapes.shuffled(p);
  }

  // 2. MACHINE: two nested crystals (icosahedrons) with spokes between them
  static machine(n) {
    const g = (1 + Math.sqrt(5)) / 2;
    const raw = [
      [-1, g, 0], [1, g, 0], [-1, -g, 0], [1, -g, 0],
      [0, -1, g], [0, 1, g], [0, -1, -g], [0, 1, -g],
      [g, 0, -1], [g, 0, 1], [-g, 0, -1], [-g, 0, 1],
    ];
    const len = Math.hypot(1, g);
    const edges = [];
    for (let a = 0; a < 12; a++)
      for (let b = a + 1; b < 12; b++) {
        const d = Math.hypot(raw[a][0] - raw[b][0], raw[a][1] - raw[b][1], raw[a][2] - raw[b][2]);
        if (Math.abs(d - 2) < 0.01) edges.push([a, b]);
      }
    const outer = raw.map((v) => v.map((c) => (c / len) * 1.15));
    const inner = raw.map((v) => [v[1], v[2], v[0]].map((c) => (c / len) * 0.55)); // turned, smaller

    // a random point on the straight line from A to B
    const along = (A, B) => {
      const u = Math.random();
      const j = () => (Math.random() - 0.5) * 0.012;
      return [A[0] + (B[0] - A[0]) * u + j(), A[1] + (B[1] - A[1]) * u + j(), A[2] + (B[2] - A[2]) * u + j()];
    };

    const p = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const pick = Math.random();
      let pt;
      if (pick < 0.6) {
        const [a, b] = edges[i % edges.length];
        pt = along(outer[a], outer[b]);       // 60% on the outer crystal
      } else if (pick < 0.85) {
        const [a, b] = edges[i % edges.length];
        pt = along(inner[a], inner[b]);       // 25% on the inner crystal
      } else {
        const v = i % 12;
        pt = along(inner[v], outer[v]);       // 15% on the spokes
      }
      p.set(pt, i * 3);
    }
    return Shapes.shuffled(p);
  }

  // 3. HYBRID: a tube shaped like the infinity symbol, twisting slightly in depth
  static hybrid(n) {
    const curve = (t) => {
      const s = Math.sin(t), c = Math.cos(t), d = 1 + s * s;
      return [(1.2 * c) / d, (1.3 * s * c) / d, 0.35 * s];
    };
    const p = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const t = Math.random() * Math.PI * 2;
      const a = Math.random() * Math.PI * 2;
      const c0 = curve(t), c1 = curve(t + 0.001);
      // direction of the curve, and two directions at right angles to it
      let tx = c1[0] - c0[0], ty = c1[1] - c0[1], tz = c1[2] - c0[2];
      const tl = Math.hypot(tx, ty, tz); tx /= tl; ty /= tl; tz /= tl;
      let nx = ty, ny = -tx, nz = 0;
      const nl = Math.hypot(nx, ny) || 1; nx /= nl; ny /= nl;
      const bx = ty * nz - tz * ny, by = tz * nx - tx * nz, bz = tx * ny - ty * nx;
      const r = 0.2; // thickness of the tube
      p.set([
        c0[0] + (nx * Math.cos(a) + bx * Math.sin(a)) * r,
        c0[1] + (ny * Math.cos(a) + by * Math.sin(a)) * r,
        c0[2] + (nz * Math.cos(a) + bz * Math.sin(a)) * r,
      ], i * 3);
    }
    return Shapes.shuffled(p);
  }

  // Helpers 

  // Spreads n points evenly over a ball, returns the direction of point i
  static sphereDirection(i, n) {
    const y = 1 - (2 * (i + 0.5)) / n;
    const r = Math.sqrt(1 - y * y);
    const a = i * 2.399963; // the "golden angle" spreads points evenly
    return [Math.cos(a) * r, y, Math.sin(a) * r];
  }

  // Mixes up the order, so each dot travels to a random place in the next shape (looks like a swarm)
  static shuffled(points) {
    const n = points.length / 3;
    for (let i = n - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      for (let k = 0; k < 3; k++) {
        const t = points[i * 3 + k];
        points[i * 3 + k] = points[j * 3 + k];
        points[j * 3 + k] = t;
      }
    }
    return points;
  }
}
