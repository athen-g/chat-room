import React, { useState } from 'react';

interface JoinFormProps {
  onJoin: (username: string, roomId: string) => void;
}

export const JoinForm: React.FC<JoinFormProps> = ({ onJoin }) => {
  const [username, setUsername] = useState('');
  const [roomId, setRoomId] = useState('ALPHA-ROOM');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim() && roomId.trim()) {
      onJoin(username.trim(), roomId.trim());
    }
  };

  const handleQuickPreset = (name: string, room: string) => {
    onJoin(name, room);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-crt p-4 relative font-mono text-phosphor selection:bg-hazard selection:text-black">
      {/* Decorative Grid Lines */}
      <div className="absolute inset-0 grid grid-cols-6 pointer-events-none opacity-10 border-b border-neutral-700">
        <div className="border-r border-neutral-700"></div>
        <div className="border-r border-neutral-700"></div>
        <div className="border-r border-neutral-700"></div>
        <div className="border-r border-neutral-700"></div>
        <div className="border-r border-neutral-700"></div>
        <div></div>
      </div>

      <div className="w-full max-w-xl bg-panel border-2 border-neutral-700 shadow-2xl relative z-10">
        {/* Technical Header Strip */}
        <div className="bg-neutral-900 border-b-2 border-neutral-700 p-3 flex justify-between items-center text-xs tracking-wider">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-hazard inline-block animate-pulse"></span>
            <span className="font-bold text-hazard uppercase">SYS_AUTH // TELEMETRY TERMINAL v2.6</span>
          </div>
          <div className="text-neutral-500 font-mono">SEC_LEVEL: 04 // CLASSIFIED</div>
        </div>

        {/* Banner Section */}
        <div className="p-6 border-b border-neutral-800 bg-neutral-950">
          <div className="text-xs text-neutral-500 mb-1">/// INITIALIZING COMMUNICATION PROTOCOL ///</div>
          <h1 className="text-3xl font-extrabold text-white tracking-tighter uppercase mb-2">
            MULTIPLAYER AI ROOM
          </h1>
          <p className="text-xs text-neutral-400 leading-relaxed uppercase">
            STRICT PER-USER CONTEXT ISOLATION MATRIX. AGENT RESPONSES ARE ISOLATED AT STORAGE & EXECUTION LAYERS.
          </p>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Field 1: Operator ID */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs uppercase font-bold tracking-wider">
              <label className="text-neutral-300 flex items-center gap-1.5">
                <span className="text-hazard">&gt;&gt;</span> 01. OPERATOR IDENTIFIER (NAME)
              </label>
              <span className="text-neutral-500">[ REQ_ID ]</span>
            </div>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. OPERATOR_ALICE"
              className="w-full bg-black border border-neutral-700 focus:border-hazard p-3 text-sm text-white placeholder-neutral-700 focus:outline-none uppercase font-mono transition-colors"
            />
          </div>

          {/* Field 2: Room Code */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs uppercase font-bold tracking-wider">
              <label className="text-neutral-300 flex items-center gap-1.5">
                <span className="text-hazard">&gt;&gt;</span> 02. ROOM SECTOR CODE
              </label>
              <span className="text-neutral-500">[ SEC_ID ]</span>
            </div>
            <input
              type="text"
              required
              value={roomId}
              onChange={(e) => setRoomId(e.target.value)}
              placeholder="e.g. ALPHA-ROOM"
              className="w-full bg-black border border-neutral-700 focus:border-hazard p-3 text-sm text-white placeholder-neutral-700 focus:outline-none uppercase font-mono transition-colors"
            />
          </div>

          {/* Primary Action Button */}
          <button
            type="submit"
            className="w-full bg-hazard hover:bg-red-600 text-black font-extrabold py-3.5 px-4 text-sm uppercase tracking-wider transition-all flex items-center justify-center gap-2 border border-hazard"
          >
            <span>[ INITIALIZE LINK &amp; ENTER SECTOR ]</span>
            <span>&gt;&gt;&gt;</span>
          </button>

          {/* Technical Separator */}
          <div className="flex items-center my-6 text-xs text-neutral-600">
            <div className="flex-1 border-t border-neutral-800"></div>
            <span className="px-3 tracking-widest font-mono">// DUAL OPERATOR CONCURRENCY PRESETS //</span>
            <div className="flex-1 border-t border-neutral-800"></div>
          </div>

          {/* Quick Start Presets */}
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => handleQuickPreset('OPERATOR_ALICE', 'ALPHA-ROOM')}
              className="p-3 bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 hover:border-neutral-500 text-xs text-left text-neutral-300 transition-colors"
            >
              <div className="font-bold text-white mb-0.5">[ TAB 1: ALICE ]</div>
              <div className="text-[10px] text-neutral-500 uppercase">SECTOR: ALPHA-ROOM</div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickPreset('OPERATOR_BOB', 'ALPHA-ROOM')}
              className="p-3 bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 hover:border-neutral-500 text-xs text-left text-neutral-300 transition-colors"
            >
              <div className="font-bold text-white mb-0.5">[ TAB 2: BOB ]</div>
              <div className="text-[10px] text-neutral-500 uppercase">SECTOR: ALPHA-ROOM</div>
            </button>
          </div>
        </form>

        {/* Footer Technical Bar */}
        <div className="bg-neutral-950 border-t border-neutral-800 p-3 text-[10px] text-neutral-500 flex justify-between font-mono uppercase">
          <span>SQLITE_DB: ACTIVE</span>
          <span>WEBSOCKET: READY</span>
          <span>ISOLATION: ENFORCED</span>
        </div>
      </div>
    </div>
  );
};
