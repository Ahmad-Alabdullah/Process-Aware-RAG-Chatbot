"use client";

import { Check, ChevronsUpDown } from "lucide-react";
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
import { useTasks } from "@/hooks/use-processes";
import type { TaskOption } from "@/types";

interface TaskComboboxProps {
  processId: string | null;
  value: TaskOption | null;
  onSelect: (task: TaskOption | null) => void;
  disabled?: boolean;
}

export function TaskCombobox({
  processId,
  value,
  onSelect,
  disabled = false,
}: TaskComboboxProps) {
  const [open, setOpen] = useState(false);
  const { data: tasks = [], isLoading } = useTasks(processId);

  if (disabled) {
    return (
      <div className="flex flex-col gap-1">
        <Button
          variant="outline"
          disabled
          className="w-[200px] justify-between opacity-50"
        >
          <span className="text-muted-foreground">Schritt wählen...</span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
        {/* <span className="text-xs text-muted-foreground">
          Kein BPMN-Modell verfügbar
        </span> */}
      </div>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          aria-label="Schritt auswählen"
          disabled={!processId}
          className="w-[200px] justify-between"
        >
          {value ? (
            <span className="truncate">{value.task_name}</span>
          ) : (
            <span className="text-muted-foreground">Schritt wählen...</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[250px] p-0" align="start">
        <Command>
          <CommandInput placeholder="Schritt suchen..." />
          <CommandList>
            <CommandEmpty>
              {isLoading ? "Laden..." : "Keine Schritte gefunden."}
            </CommandEmpty>
            <CommandGroup>
              {tasks.map((task, index) => (
                <CommandItem
                  key={`${task.task_id}-${index}`}
                  value={task.task_name}
                  onSelect={() => {
                    onSelect(task.task_id === value?.task_id ? null : task);
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value?.task_id === task.task_id
                        ? "opacity-100"
                        : "opacity-0"
                    )}
                  />
                  <span className="truncate">{task.task_name}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
