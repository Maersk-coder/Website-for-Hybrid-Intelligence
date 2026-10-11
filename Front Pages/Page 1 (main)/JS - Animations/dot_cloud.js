// DOT CLOUD: the 3D cloud of dots, drawn with Three.js.
// It holds two shapes at a time ("from" and "to") and blends between them.
class DotCloud {
  static CAMERA_DISTANCE = 6;
  static FIELD_OF_VIEW = 35;

  constructor(canvas) {
    // If Three.js didn't load (for example, no internet), the cloud is simply skipped
    this.ready = typeof THREE !== "undefined";
    if (!this.ready) return;

    const n = SETTINGS.points;
    this.shapes = Shapes.all(n);

    // Three.js works like a film set: the scene holds the objects, the camera looks at them,
    // and the renderer draws what the camera sees onto the canvas.
    this.renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(DotCloud.FIELD_OF_VIEW, 1, 0.1, 100);
    this.camera.position.z = DotCloud.CAMERA_DISTANCE;

    // a random "wobble" direction and number for every dot
    const random = new Float32Array(n * 4);
    for (let i = 0; i < n; i++) {
      const [x, y, z] = Shapes.sphereDirection(Math.floor(Math.random() * n), n);
      const s = 0.3 + Math.random() * 0.7;
      random.set([x * s, y * s, z * s, Math.random()], i * 4);
    }

    // The dots: the geometry holds where every dot is, the material decides how they look
    this.geometry = new THREE.BufferGeometry();
    this.geometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(n * 3), 3)); // shape we come from
    this.geometry.setAttribute("target", new THREE.BufferAttribute(new Float32Array(n * 3), 3));   // shape we go to
    this.geometry.setAttribute("rnd", new THREE.BufferAttribute(random, 4));

    this.material = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      uniforms: {
        uMix: { value: 0 },      // 0 = "from" shape, 1 = "to" shape
        uTime: { value: 0 },
        uSize: { value: 2 },
        uRadius: { value: 1 },
        uAlpha: { value: 1 },
        uDot: { value: new THREE.Color(SETTINGS.dotColor) },
        uAccent: { value: new THREE.Color(SETTINGS.accentColor) },
      },
      vertexShader: DotCloud.VERTEX_SHADER,
      fragmentShader: DotCloud.FRAGMENT_SHADER,
    });

    this.points = new THREE.Points(this.geometry, this.material);
    this.points.frustumCulled = false;
    this.scene.add(this.points);

    const phases = SETTINGS.phases;
    this.showShapes(phases[0].shape, phases[1].shape);
  }

  // Choose which shape we come from and which we go to (names: "human", "machine", "hybrid")
  showShapes(fromName, toName) {
    if (!this.ready) return;
    const { position, target } = this.geometry.attributes;
    position.array.set(this.shapes[fromName]);
    target.array.set(this.shapes[toName]);
    position.needsUpdate = true;
    target.needsUpdate = true;
  }

  // How far through the change we are: 0 = "from" shape, 1 = "to" shape
  setMix(amount) {
    if (this.ready) this.material.uniforms.uMix.value = amount;
  }

  // Place and size the cloud to match the layout
  fitTo(layout) {
    if (!this.ready) return;
    const { width, height } = layout;
    this.renderer.setPixelRatio(layout.pixelRatio);
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();

    // how many 3D units one screen pixel is, at the depth of the cloud
    const unit = (2 * Math.tan((DotCloud.FIELD_OF_VIEW * Math.PI) / 360) * DotCloud.CAMERA_DISTANCE) / height;
    this.points.position.set((layout.centerX - width / 2) * unit, -(layout.centerY - height / 2) * unit, 0);
    const scale = layout.radius * unit;
    this.points.scale.setScalar(scale);

    const u = this.material.uniforms;
    u.uRadius.value = scale * 1.5;
    u.uSize.value = SETTINGS.dotSize * layout.pixelRatio * DotCloud.CAMERA_DISTANCE;
    u.uAlpha.value = layout.wide ? 1 : SETTINGS.phoneOpacity;
  }

  // Turn the cloud and draw it
  render(time, turnX, turnY) {
    if (!this.ready) return;
    this.material.uniforms.uTime.value = time;
    this.points.rotation.set(turnX, turnY, 0);
    this.renderer.render(this.scene, this.camera);
  }

  // Where a point on the cloud ends up on screen, in pixels (used by the pointer lines)
  toScreen(point, layout) {
    if (!this.ready) return null;
    this.points.updateMatrixWorld();
    const v = new THREE.Vector3(...point).applyMatrix4(this.points.matrixWorld).project(this.camera);
    return {
      x: ((v.x + 1) / 2) * layout.width,
      y: ((1 - v.y) / 2) * layout.height,
    };
  }

  // The small programs (shaders) that run on the graphics card for every dot.
  // The vertex shader decides where a dot goes, the fragment shader what colour it gets.
  // The "uniforms" above are the values JavaScript passes into them, like uMix and uTime.

  static VERTEX_SHADER = `
    attribute vec3 target;
    attribute vec4 rnd;
    uniform float uMix, uTime, uSize, uRadius;
    varying float vDepth;
    varying float vAccent;
    void main() {
      vec3 p = mix(position, target, uMix);
      p += rnd.xyz * sin(uMix * 3.14159) * 0.35;                              // dots loosen up halfway through a change
      p += normalize(p + 0.0001) * sin(uTime * 0.9 + rnd.w * 6.2831) * 0.012; // gentle shimmer
      vec4 mv = modelViewMatrix * vec4(p, 1.0);
      gl_Position = projectionMatrix * mv;
      vAccent = step(0.93, rnd.w);
      gl_PointSize = uSize * (1.0 + vAccent * 0.7) / -mv.z;
      vDepth = clamp((-mv.z - (${DotCloud.CAMERA_DISTANCE.toFixed(1)} - uRadius)) / (2.0 * uRadius), 0.0, 1.0); // 0 = front, 1 = back
    }`;

  static FRAGMENT_SHADER = `
    uniform vec3 uDot, uAccent;
    uniform float uAlpha;
    varying float vDepth;
    varying float vAccent;
    void main() {
      float d = length(gl_PointCoord - 0.5);
      if (d > 0.5) discard;                              // round dots
      float edge = smoothstep(0.5, 0.3, d);
      vec3 col = mix(uDot, uAccent, vAccent);
      float a = mix(0.9, 0.18, vDepth) * edge * uAlpha;  // dots further away are fainter
      gl_FragColor = vec4(col, a);
    }`;
}
