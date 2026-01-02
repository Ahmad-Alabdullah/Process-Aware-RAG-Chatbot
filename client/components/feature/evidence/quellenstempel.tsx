"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, FileText, Workflow } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { EvidenceChunk } from "@/types";

interface QuellenstempelProps {
  evidence: EvidenceChunk[];
  defaultOpen?: boolean;
}

export function Quellenstempel({
  evidence,
  defaultOpen = false,
}: QuellenstempelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (!evidence || evidence.length === 0) return null;

  // Derive source info from evidence chunks
  const sources = evidence.slice(0, 5).map((chunk, index) => {
    // Try to extract source type and locator from metadata or chunk_id
    const sourceType = chunk.metadata?.source_type as string | undefined;
    const isBpmn =
      sourceType === "bpmn" ||
      sourceType === "BPMN" ||
      chunk.chunk_id?.includes("bpmn") ||
      chunk.chunk_id?.includes("node_");

    const title =
      (chunk.metadata?.title as string) ||
      (chunk.metadata?.filename as string) ||
      chunk.chunk_id ||
      `Quelle ${index + 1}`;

    const locator =
      (chunk.metadata?.page as string) ||
      (chunk.metadata?.section as string) ||
      chunk.chunk_id?.split("_").slice(-1)[0];

    return {
      id: chunk.chunk_id || `source-${index}`,
      title,
      type: isBpmn ? ("BPMN" as const) : ("DOC" as const),
      locator,
    };
  });

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="gap-2 h-auto py-1 px-2 text-xs text-muted-foreground hover:text-foreground"
        >
          <span>Quellen ({sources.length})</span>
          {isOpen ? (
            <ChevronUp className="h-3 w-3" />
          ) : (
            <ChevronDown className="h-3 w-3" />
          )}
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 space-y-2">
        {sources.map((source) => (
          <div
            key={source.id}
            className="flex items-start gap-2 text-xs text-muted-foreground"
          >
            {source.type === "BPMN" ? (
              <Workflow className="h-3.5 w-3.5 mt-0.5 shrink-0" />
            ) : (
              <FileText className="h-3.5 w-3.5 mt-0.5 shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <span className="truncate">{source.title}</span>
              {source.locator && (
                <span className="opacity-70"> · {source.locator}</span>
              )}
            </div>
            <Badge
              variant="outline"
              className={
                source.type === "BPMN"
                  ? "bg-purple-500/20 text-purple-400 border-purple-500/30"
                  : "bg-blue-500/20 text-blue-400 border-blue-500/30"
              }
            >
              {source.type}
            </Badge>
          </div>
        ))}
      </CollapsibleContent>
    </Collapsible>
  );
}
