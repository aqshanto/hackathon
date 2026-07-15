"use client";
import React, { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

interface CostChartProps {
  simTime: string;
  savedCost: number;
}

export default function CostChart({ simTime, savedCost }: CostChartProps) {
  const [labels, setLabels] = useState<string[]>([]);
  const [legacyData, setLegacyData] = useState<number[]>([]);
  const [aiData, setAiData] = useState<number[]>([]);

  useEffect(() => {
    if (!simTime || simTime === "00:00:00") return;

    // প্রতি ৩ সেকেন্ড পর পর গ্রাফে পয়েন্ট যোগ হবে
    const timeLabel = simTime.substring(0, 5); // HH:MM
    setLabels((prev) => {
      if (prev[prev.length - 1] === timeLabel) return prev;
      const next = [...prev, timeLabel];
      return next.length > 20 ? next.slice(1) : next;
    });

    setLegacyData((prev) => {
      if (labels[labels.length - 1] === timeLabel) return prev;
      const nextVal = (prev[prev.length - 1] || 0) + 0.08;
      const next = [...prev, Number(nextVal.toFixed(2))];
      return next.length > 20 ? next.slice(1) : next;
    });

    setAiData((prev) => {
      if (labels[labels.length - 1] === timeLabel) return prev;
      const nextVal = (prev[prev.length - 1] || 0) + 0.03;
      const next = [...prev, Number(nextVal.toFixed(2))];
      return next.length > 20 ? next.slice(1) : next;
    });
  }, [simTime]);

  const data = {
    labels,
    datasets: [
      {
        label: "Legacy Cost ($)",
        data: legacyData,
        borderColor: "#ef4444",
        backgroundColor: "#ef4444",
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.3,
      },
      {
        label: "AI Cost ($)",
        data: aiData,
        borderColor: "#10b981",
        backgroundColor: "#10b981",
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: "top" as const,
        labels: { color: "#cbd5e1", font: { size: 10 } },
      },
    },
    scales: {
      x: {
        grid: { color: "rgba(51, 65, 85, 0.4)" },
        ticks: { color: "#94a3b8", font: { size: 10 } },
      },
      y: {
        grid: { color: "rgba(51, 65, 85, 0.4)" },
        ticks: { color: "#94a3b8", font: { size: 10 } },
      },
    },
    animation: { duration: 0 },
  };

  return (
    <div className="glass-panel p-5 rounded-xl border-l-4 border-l-emerald-500 pointer-events-auto">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="text-white font-semibold text-sm">Cost Analytics</h3>
          <p className="text-[10px] text-slate-400">
            Legacy vs AI Optimized ($)
          </p>
        </div>
        <div className="text-right">
          <p className="text-[10px] text-emerald-400 uppercase font-bold tracking-wider">
            Total Saved
          </p>
          <p className="text-xl font-bold text-emerald-400 metric-value">
            ${savedCost.toFixed(2)}
          </p>
        </div>
      </div>
      <div className="w-full h-[160px] mt-2">
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
