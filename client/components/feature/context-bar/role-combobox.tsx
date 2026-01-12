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
import { useRoles } from "@/hooks/use-processes";
import type { LaneOption } from "@/types";

interface RoleComboboxProps {
  processId: string | null;
  value: LaneOption | null;
  onSelect: (role: LaneOption | null) => void;
  disabled?: boolean;
}

export function RoleCombobox({
  processId,
  value,
  onSelect,
  disabled = false,
}: RoleComboboxProps) {
  const [open, setOpen] = useState(false);
  const { data: roles = [], isLoading } = useRoles(processId);

  if (disabled) {
    return (
      <Button
        variant="outline"
        disabled
        className="w-[180px] justify-between opacity-50"
      >
        <span className="text-muted-foreground">Rolle wählen...</span>
        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </Button>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          aria-label="Rolle auswählen"
          disabled={!processId}
          className="w-[180px] justify-between"
        >
          {value ? (
            <span className="truncate">{value.name}</span>
          ) : (
            <span className="text-muted-foreground">Rolle wählen...</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[220px] p-0" align="start">
        <Command>
          <CommandInput placeholder="Rolle suchen..." />
          <CommandList>
            <CommandEmpty>
              {isLoading ? "Laden..." : "Keine Rollen gefunden."}
            </CommandEmpty>
            <CommandGroup>
              {roles.map((role) => (
                <CommandItem
                  key={role.id}
                  value={role.name}
                  onSelect={() => {
                    onSelect(role.id === value?.id ? null : role);
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value?.id === role.id ? "opacity-100" : "opacity-0"
                    )}
                  />
                  <div className="flex flex-col">
                    <span className="truncate">{role.name}</span>
                    {role.task_count !== undefined && (
                      <span className="text-xs text-muted-foreground">
                        {role.task_count} {role.task_count === 1 ? "Aufgabe" : "Aufgaben"}
                      </span>
                    )}
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
