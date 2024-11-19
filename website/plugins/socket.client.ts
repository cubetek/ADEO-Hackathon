import { io } from 'socket.io-client'


export default defineNuxtPlugin({
  async setup(nuxtApp) {
    const host = nuxtApp.$config.public.VITE_API_URL as string; // Backend host
    const sockets: string[] = ['chat']; // Define your socket namespaces
    sockets.forEach((name) => {
      const socketName = `${name}Socket`;
      const socket = io(`${host}/${name}-socket`, {
        autoConnect: true,
      });

      // Provide the socket instance to the app
      nuxtApp.provide(socketName, socket);

      // Handle socket events
      socket.on('error', (error: any) => {
        console.error(`Error on ${name} socket:`, error);
      });

      socket.on('disconnect', () => {
        console.warn(`${name} socket disconnected`);
        window.dispatchEvent(
          new CustomEvent('socket-disconnect', {
            detail: { socketName },
          }),
        );
      });

      socket.on('connect', () => {
        console.log(`${name} socket connected`);
        window.dispatchEvent(
          new CustomEvent('socket-connect', {
            detail: { socketName },
          }),
        );
      });
    });
  },
  hooks: {
    'app:created'() {
      console.log('Nuxt app created. Socket.IO plugin is initialized.');
    },
  },
  env: {
    islands: true,
  },
});
