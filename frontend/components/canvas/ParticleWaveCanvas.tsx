"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { disposeThreeScene } from "./utils/disposeThreeScene";

export default function ParticleWaveCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const scene = new THREE.Scene();
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || 600;

    const camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 100);
    camera.position.set(0, 12, 22);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    container.appendChild(renderer.domElement);

    // Grid Dimensions: 55 x 45 = 2475 points
    const cols = 55;
    const rows = 45;
    const totalPoints = cols * rows;
    const positions = new Float32Array(totalPoints * 3);
    const colors = new Float32Array(totalPoints * 3);

    const colorNavy = new THREE.Color(0x0a1c3c);
    const colorCyan = new THREE.Color(0x00d2ff);
    const colorGold = new THREE.Color(0xffc709);

    let idx = 0;
    for (let i = 0; i < cols; i++) {
      for (let j = 0; j < rows; j++) {
        const x = (i - cols / 2) * 0.95;
        const z = (j - rows / 2) * 0.95;
        const y = 0;

        positions[idx * 3] = x;
        positions[idx * 3 + 1] = y;
        positions[idx * 3 + 2] = z;

        // Gradient blend
        const t = (i / cols + j / rows) * 0.5;
        const blended = colorNavy.clone().lerp(t > 0.6 ? colorGold : colorCyan, t);
        colors[idx * 3] = blended.r;
        colors[idx * 3 + 1] = blended.g;
        colors[idx * 3 + 2] = blended.b;
        idx++;
      }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("aColor", new THREE.BufferAttribute(colors, 3));

    const uniforms = {
      uTime: { value: 0 },
      uMouse: { value: new THREE.Vector2(-999, -999) },
      uMouseRadius: { value: 8.0 },
      uMouseStrength: { value: 2.4 },
    };

    const shaderMaterial = new THREE.ShaderMaterial({
      uniforms,
      vertexShader: `
        uniform float uTime;
        uniform vec2 uMouse;
        uniform float uMouseRadius;
        uniform float uMouseStrength;
        attribute vec3 aColor;
        varying vec3 vColor;
        varying float vElevation;
        void main() {
          vec3 pos = position;
          float wave = sin(pos.x * 0.15 + uTime * 1.5) * cos(pos.z * 0.15 + uTime * 1.2) * 1.6;
          float dist = distance(pos.xz, uMouse);
          if (dist < uMouseRadius) {
            float influence = smoothstep(uMouseRadius, 0.0, dist);
            wave += sin(dist * 1.8 - uTime * 4.0) * uMouseStrength * influence;
          }
          pos.y += wave;
          vElevation = wave;
          vColor = aColor;
          vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
          gl_PointSize = (22.0 / -mvPosition.z) * (1.0 + wave * 0.2);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        varying float vElevation;
        void main() {
          vec2 center = gl_PointCoord - vec2(0.5);
          float dist = length(center);
          if (dist > 0.5) discard;
          float alpha = smoothstep(0.5, 0.08, dist);
          vec3 gold = vec3(1.0, 0.78, 0.035);
          vec3 finalColor = mix(vColor, gold, smoothstep(0.4, 2.0, vElevation));
          gl_FragColor = vec4(finalColor, alpha * 0.85);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const particles = new THREE.Points(geometry, shaderMaterial);
    scene.add(particles);

    // Mouse Tracking on Ground Plane
    const raycaster = new THREE.Raycaster();
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    const planeIntersect = new THREE.Vector3();

    const onPointerMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const normX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const normY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      raycaster.setFromCamera(new THREE.Vector2(normX, normY), camera);
      if (raycaster.ray.intersectPlane(plane, planeIntersect)) {
        uniforms.uMouse.value.set(planeIntersect.x, planeIntersect.z);
      }
    };

    const onPointerLeave = () => {
      uniforms.uMouse.value.set(-999, -999);
    };

    const onResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener("resize", onResize);
    window.addEventListener("mousemove", onPointerMove);
    window.addEventListener("mouseleave", onPointerLeave);

    let animId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      if (!prefersReducedMotion) {
        uniforms.uTime.value = clock.getElapsedTime();
      }
      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("mousemove", onPointerMove);
      window.removeEventListener("mouseleave", onPointerLeave);

      disposeThreeScene(scene, renderer, container);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 pointer-events-none opacity-60 overflow-hidden"
      aria-hidden="true"
    />
  );
}
