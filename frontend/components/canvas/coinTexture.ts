import * as THREE from "three";

export function createTakaCoinTexture(): THREE.CanvasTexture {
  const size = 512;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d")!;

  // Background base
  ctx.fillStyle = "#808080";
  ctx.fillRect(0, 0, size, size);

  const center = size / 2;

  // Outer milled coin rim ring
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 14;
  ctx.beginPath();
  ctx.arc(center, center, center - 20, 0, Math.PI * 2);
  ctx.stroke();

  // Decorative inner beaded circle
  ctx.fillStyle = "#ffffff";
  const beadCount = 48;
  const beadRadius = center - 38;
  for (let i = 0; i < beadCount; i++) {
    const angle = (i / beadCount) * Math.PI * 2;
    const bx = center + Math.cos(angle) * beadRadius;
    const by = center + Math.sin(angle) * beadRadius;
    ctx.beginPath();
    ctx.arc(bx, by, 3.5, 0, Math.PI * 2);
    ctx.fill();
  }

  // Central embossed Bengali Taka symbol "৳"
  ctx.fillStyle = "#ffffff";
  ctx.font = 'bold 220px "Noto Sans Bengali", "Segoe UI", sans-serif';
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("৳", center, center - 12);

  // Curved brand text: SOHOJ • UPAY MFS
  ctx.font = "bold 24px sans-serif";
  ctx.letterSpacing = "6px";
  ctx.fillText("SOHOJ  •  UPAY MFS", center, center + 140);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  return texture;
}
