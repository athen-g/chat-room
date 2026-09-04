import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, LogOut, Copy, Check, Bot, AlertCircle } from 'lucide-react';
import { useRoomSocket } from '../hooks/useRoomSocket';
import { MessageBubble } from './MessageBubble';

interface ChatRoomProps {
  roomId: string;
  userId: string;
  onLeave: () => void;
}

export const ChatRoom: React.FC<ChatRoomProps> = ({ roomId, userId, onLeave }) => {
  const { messages, status, thinkingUsers, sendMessage } = useRoomSocket(roomId, userId);
  const [inputText, setInputText] = useState('');
  const [copied, setCopied] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, thinkingUsers]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    sendMessage(inputText);
    setInputText('');
  };

  const handleAddAgentTrigger = () => {
    if (!inputText.includes('@agent')) {
      setInputText((prev) => (prev ? `@agent ${prev}` : '@agent '));
    }
  };

  const handleCopyRoomCode = () => {
    navigator.clipboard.writeText(roomId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-slate-900 border-x border-slate-800 shadow-2xl">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-lg text-white font-mono">{roomId}</h2>
              <button
                onClick={handleCopyRoomCode}
                className="p-1 text-slate-400 hover:text-white transition-colors"
                title="Copy Room Code"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className={`w-2 h-2 rounded-full ${
                status === 'connected' ? 'bg-emerald-500 animate-pulse' :
                status === 'connecting' ? 'bg-amber-500' : 'bg-rose-500'
              }`} />
              <span className="text-slate-400 capitalize">{status}</span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-400">User: <strong className="text-indigo-400">{userId}</strong></span>
            </div>
          </div>
        </div>

        <button
          onClick={onLeave}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-rose-400 bg-slate-800 hover:bg-rose-950/30 border border-slate-700 hover:border-rose-800/50 rounded-lg transition-all"
        >
          <LogOut className="w-4 h-4" />
          <span>Leave</span>
        </button>
      </header>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-6 space-y-2">
        {status === 'error' && (
          <div className="p-3 bg-rose-950/40 border border-rose-800/50 rounded-xl text-rose-300 text-sm flex items-center gap-2 my-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>Connection error. Attempting to reconnect...</span>
          </div>
        )}

        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4 my-12">
            <div className="w-16 h-16 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400">
              <Bot className="w-8 h-8 text-indigo-400" />
            </div>
            <div className="max-w-md space-y-1">
              <h3 className="text-lg font-semibold text-slate-200">Room is empty & quiet</h3>
              <p className="text-sm text-slate-400">
                Share room code <code className="bg-slate-800 px-1.5 py-0.5 rounded text-indigo-300 font-mono">{roomId}</code> with another user to chat live!
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Tip: Type <span className="text-purple-400 font-semibold">@agent</span> in your message to prompt the AI assistant.
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} currentUserId={userId} />
          ))
        )}

        {/* Thinking Indicator */}
        {thinkingUsers.map((thinkingUser) => (
          <div key={thinkingUser} className="flex items-center gap-2 my-2 text-xs text-purple-300 bg-purple-950/40 border border-purple-800/40 rounded-xl px-4 py-2 w-fit">
            <Bot className="w-4 h-4 text-purple-400 animate-spin" />
            <span>Agent is thinking for <strong>@{thinkingUser}</strong>...</span>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <footer className="p-4 bg-slate-900 border-t border-slate-800">
        <form onSubmit={handleSend} className="flex flex-col gap-2">
          <div className="relative flex items-center">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={`Type a message... (use @agent to address AI)`}
              disabled={status !== 'connected'}
              className="w-full bg-slate-800 border border-slate-700 focus:border-indigo-500 rounded-xl pl-4 pr-24 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50 transition-all"
            />

            <div className="absolute right-2 flex items-center gap-1.5">
              <button
                type="button"
                onClick={handleAddAgentTrigger}
                title="Add @agent to prompt"
                className="px-2.5 py-1 text-xs font-semibold bg-purple-900/60 hover:bg-purple-800 text-purple-300 border border-purple-700/50 rounded-lg transition-all flex items-center gap-1"
              >
                <Sparkles className="w-3 h-3" />
                <span>@agent</span>
              </button>

              <button
                type="submit"
                disabled={!inputText.trim() || status !== 'connected'}
                className="p-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg transition-all shadow-md shadow-indigo-600/20 flex items-center justify-center"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </form>
      </footer>
    </div>
  );
};
