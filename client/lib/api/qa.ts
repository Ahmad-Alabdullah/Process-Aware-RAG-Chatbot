import { apiClient } from "./client";
import type { AskRequest, AskResponse } from "@/types";

export async function askQuestion(request: AskRequest): Promise<AskResponse> {
  return apiClient.post<AskResponse>("/api/qa/ask", request);
}
