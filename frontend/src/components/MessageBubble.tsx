import React from 'react';
import { Bot, User, CornerDownRight } from 'lucide-react';
import { ChatMessage } from '../types';

interface MessageBubbleProps {
  message: ChatMessage;
  currentUserId: string;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, currentUserId }) => {
  const isSelf = message.user_id === currentUserId;
  const isAgent = message.role === 'agent' || message.user_id === 'Agent';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center my-3">
        <div className="bg-amber-950/40 border border-amber-800/50 text-amber-300 text-xs px-3 py-1.5 rounded-full">
          {message.content}
        </div>
      </div>
    );
  }

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div className={`flex gap-3 my-3 ${isSelf ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className="flex-shrink-0">
        {isAgent ? (
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-600 to-pink-500 flex items-center justify-center text-white shadow-md shadow-purple-500/20">
            <Bot className="w-5 h-5" />
          </div>
        ) : (
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
            isSelf ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300'
          }`}>
            <User className="w-4 h-4" />
          </div>
        )}
      </div>

      {/* Bubble Content */}
      <div className={`max-w-[75%] space-y-1 ${isSelf ? 'items-end' : 'items-start'}`}>
        {/* Username Header */}
        <div className={`flex items-center gap-2 text-xs text-slate-400 ${isSelf ? 'justify-end' : 'justify-start'}`}>
          <span className="font-semibold text-slate-300">
            {isSelf ? 'You' : message.user_id}
          </span>
          {isAgent && message.target_user_id && (
            <span className="inline-flex items-center gap-1 text-[11px] bg-purple-950/80 text-purple-300 border border-purple-800/50 px-2 py-0.5 rounded-md">
              <CornerDownRight className="w-3 h-3" />
              Replying to @{message.target_user_id}
            </span>
          )}
          <span className="text-[10px] text-slate-500">{formatTime(message.created_at)}</span>
        </div>

        {/* Text Body */}
        <div
          className={`p-3.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap shadow-md ${
            isAgent
              ? 'bg-slate-800/90 border border-purple-500/30 text-purple-100 rounded-tl-xs'
              : isSelf
              ? 'bg-indigo-600 text-white rounded-tr-xs'
              : 'bg-slate-800 border border-slate-700 text-slate-200 rounded-tl-xs'
          }`}
        >
          {message.content}
        </div>
      </div>
    </div>
  );
};
