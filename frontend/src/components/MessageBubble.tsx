import React from 'react';
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
        <div className="bg-neutral-900 border border-hazard text-hazard font-mono text-xs px-3 py-1.5 uppercase tracking-wider flex items-center gap-2">
          <span className="w-2 h-2 bg-hazard animate-ping"></span>
          <span>[ SYS_EVENT // {message.content} ]</span>
        </div>
      </div>
    );
  }

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return '00:00:00';
    }
  };

  return (
    <div className={`my-4 flex flex-col font-mono ${isSelf ? 'items-end' : 'items-start'}`}>
      {/* Message Frame Container */}
      <div className={`max-w-[85%] border ${
        isAgent
          ? 'border-2 border-hazard bg-black'
          : isSelf
          ? 'border-l-4 border-l-hazard border-neutral-800 bg-neutral-900'
          : 'border-l-4 border-l-neutral-600 border-neutral-800 bg-neutral-950'
      } p-3 space-y-2`}>
        {/* Telemetry Header */}
        <div className="flex items-center justify-between gap-4 text-[11px] border-b border-neutral-800 pb-1.5 uppercase font-bold tracking-wider">
          <div className="flex items-center gap-2">
            <span className={`px-1.5 py-0.5 text-[10px] ${
              isAgent
                ? 'bg-hazard text-black font-extrabold'
                : isSelf
                ? 'bg-neutral-800 text-hazard'
                : 'bg-neutral-800 text-neutral-400'
            }`}>
              {isAgent ? '[ AGENT ]' : isSelf ? '[ YOU ]' : `[ ${message.user_id} ]`}
            </span>
            {isAgent && message.target_user_id && (
              <span className="text-neutral-400 text-[10px]">
                &gt;&gt; TARGET: <strong className="text-hazard">@{message.target_user_id}</strong>
              </span>
            )}
          </div>

          <span className="text-neutral-500 font-mono text-[10px]">
            T+{formatTime(message.created_at)}
          </span>
        </div>

        {/* Message Content */}
        <div className={`text-xs md:text-sm leading-relaxed whitespace-pre-wrap ${
          isAgent ? 'text-white font-mono' : 'text-neutral-200'
        }`}>
          {message.content}
        </div>

        {/* Footer Metadata */}
        <div className="text-[9px] text-neutral-600 pt-1 flex justify-between uppercase">
          <span>MSG_ID: #{message.id}</span>
          <span>ISOLATION_STATUS: ENFORCED</span>
        </div>
      </div>
    </div>
  );
};
