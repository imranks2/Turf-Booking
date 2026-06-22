import { create } from 'zustand';
import type { TurfCard } from '@/types';

export interface AppNotification {
  id: string;
  message: string;
  variant: 'info' | 'success' | 'error';
}

interface AppState {
  sidebarOpen: boolean;
  notifications: AppNotification[];
  currentTurf: TurfCard | null;
  toggleSidebar: () => void;
  setSidebar: (open: boolean) => void;
  pushNotification: (notification: AppNotification) => void;
  dismissNotification: (id: string) => void;
  setCurrentTurf: (turf: TurfCard | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  notifications: [],
  currentTurf: null,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebar: (open) => set({ sidebarOpen: open }),
  pushNotification: (notification) =>
    set((state) => ({ notifications: [...state.notifications, notification] })),
  dismissNotification: (id) =>
    set((state) => ({ notifications: state.notifications.filter((n) => n.id !== id) })),
  setCurrentTurf: (turf) => set({ currentTurf: turf }),
}));
