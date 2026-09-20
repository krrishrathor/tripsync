import { defineStore } from 'pinia';
import api from '@/api/axios';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.accessToken,
  },
  
  actions: {
    async login(email, password) {
      try {
        const response = await api.post('/auth/token/', { email, password });
        this.accessToken = response.data.access;
        this.refreshToken = response.data.refresh;
        localStorage.setItem('access_token', this.accessToken);
        localStorage.setItem('refresh_token', this.refreshToken);
        await this.fetchUser();
        return true;
      } catch (error) {
        console.error('Login failed', error);
        throw error;
      }
    },
    
    async register(userData) {
      try {
        await api.post('/auth/register/', userData);
        // Auto login after register
        return await this.login(userData.email, userData.password);
      } catch (error) {
        console.error('Registration failed', error);
        throw error;
      }
    },
    
    async fetchUser() {
      if (!this.accessToken) return null;
      try {
        const response = await api.get('/auth/me/');
        this.user = response.data;
        return this.user;
      } catch (error) {
        this.logout();
        return null;
      }
    },
    
    logout() {
      this.user = null;
      this.accessToken = null;
      this.refreshToken = null;
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }
});
