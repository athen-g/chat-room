import React, { useState } from 'react';
import { MessageSquare, Users, Sparkles, ArrowRight } from 'lucide-react';

interface JoinFormProps {
  onJoin: (username: string, roomId: string) => void;
}

export const JoinForm: React.FC<JoinFormProps> = ({ onJoin }) => {
  const [username, setUsername] = useState('');
  const [roomId, setRoomId] = useState('demo-room');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim() && roomId.trim()) {
      onJoin(username.trim(), roomId.trim());
    }
  };

  const handleQuickDemo = () => {
    const randomUser = `User_${Math.floor(1000 + Math.random() * 9000)}`;
    onJoin(randomUser, 'demo-room');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header decoration */}
        <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-6 text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-white/10 backdrop-blur-md mb-3 border border-white/20">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">AI Multiplayer Room</h1>
          <p className="text-indigo-100 text-sm mt-1">Real-time chat with per-user AI context isolation</p>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Your Display Name
            </label>
            <div className="relative">
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. Alice"
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
              <Users className="absolute right-3.5 top-3.5 w-5 h-5 text-slate-500 pointer-events-none" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Room Code
            </label>
            <div className="relative">
              <input
                type="text"
                required
                value={roomId}
                onChange={(e) => setRoomId(e.target.value)}
                placeholder="e.g. demo-room"
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all font-mono"
              />
              <MessageSquare className="absolute right-3.5 top-3.5 w-5 h-5 text-slate-500 pointer-events-none" />
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3 rounded-xl transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 group"
          >
            <span>Enter Room</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-900 px-2 text-slate-500">Or quick start</span>
            </div>
          </div>

          <button
            type="button"
            onClick={handleQuickDemo}
            className="w-full bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-300 hover:text-white font-medium py-2.5 rounded-xl transition-all text-sm"
          >
            Join as Random User in 'demo-room'
          </button>
        </form>
      </div>
    </div>
  );
};
