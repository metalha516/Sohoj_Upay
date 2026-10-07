"use client";

import React, { useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, useMotionValue, useSpring } from "framer-motion";

interface MagneticButtonProps {
  children: React.ReactNode;
  icon?: React.ReactNode;
  variant?: "primary" | "secondary" | "ghost";
  className?: string;
  href?: string;
  onClick?: (e: React.MouseEvent<HTMLElement>) => void;
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
}

export function MagneticButton({
  children,
  icon,
  variant = "primary",
  className = "",
  href,
  onClick,
  ...props
}: MagneticButtonProps) {
  const ref = useRef<HTMLInputElement & HTMLAnchorElement & HTMLButtonElement>(null);
  const router = useRouter();

  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const iconX = useMotionValue(0);
  const iconY = useMotionValue(0);

  const springConfig = { damping: 18, stiffness: 320, mass: 0.1 };
  const smoothX = useSpring(x, springConfig);
  const smoothY = useSpring(y, springConfig);
  const smoothIconX = useSpring(iconX, springConfig);
  const smoothIconY = useSpring(iconY, springConfig);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!ref.current) return;
    const { left, top, width, height } = ref.current.getBoundingClientRect();
    const centerX = left + width / 2;
    const centerY = top + height / 2;

    const deltaX = (e.clientX - centerX) * 0.3;
    const deltaY = (e.clientY - centerY) * 0.3;

    x.set(deltaX);
    y.set(deltaY);
    iconX.set(deltaX * 1.5);
    iconY.set(deltaY * 1.5);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
    iconX.set(0);
    iconY.set(0);
  };

  const variantStyles = {
    primary:
      "bg-upay-500 text-navy-950 font-black shadow-lg shadow-upay-500/25 hover:bg-upay-400 border border-upay-400/40",
    secondary:
      "bg-navy-900/90 text-white font-bold hover:bg-navy-800 border border-navy-700/80 shadow-md",
    ghost:
      "bg-navy-950/60 text-slate-300 font-semibold hover:text-white hover:bg-navy-900 border border-navy-800/80",
  };

  const combinedClassName = `group relative inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-2xl text-sm transition-colors select-none cursor-pointer ${variantStyles[variant]} ${className}`;

  const content = (
    <>
      <span>{children}</span>
      {icon && (
        <motion.span
          style={{ x: smoothIconX, y: smoothIconY }}
          className="flex h-6 w-6 items-center justify-center rounded-full transition-transform group-hover:scale-105"
        >
          {icon}
        </motion.span>
      )}
    </>
  );

  if (href) {
    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
      if (onClick) onClick(e);
      if (href.startsWith("#")) {
        e.preventDefault();
        const element = document.querySelector(href);
        if (element) {
          element.scrollIntoView({ behavior: "smooth" });
        }
      } else {
        e.preventDefault();
        router.push(href);
      }
    };

    return (
      <motion.a
        ref={ref}
        href={href}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        style={{ x: smoothX, y: smoothY }}
        whileTap={{ scale: 0.96 }}
        className={combinedClassName}
      >
        {content}
      </motion.a>
    );
  }

  return (
    <motion.button
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick as any}
      style={{ x: smoothX, y: smoothY }}
      whileTap={{ scale: 0.96 }}
      className={combinedClassName}
    >
      {content}
    </motion.button>
  );
}

