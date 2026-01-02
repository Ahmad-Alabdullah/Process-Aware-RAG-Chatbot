"use client";

import { Check, ChevronsUpDown, Search } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { useProcesses } from "@/hooks/use-processes";
import type { ProcessOption } from "@/types";

interface ProcessComboboxProps {
  value: ProcessOption | null;
  onSelect: (process: ProcessOption | null) => void;
}

export function ProcessCombobox({ value, onSelect }: ProcessComboboxProps) {
  const [open, setOpen] = useState(false);
  const { data: processes = [], isLoading } = useProcesses();

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          aria-label="Prozess auswählen"
          className="w-[220px] justify-between"
        >
          {value ? (
            <span className="truncate">{value.name}</span>
          ) : (
            <span className="text-muted-foreground">Prozess wählen...</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[350px] p-0" align="start">
        <Command>
          <CommandInput placeholder="Prozess suchen..." />
          <CommandList>
            <CommandEmpty>
              {isLoading ? "Laden..." : "Keine Prozesse gefunden."}
            </CommandEmpty>
            <CommandGroup>
              {processes.map((process) => (
                <CommandItem
                  key={process.id}
                  value={process.name}
                  onSelect={() => {
                    onSelect(process.id === value?.id ? null : process);
                    setOpen(false);
                  }}
                  className="flex items-center gap-3 py-2"
                >
                  <Check
                    className={cn(
                      "h-4 w-4 shrink-0",
                      value?.id === process.id ? "opacity-100" : "opacity-0"
                    )}
                  />
                  <span className="flex-1 truncate">{process.name}</span>
                  <Badge
                    variant="outline"
                    className={cn(
                      "shrink-0 text-xs",
                      process.has_model
                        ? "bg-green-500/20 text-green-400 border-green-500/30"
                        : "bg-blue-500/20 text-blue-400 border-blue-500/30"
                    )}
                  >
                    {process.has_model && process.doc_count 
                      ? "MODELED + DOCS" 
                      : process.has_model 
                        ? "MODELED" 
                        : "DOCS"}
                  </Badge>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
