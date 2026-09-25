import { defineStore } from 'pinia';
import api from '@/api/axios';

export const useDestinationStore = defineStore('destination', {
  state: () => ({
    scoredDestinations: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchCompatible(tripId, refresh = false) {
      this.loading = true;
      this.error = null;
      try {
        const url = `/trips/${tripId}/compatible-destinations/${refresh ? '?refresh=1' : ''}`;
        const response = await api.get(url);
        this.scoredDestinations = response.data;
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to load destinations.';
      } finally {
        this.loading = false;
      }
    },
  },
});
