import React, { useState, useRef, useEffect } from 'react';
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
    <div className="flex flex-col h-screen max-w-5xl mx-auto bg-panel border-x-2 border-neutral-800 font-mono text-phosphor selection:bg-hazard selection:text-black">
      {/* Top Telemetry Bar */}
      <div className="bg-black border-b-2 border-neutral-800 p-2.5 px-4 flex justify-between items-center text-xs tracking-wider uppercase">
        <div className="flex items-center gap-3">
          <span className="text-hazard font-extrabold">// SECTOR LINK:</span>
          <span className="bg-neutral-900 border border-neutral-700 px-2 py-0.5 font-bold text-white font-mono">{roomId}</span>
          <button
            onClick={handleCopyRoomCode}
            className="text-[10px] bg-neutral-800 hover:bg-neutral-700 border border-neutral-600 px-2 py-0.5 text-neutral-300 transition-colors"
          >
            {copied ? '[ COPIED ]' : '[ COPY CODE ]'}
          </button>
        </div>

        <div className="flex items-center gap-4 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 ${
              status === 'connected' ? 'bg-terminal animate-pulse' :
              status === 'connecting' ? 'bg-amber-500' : 'bg-hazard'
            }`} />
            <span className="text-neutral-300 font-bold">{status}</span>
          </div>

          <span className="text-neutral-600">|</span>

          <div className="text-neutral-400">
            OPERATOR: <strong className="text-white">{userId}</strong>
          </div>

          <button
            onClick={onLeave}
            className="bg-neutral-900 hover:bg-hazard hover:text-black border border-neutral-700 text-neutral-400 font-bold px-2.5 py-1 text-[10px] transition-colors"
          >
            [ LEAVE SECTOR ]
          </button>
        </div>
      </div>

      {/* Context Isolation Banner */}
      <div className="bg-neutral-950 border-b border-neutral-800 p-2 px-4 text-[10px] text-neutral-400 flex justify-between items-center uppercase tracking-widest font-mono">
        <div className="flex items-center gap-2">
          <span className="text-hazard font-bold">/// CONTEXT_ISOLATION:</span>
          <span>PER-USER AGENT THREADS PARTITIONED IN SQLITE</span>
        </div>
        <div className="text-neutral-600">
          THREAD_ID: [{roomId} // {userId}]
        </div>
      </div>

      {/* Messages Feed Container */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-2 bg-crt">
        {status === 'error' && (
          <div className="p-3 bg-neutral-900 border-2 border-hazard text-hazard text-xs uppercase font-mono mb-4 flex items-center justify-between">
            <span>[ ERROR // LINK DISRUPTED — ATTEMPTING RECONNECT ]</span>
            <span className="animate-ping">///</span>
          </div>
        )}

        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4 my-12 border-2 border-dashed border-neutral-800 bg-black/50">
            <div className="text-2xl text-neutral-600 font-extrabold">
              [ NO TRANSMISSIONS IN SECTOR ]
            </div>
            <div className="max-w-md space-y-2 text-xs text-neutral-400 uppercase">
              <p>
                SHARE SECTOR CODE <span className="bg-neutral-800 text-white px-2 py-0.5 font-bold border border-neutral-700">{roomId}</span> WITH ANOTHER OPERATOR TO BEGIN MULTIPLAYER CHAT.
              </p>
              <p className="text-hazard pt-2">
                &gt;&gt; TYPE <span className="underline font-bold">@agent</span> IN YOUR TRANSMISSION TO INSTRUCT THE AI PARTICIPANT.
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} currentUserId={userId} />
          ))
        )}

        {/* Thinking State Indicators */}
        {thinkingUsers.map((thinkingUser) => (
          <div key={thinkingUser} className="my-3 p-3 bg-black border-2 border-hazard text-hazard font-mono text-xs uppercase flex items-center gap-3 w-fit">
            <span className="w-2.5 h-2.5 bg-hazard animate-ping"></span>
            <span>[ TELEMETRY // AGENT IS COMPUTING RESPONSE FOR @{thinkingUser} ... ]</span>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Control Bar */}
      <div className="p-4 bg-black border-t-2 border-neutral-800">
        <form onSubmit={handleSend} className="space-y-2">
          <div className="flex justify-between text-[10px] text-neutral-500 uppercase font-mono">
            <span>&gt;&gt; TRANSMISSION BUFFER</span>
            <span>KEYBOARD TRIGGER: @agent &lt;PROMPT&gt;</span>
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={`TYPE TRANSMISSION... (MENTION @agent TO QUERY AI)`}
              disabled={status !== 'connected'}
              className="flex-1 bg-neutral-950 border border-neutral-700 focus:border-hazard p-3 text-xs md:text-sm text-white placeholder-neutral-700 focus:outline-none uppercase font-mono disabled:opacity-40 transition-colors"
            />

            <button
              type="button"
              onClick={handleAddAgentTrigger}
              className="bg-neutral-900 hover:bg-neutral-800 text-hazard border border-neutral-700 hover:border-hazard px-3 text-xs font-bold uppercase transition-colors flex items-center gap-1"
              title="Append @agent prompt trigger"
            >
              <span>+ @agent</span>
            </button>

            <button
              type="submit"
              disabled={!inputText.trim() || status !== 'connected'}
              className="bg-hazard hover:bg-red-600 disabled:opacity-40 text-black font-extrabold px-5 text-xs uppercase tracking-wider transition-all border border-hazard flex items-center gap-2"
            >
              <span>[ TRANSMIT ]</span>
              <span>&gt;&gt;</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
