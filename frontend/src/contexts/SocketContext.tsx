import { createContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { Socket } from 'socket.io-client';
import { connectSocket, disconnectSocket, getSocket } from '@/services/socket';

export interface SocketContextValue {
  socket: Socket;
  connected: boolean;
  joinTurfRoom: (turfId: string) => void;
  joinSlotRoom: (turfSportId: string, date: string) => void;
  lockSlot: (slotId: string, playerId: string) => void;
  unlockSlot: (slotId: string, playerId: string) => void;
}

export const SocketContext = createContext<SocketContextValue | null>(null);

export function SocketProvider({ children }: { children: ReactNode }): JSX.Element {
  const socket = useMemo(() => getSocket(), []);
  const [connected, setConnected] = useState<boolean>(socket.connected);

  useEffect(() => {
    const onConnect = (): void => setConnected(true);
    const onDisconnect = (): void => setConnected(false);
    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    connectSocket();
    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      disconnectSocket();
    };
  }, [socket]);

  const value = useMemo<SocketContextValue>(
    () => ({
      socket,
      connected,
      joinTurfRoom: (turfId) => socket.emit('join_turf_room', { turf_id: turfId }),
      joinSlotRoom: (turfSportId, date) =>
        socket.emit('join_slot_room', { turf_sport_id: turfSportId, date }),
      lockSlot: (slotId, playerId) => socket.emit('lock_slot', { slot_id: slotId, player_id: playerId }),
      unlockSlot: (slotId, playerId) =>
        socket.emit('unlock_slot', { slot_id: slotId, player_id: playerId }),
    }),
    [socket, connected],
  );

  return <SocketContext.Provider value={value}>{children}</SocketContext.Provider>;
}
