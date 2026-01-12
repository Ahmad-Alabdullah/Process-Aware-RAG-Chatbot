"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchProcesses, fetchTasks, fetchRoles } from "@/lib/api/bpmn";
import type { ProcessOption, TaskOption, LaneOption } from "@/types";

export function useProcesses() {
  return useQuery<ProcessOption[], Error>({
    queryKey: ["processes"],
    queryFn: fetchProcesses,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

export function useTasks(processId: string | null) {
  return useQuery<TaskOption[], Error>({
    queryKey: ["tasks", processId],
    queryFn: () => (processId ? fetchTasks(processId) : Promise.resolve([])),
    enabled: !!processId,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

export function useRoles(processId: string | null) {
  return useQuery<LaneOption[], Error>({
    queryKey: ["roles", processId],
    queryFn: () => (processId ? fetchRoles(processId) : Promise.resolve([])),
    enabled: !!processId,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}
