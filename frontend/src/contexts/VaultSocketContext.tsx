'use client';

import { createContext, useContext, useEffect, useRef, useState, useCallback, ReactNode } from 'react';
import { useAuthStore } from '@/stores/authStore';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

interface WebSocketMessage {
  type: string;
  data: any;
}

interface VaultSocketContextValue {
  status: ConnectionStatus;
  send: (eventType: string, data: any) => void;
  addEventListener: (eventType: string, handler: (data: any) => void) => () => void;
}

const VaultSocketContext = createContext<VaultSocketContextValue | null>(null);

interface VaultSocketProviderProps {
  vaultId: string;
  children: ReactNode;
}

/**
 * Provider that manages a single WebSocket connection per vault.
 * All child components share this connection via useVaultSocket hook.
 */
export function VaultSocketProvider({ vaultId, children }: VaultSocketProviderProps) {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const wsRef = useRef<WebSocket | null>(null);
  const eventHandlersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectDelayRef = useRef<number>(1000);
  const maxReconnectDelay = 30000;
  const isUnmountedRef = useRef(false);
  const connectingRef = useRef(false); // Prevent duplicate connection attempts

  const connect = useCallback(() => {
    if (isUnmountedRef.current) return;
    if (connectingRef.current) return; // Already connecting
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return; // Already connected or connecting
    }

    if (!vaultId) {
      setStatus('disconnected');
      return;
    }

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL;
    if (!wsUrl) {
      console.error('NEXT_PUBLIC_WS_URL is not defined');
      setStatus('disconnected');
      return;
    }

    const { accessToken } = useAuthStore.getState();
    if (!accessToken) {
      console.error('No access token available for WebSocket connection');
      setStatus('disconnected');
      return;
    }

    const url = `${wsUrl}/vault/${vaultId}/?token=${encodeURIComponent(accessToken)}`;

    try {
      connectingRef.current = true;
      setStatus(status === 'disconnected' ? 'connecting' : 'reconnecting');
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        connectingRef.current = false;
        if (isUnmountedRef.current) {
          ws.close();
          return;
        }

        const wasReconnecting = status === 'reconnecting' || status === 'disconnected';
        setStatus('connected');
        reconnectDelayRef.current = 1000;
        console.log(`WebSocket connected to vault ${vaultId}`);

        if (wasReconnecting) {
          const handlers = eventHandlersRef.current.get('reconnected');
          if (handlers) {
            handlers.forEach((handler) => {
              try {
                handler({ vaultId });
              } catch (error) {
                console.error('Error in reconnected event handler:', error);
              }
            });
          }
        }
      };

      ws.onmessage = (event) => {
        if (isUnmountedRef.current) return;

        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          const handlers = eventHandlersRef.current.get(message.type);

          if (handlers) {
            handlers.forEach((handler) => {
              try {
                handler(message.data);
              } catch (error) {
                console.error(`Error in event handler for ${message.type}:`, error);
              }
            });
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        connectingRef.current = false;
        if (isUnmountedRef.current) return;
        console.error('WebSocket error:', error);
      };

      ws.onclose = (event) => {
        connectingRef.current = false;
        if (isUnmountedRef.current) return;

        setStatus('disconnected');
        wsRef.current = null;
        console.log(`WebSocket disconnected from vault ${vaultId} (code: ${event.code})`);

        // Don't reconnect on policy violations (rate limit, auth failure, etc.)
        if (event.code >= 4000 && event.code <= 4999) {
          console.warn(`WebSocket closed with policy violation code ${event.code}, not reconnecting`);
          return;
        }

        // Attempt reconnection with exponential backoff
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }

        reconnectTimeoutRef.current = setTimeout(() => {
          if (!isUnmountedRef.current) {
            connect();
          }
        }, reconnectDelayRef.current);

        reconnectDelayRef.current = Math.min(
          reconnectDelayRef.current * 2,
          maxReconnectDelay
        );
      };
    } catch (error) {
      connectingRef.current = false;
      console.error('Error creating WebSocket:', error);
      setStatus('disconnected');
    }
  }, [vaultId, status]);

  const send = useCallback((eventType: string, data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = { type: eventType, data };
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn(`Cannot send message: WebSocket is not connected (status: ${status})`);
    }
  }, [status]);

  const addEventListener = useCallback((eventType: string, handler: (data: any) => void) => {
    if (!eventHandlersRef.current.has(eventType)) {
      eventHandlersRef.current.set(eventType, new Set());
    }

    const handlers = eventHandlersRef.current.get(eventType)!;
    handlers.add(handler);

    return () => {
      handlers.delete(handler);
      if (handlers.size === 0) {
        eventHandlersRef.current.delete(eventType);
      }
    };
  }, []);

  useEffect(() => {
    isUnmountedRef.current = false;
    connect();

    return () => {
      isUnmountedRef.current = true;

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      eventHandlersRef.current.clear();
    };
  }, [vaultId]); // Only reconnect when vaultId changes

  const value: VaultSocketContextValue = {
    status,
    send,
    addEventListener,
  };

  return (
    <VaultSocketContext.Provider value={value}>
      {children}
    </VaultSocketContext.Provider>
  );
}

/**
 * Hook to access the vault WebSocket connection.
 * Must be used within a VaultSocketProvider.
 */
export function useVaultSocketContext(): VaultSocketContextValue {
  const context = useContext(VaultSocketContext);
  if (!context) {
    throw new Error('useVaultSocketContext must be used within a VaultSocketProvider');
  }
  return context;
}

/**
 * Hook that returns null if no provider is present (for optional usage).
 */
export function useVaultSocketContextOptional(): VaultSocketContextValue | null {
  return useContext(VaultSocketContext);
}
