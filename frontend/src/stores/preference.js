import { defineStore } from 'pinia';
import api from '@/api/axios';

export const usePreferenceStore = defineStore('preference', {
  state: () => ({
    myPreferences: null,
    groupPreferences: null,
    loading: false,
    error: null
  }),
  
  actions: {
    async fetchMyPreferences(tripId) {
      this.loading = true;
      try {
        const response = await api.get(`/preferences/trip/${tripId}/my-preferences/`);
        this.myPreferences = response.data;
      } catch (error) {
        if (error.response?.status === 404) {
          this.myPreferences = null; // No preferences set yet
        } else {
          this.error = error;
        }
      } finally {
        this.loading = false;
      }
    },
    
    async saveMyPreferences(tripId, data) {
      this.loading = true;
      try {
        const response = await api.post(`/preferences/trip/${tripId}/my-preferences/`, data);
        this.myPreferences = response.data;
        return response.data;
      } catch (error) {
        this.error = error;
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async fetchGroupPreferences(tripId) {
      this.loading = true;
      try {
        const response = await api.get(`/preferences/trip/${tripId}/group/`);
        this.groupPreferences = response.data;
      } catch (error) {
        this.error = error;
      } finally {
        this.loading = false;
      }
    }
  }
});
