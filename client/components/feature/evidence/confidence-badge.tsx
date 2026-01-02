"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ConfidenceInfo } from "@/types";

interface ConfidenceBadgeProps {
  confidence: ConfidenceInfo;
  showScore?: boolean;
}

export function ConfidenceBadge({
  confidence,
  showScore = true,
}: ConfidenceBadgeProps) {
  const colorClasses = {
    green: "bg-green-500/20 text-green-400 border-green-500/30",
    amber: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    red: "bg-red-500/20 text-red-400 border-red-500/30",
  };

  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1.5 font-medium",
        colorClasses[confidence.color as keyof typeof colorClasses] ||
          colorClasses.amber
      )}
    >
      <span
        className={cn(
          "h-2 w-2 rounded-full",
          confidence.color === "green" && "bg-green-400",
          confidence.color === "amber" && "bg-amber-400",
          confidence.color === "red" && "bg-red-400"
        )}
      />
      {confidence.label}
      {showScore && (
        <span className="opacity-70">
          ({(confidence.score * 100).toFixed(0)}%)
        </span>
      )}
    </Badge>
  );
}
