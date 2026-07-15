"use client";
import React, { useEffect, useRef } from "react";
import { TelemetryData } from "@/types";

interface SimulationCanvasProps {
  telemetry: TelemetryData | null;
}

export default function SimulationCanvas({ telemetry }: SimulationCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const particlesRef = useRef<any[]>([]);

  // WebSocket-এর ঘনঘন রি-রেন্ডার থেকে অ্যানিমেশন লুপকে মুক্ত রাখতে useRef ব্যবহার করা হচ্ছে
  const telemetryRef = useRef<TelemetryData | null>(null);

  useEffect(() => {
    telemetryRef.current = telemetry;
  }, [telemetry]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    // পার্টিকেল জেনারেটর (লাল ও নীল গ্লোয়িং ট্রাফিক কণা তৈরি করে)
    const spawnParticle = () => {
      const currentTelemetry = telemetryRef.current;
      const isSurge = currentTelemetry?.surge_active || false;
      const isAi = currentTelemetry?.ai_enabled ?? true;
      const nodes = currentTelemetry?.nodes || [];

      // লাল (Heavy Task) নাকি নীল (Light Task) হবে তা নির্ধারণ
      const isHeavy = Math.random() < (isSurge ? 0.4 : 0.25);
      const W = canvas.width;
      const H = canvas.height;

      const srcX = 380;
      const srcY = H * 0.45;
      const orchX = W / 2;
      const orchY = H * 0.45;
      const nodeX = W - 350;

      // ৩টি নোডের ওয়াই-অক্ষ (Y-axis) পজিশন
      const nodeYs = [orchY - 140, orchY, orchY + 140];

      // রাউটিং লজিক: AI অন থাকলে হেলদি নোডে যাবে, না থাকলে র‍্যান্ডম
      let destIdx = 0;
      if (isAi) {
        if (isHeavy) {
          destIdx =
            nodes[0]?.status === "healthy" && (nodes[0]?.load || 0) < 85
              ? 0
              : 2;
        } else {
          destIdx =
            nodes[1]?.status === "healthy" && (nodes[1]?.load || 0) < 85
              ? 1
              : 2;
        }
      } else {
        destIdx = Math.floor(Math.random() * 3);
      }

      particlesRef.current.push({
        x: srcX,
        y: srcY + (Math.random() * 40 - 20),
        target: "orch",
        progress: 0,
        speed: isSurge ? 0.035 : 0.018,
        color: isHeavy ? "#ef4444" : "#3b82f6",
        size: isHeavy ? 5.5 : 4,
        destX: nodeX,
        destY: nodeYs[destIdx] || orchY,
        startX: 0,
        startY: 0,
      });
    };

    // প্রতি ৮০ মিলিসেকেন্ড পর পর নতুন ট্রাফিক কণা তৈরি হবে
    const interval = setInterval(() => {
      const currentTelemetry = telemetryRef.current;
      const spawnChance = currentTelemetry?.surge_active ? 0.85 : 0.35;
      if (Math.random() < spawnChance) {
        spawnParticle();
      }
    }, 80);

    // ৬০ এফপিএস (60fps) রেন্ডার লুপ
    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const W = canvas.width;
      const H = canvas.height;
      const srcX = 380,
        srcY = H * 0.45,
        orchX = W / 2,
        orchY = H * 0.45,
        nodeX = W - 350;
      const nodeYs = [orchY - 140, orchY, orchY + 140];

      // সংযোগ রেখাগুলো আঁকা হচ্ছে
      ctx.lineWidth = 1;
      ctx.strokeStyle = "rgba(51, 65, 85, 0.4)";
      ctx.beginPath();
      ctx.moveTo(srcX, srcY);
      ctx.lineTo(orchX, orchY);
      ctx.stroke();

      nodeYs.forEach((ny) => {
        ctx.beginPath();
        ctx.moveTo(orchX, orchY);
        ctx.lineTo(nodeX, ny);
        ctx.stroke();
      });

      // প্রতিটি কণার মুভমেন্ট এবং গ্লো ইফেক্ট
      for (let i = particlesRef.current.length - 1; i >= 0; i--) {
        const p = particlesRef.current[i];
        p.progress += p.speed;

        if (p.target === "orch") {
          p.x = (1 - p.progress) * 380 + p.progress * orchX;
          p.y = (1 - p.progress) * p.y + p.progress * orchY;
          if (p.progress >= 1) {
            p.target = "node";
            p.progress = 0;
            p.startX = p.x;
            p.startY = p.y;
          }
        } else {
          p.x = (1 - p.progress) * p.startX + p.progress * p.destX;
          p.y = (1 - p.progress) * p.startY + p.progress * p.destY;
          if (p.progress >= 1) {
            particlesRef.current.splice(i, 1);
            continue;
          }
        }

        // কণা আঁকা এবং উজ্জ্বল গ্লো (Glow) ইফেক্ট দেওয়া হচ্ছে
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.shadowBlur = 15;
        ctx.shadowColor = p.color;
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      animationFrameId = requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationFrameId);
      clearInterval(interval);
    };
  }, []); // খালি অ্যারে দেওয়া হয়েছে যেন রি-রেন্ডারে অ্যানিমেশন বন্ধ না হয়!

  return (
    <canvas
      ref={canvasRef}
      className="absolute top-0 left-0 w-full h-full z-0 pointer-events-none"
    />
  );
}
