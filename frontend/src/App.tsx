import { useState } from 'react';
import { JoinForm } from './components/JoinForm';
import { ChatRoom } from './components/ChatRoom';

export function App() {
  const [session, setSession] = useState<{ username: string; roomId: string } | null>(null);

  if (!session) {
    return (
      <JoinForm
        onJoin={(username, roomId) => {
          setSession({ username, roomId });
        }}
      />
    );
  }

  return (
    <ChatRoom
      roomId={session.roomId}
      userId={session.username}
      onLeave={() => setSession(null)}
    />
  );
}

export default App;
