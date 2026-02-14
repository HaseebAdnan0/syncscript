import { useEffect, useRef, useState, useCallback } from 'react';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

interface VaultSocketOptions {
  vaultId?: string;
}

interface VaultSocketReturn {
  status: ConnectionStatus;
  send: (eventType: string, data: any) => void;
  addEventListener: (eventType: string, handler: (data: any) => void) => () => void;
}

interface WebSocketMessage {
  type: string;
  data: any;
}

export function useVaultSocket({ vaultId }: VaultSocketOptions): VaultSocketReturn {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const wsRef = useRef<WebSocket | null>(null);
  const eventHandlersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectDelayRef = useRef<number>(1000);
  const maxReconnectDelay = 30000;
  const isUnmountedRef = useRef(false);

  const connect = useCallback(() => {
    if (isUnmountedRef.current) return;

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

    const url = `${wsUrl}/vault/${vaultId}/`;

    try {
      setStatus(status === 'disconnected' ? 'connecting' : 'reconnecting');
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (isUnmountedRef.current) return;

        // Check if this is a reconnection (was previously disconnected/reconnecting)
        const wasReconnecting = status === 'reconnecting' || status === 'disconnected';

        setStatus('connected');
        reconnectDelayRef.current = 1000; // Reset reconnect delay on successful connection
        console.log(`WebSocket connected to vault ${vaultId}`);

        // Emit reconnected event if this was a reconnection
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
        if (isUnmountedRef.current) return;
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        if (isUnmountedRef.current) return;

        setStatus('disconnected');
        wsRef.current = null;
        console.log(`WebSocket disconnected from vault ${vaultId}`);

        // Attempt reconnection with exponential backoff
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }

        reconnectTimeoutRef.current = setTimeout(() => {
          if (!isUnmountedRef.current) {
            connect();
          }
        }, reconnectDelayRef.current);

        // Increase delay for next reconnection attempt (exponential backoff)
        reconnectDelayRef.current = Math.min(
          reconnectDelayRef.current * 2,
          maxReconnectDelay
        );
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setStatus('disconnected');
    }
  }, [vaultId]);

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

    // Return cleanup function
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
  }, [connect]);

  return {
    status,
    send,
    addEventListener,
  };
}
