import { defineStore } from 'pinia';
import api from '@/api/axios';

export const useItineraryStore = defineStore('itinerary', {
  state: () => ({
    itinerary: null,
    loading: false,
    generating: false,
    error: null,
  }),

  actions: {
    async fetchItinerary(tripId) {
      this.loading = true;
      this.error = null;
      try {
        const res = await api.get(`/trips/${tripId}/itinerary/`);
        this.itinerary = res.data;
      } catch (err) {
        if (err.response?.status !== 404) {
          this.error = err.response?.data?.detail || 'Failed to load itinerary';
        }
      } finally {
        this.loading = false;
      }
    },

    async generateItinerary(tripId) {
      this.generating = true;
      this.error = null;
      try {
        const res = await api.post(`/trips/${tripId}/itinerary/generate/`);
        this.itinerary = res.data;
        return res.data;
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to generate itinerary';
        throw err;
      } finally {
        this.generating = false;
      }
    }
  }
});
