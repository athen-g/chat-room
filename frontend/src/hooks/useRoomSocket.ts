import { useState, useEffect, useRef, useCallback } from 'react';
import { ChatMessage, SocketStatus } from '../types';

export function useRoomSocket(roomId: string, userId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<SocketStatus>('connecting');
  const [thinkingUsers, setThinkingUsers] = useState<Set<string>>(new Set());
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Initial load of room message history via REST API
  useEffect(() => {
    let isMounted = true;
    async function loadHistory() {
      try {
        const protocol = window.location.protocol;
        const host = window.location.host;
        const isDev = import.meta.env.DEV;
        const apiUrl = !isDev 
          ? `${protocol}//${host}/api/rooms/${roomId}/messages`
          : `http://localhost:8000/api/rooms/${roomId}/messages`;

        const resp = await fetch(apiUrl);
        if (resp.ok) {
          const data: ChatMessage[] = await resp.json();
          if (isMounted) {
            setMessages(data);
          }
        }
      } catch (err) {
        console.error('Failed to load message history:', err);
      }
    }

    if (roomId) {
      loadHistory();
    }

    return () => {
      isMounted = false;
    };
  }, [roomId]);

  // Connect WebSocket
  const connectSocket = useCallback(() => {
    if (!roomId || !userId) return;

    setStatus('connecting');

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    
    // In dev mode when running vite server on 5173, point directly to backend 8000
    const wsHost = host.includes('5173') ? 'localhost:8000' : host;
    const wsUrl = `${wsProtocol}//${wsHost}/ws/${encodeURIComponent(roomId)}/${encodeURIComponent(userId)}`;

    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'message') {
          const newMsg: ChatMessage = {
            id: data.id,
            room_id: data.room_id,
            user_id: data.user_id,
            role: data.role,
            content: data.content,
            created_at: data.created_at,
            target_user_id: data.target_user_id,
          };
          setMessages((prev) => {
            if (prev.some((m) => m.id === newMsg.id)) {
              return prev;
            }
            return [...prev, newMsg];
          });
        } else if (data.type === 'thinking') {
          const { user_id, is_thinking } = data;
          setThinkingUsers((prev) => {
            const next = new Set(prev);
            if (is_thinking) {
              next.add(user_id);
            } else {
              next.delete(user_id);
            }
            return next;
          });
        } else if (data.type === 'error') {
          console.error('Socket error received:', data.message);
          // Render error visibly in the room message log as a system-style notification
          const errSystemMsg: ChatMessage = {
            id: Date.now(),
            room_id: roomId,
            user_id: 'SYSTEM',
            role: 'system',
            content: data.message || 'An unexpected error occurred.',
            created_at: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, errSystemMsg]);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket payload:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setStatus('error');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setStatus('disconnected');
      // Attempt reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log('Attempting WebSocket reconnect...');
        connectSocket();
      }, 3000);
    };
  }, [roomId, userId]);

  useEffect(() => {
    connectSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connectSocket]);

  const sendMessage = useCallback((content: string) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'message', content }));
    } else {
      console.warn('Cannot send message, WebSocket is not connected.');
    }
  }, []);

  return {
    messages,
    status,
    thinkingUsers: Array.from(thinkingUsers),
    sendMessage,
  };
}
