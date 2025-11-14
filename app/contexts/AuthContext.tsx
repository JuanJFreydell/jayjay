'use client';

import { createContext, useContext } from 'react';
import { SessionProvider, useSession } from 'next-auth/react';

const AuthContext = createContext<any>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      {children}
    </SessionProvider>
  );
}

export function useAuth() {
  const session = useSession();
  return {
    user: session.data?.user,
    isLoading: session.status === 'loading',
    isAuthenticated: session.status === 'authenticated',
    signOut: session.data ? () => import('next-auth/react').then(mod => mod.signOut()) : undefined,
  };
}