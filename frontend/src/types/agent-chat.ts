export type MessageRole = "user" | "assistant" | "system" | "tool";

export type ToolCallStatus = "pending" | "running" | "completed" | "failed";

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  status: ToolCallStatus;
  result?: unknown;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  tool_calls?: ToolCall[];
  created_at: string;
}

export type StreamChunkType =
  | "text_delta"
  | "tool_call_start"
  | "tool_call_delta"
  | "tool_call_end"
  | "message_start"
  | "message_end"
  | "error";

export interface StreamChunk {
  type: StreamChunkType;
  message_id?: string;
  content?: string;
  tool_call?: Partial<ToolCall>;
  error?: string;
}
