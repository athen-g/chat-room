export type MessageRole = 'human' | 'agent' | 'system';

export interface ChatMessage {
  id: number;
  room_id: string;
  user_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  target_user_id?: string | null;
}

export interface ThinkingState {
  user_id: string;
  is_thinking: boolean;
}

export type SocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';
