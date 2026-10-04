"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { createTakaCoinTexture } from "./coinTexture";
import { disposeThreeScene } from "./utils/disposeThreeScene";

export default function GoldTakaCoinCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const width = container.clientWidth || 360;
    const height = container.clientHeight || 360;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 7.5);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;
    container.appendChild(renderer.domElement);

    // 2. Procedural Bump Map & Metallic Gold Material
    const bumpTexture = createTakaCoinTexture();
    const goldMaterial = new THREE.MeshPhysicalMaterial({
      color: 0xffc709, // Vibrant Upay Gold
      emissive: 0x221800,
      metalness: 0.95,
      roughness: 0.22,
      clearcoat: 0.35,
      clearcoatRoughness: 0.1,
      bumpMap: bumpTexture,
      bumpScale: 0.035,
      reflectivity: 0.9,
    });

    // 3. Coin Geometry (Cylinder with high radial fidelity)
    const coinGeometry = new THREE.CylinderGeometry(2.1, 2.1, 0.32, 64);
    coinGeometry.rotateX(Math.PI / 2);

    const coin = new THREE.Mesh(coinGeometry, goldMaterial);
    coin.rotation.y = 0.35;
    coin.rotation.x = 0.15;
    scene.add(coin);

    // 4. Upay Themed Lighting Setup
    const ambientLight = new THREE.AmbientLight(0x0a1c3c, 1.4); // Navy ambient
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xfff7d6, 3.2); // Warm key
    keyLight.position.set(5, 6, 5);
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0xffc709, 4.5); // Upay Yellow edge
    rimLight.position.set(-6, -4, -4);
    scene.add(rimLight);

    const blueFill = new THREE.PointLight(0x153a7a, 2.0, 15);
    blueFill.position.set(0, -5, 4);
    scene.add(blueFill);

    // 5. Physics & Pointer Interaction State
    let isHovered = false;
    let isDragging = false;
    let prevPointerX = 0;
    let angularVelocityY = 0;
    const targetTilt = { x: 0, y: 0 };
    let animId: number;

    const onPointerMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const normX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const normY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);

      if (isDragging) {
        const deltaX = e.clientX - prevPointerX;
        angularVelocityY = deltaX * 0.015;
        coin.rotation.y += angularVelocityY;
        prevPointerX = e.clientX;
      } else {
        targetTilt.x = normY * 0.45;
        targetTilt.y = normX * 0.55;
      }
    };

    const onPointerDown = (e: MouseEvent) => {
      isDragging = true;
      prevPointerX = e.clientX;
    };

    const onPointerUp = () => {
      isDragging = false;
    };

    const onPointerEnter = () => {
      isHovered = true;
    };

    const onPointerLeave = () => {
      isHovered = false;
      isDragging = false;
      targetTilt.x = 0;
      targetTilt.y = 0;
    };

    container.addEventListener("mousemove", onPointerMove);
    container.addEventListener("mousedown", onPointerDown);
    window.addEventListener("mouseup", onPointerUp);
    container.addEventListener("mouseenter", onPointerEnter);
    container.addEventListener("mouseleave", onPointerLeave);

    // 6. Animation Render Loop with Inertia & Friction
    const animate = () => {
      animId = requestAnimationFrame(animate);

      if (!prefersReducedMotion) {
        if (isDragging) {
          // Drag controls rotation directly
        } else if (Math.abs(angularVelocityY) > 0.0005) {
          coin.rotation.y += angularVelocityY;
          angularVelocityY *= 0.94; // Friction decay
        } else {
          coin.rotation.y += isHovered ? 0.018 : 0.008; // Idle spin
        }

        // Smooth lerp to mouse tilt
        coin.rotation.x += (targetTilt.x - coin.rotation.x) * 0.08;
        coin.position.y = Math.sin(Date.now() * 0.002) * 0.08; // Subtle floating bob
      }

      renderer.render(scene, camera);
    };

    animate();

    // 7. Cleanup & WebGL Context Release
    return () => {
      cancelAnimationFrame(animId);
      container.removeEventListener("mousemove", onPointerMove);
      container.removeEventListener("mousedown", onPointerDown);
      window.removeEventListener("mouseup", onPointerUp);
      container.removeEventListener("mouseenter", onPointerEnter);
      container.removeEventListener("mouseleave", onPointerLeave);

      disposeThreeScene(scene, renderer, container);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-72 h-72 sm:w-88 sm:h-88 lg:w-96 lg:h-96 cursor-grab active:cursor-grabbing mx-auto select-none"
      aria-label="Interactive 3D Sohoj Gold Taka Token"
    />
  );
}
