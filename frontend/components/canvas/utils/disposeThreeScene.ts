import * as THREE from "three";

export function disposeThreeScene(
  scene: THREE.Scene,
  renderer: THREE.WebGLRenderer,
  container: HTMLElement
) {
  // 1. Traverse and dispose all geometries, materials, and textures
  scene.traverse((object) => {
    if ((object as THREE.Mesh).isMesh) {
      const mesh = object as THREE.Mesh;
      if (mesh.geometry) {
        mesh.geometry.dispose();
      }

      if (mesh.material) {
        if (Array.isArray(mesh.material)) {
          mesh.material.forEach(disposeMaterial);
        } else {
          disposeMaterial(mesh.material);
        }
      }
    }
  });

  // 2. Clear Scene
  scene.clear();

  // 3. Dispose renderer & force context release
  renderer.dispose();
  renderer.forceContextLoss();

  // 4. Remove DOM element
  if (container.contains(renderer.domElement)) {
    container.removeChild(renderer.domElement);
  }
}

function disposeMaterial(mat: THREE.Material) {
  for (const key of Object.keys(mat)) {
    const value = (mat as unknown as Record<string, unknown>)[key];
    if (value && typeof value === "object" && "isTexture" in value) {
      (value as THREE.Texture).dispose();
    }
  }
  mat.dispose();
}
