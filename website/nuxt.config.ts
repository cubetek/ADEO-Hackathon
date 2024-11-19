// https://nuxt.com/docs/api/configuration/nuxt-config


export default defineNuxtConfig({
  compatibilityDate: '2024-04-03',
  devtools: { enabled: true },
  plugins: ['~/plugins/socket.client.ts'],
  modules: [ '@nuxtjs/mdc', '@nuxt/ui'],
  tailwindcss:{
    quiet: true,
  },
  runtimeConfig:{
    public:{
      VITE_API_URL: process.env.VITE_API_URL || 'http://0.0.0.0:8000'
    }
  },
  extends: [
    // "gh:cssninjaStudio/tairo/layers/tairo#v1.5.1",
  ]
})