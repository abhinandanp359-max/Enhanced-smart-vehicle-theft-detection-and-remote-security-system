// hooks/useSocket.js
import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import { BACKEND } from '../utils/api';

let socketInstance = null;

export function useSocket(ownerId = 'owner_01', vehicleId = 'veh_01') {
  const socketRef = useRef(null);
  const [, setRerender] = useState({});

  useEffect(() => {
    if (!socketInstance) {
      socketInstance = io(BACKEND, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        timeout: 10000,
      });
    }
    socketRef.current = socketInstance;
    setRerender({});

    socketInstance.emit('join_room', `owner:${ownerId}`);
    socketInstance.emit('join_room', `vehicle:${vehicleId}`);

    return () => {
      if (socketInstance) {
        socketInstance.emit('leave_room', `owner:${ownerId}`);
        socketInstance.emit('leave_room', `vehicle:${vehicleId}`);
      }
    };
  }, [ownerId, vehicleId]);

  return socketInstance || socketRef.current;
}
