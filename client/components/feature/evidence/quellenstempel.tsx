"use client";

import { useMemo, useState } from "react";
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

  // Group and deduplicate sources by filename
  const sources = useMemo(() => {
    if (!evidence || evidence.length === 0) return [];
    
    const byFile = new Map<string, { title: string; type: "DOC" | "BPMN" }>();
    
    for (const chunk of evidence) {
      const sourceType = chunk.metadata?.source_type as string | undefined;
      const isBpmn =
        sourceType === "bpmn" ||
        sourceType === "BPMN" ||
        chunk.chunk_id?.includes("bpmn_");
      
      // Use filename as key for deduplication
      const filename = 
        (chunk.metadata?.filename as string) ||
        (chunk.metadata?.title as string) ||
        chunk.chunk_id ||
        "Unbekannte Quelle";
      
      // Skip if already added (deduplication)
      if (byFile.has(filename)) continue;
      
      byFile.set(filename, {
        title: filename,
        type: isBpmn ? "BPMN" : "DOC",
      });
    }
    
    // Convert to array and sort (BPMN first, then DOCs)
    return Array.from(byFile.entries())
      .map(([id, data]) => ({ id, ...data }))
      .sort((a, b) => (a.type === "BPMN" ? -1 : b.type === "BPMN" ? 1 : 0));
  }, [evidence]);

  // Early return if no sources after deduplication
  if (sources.length === 0) return null;

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
