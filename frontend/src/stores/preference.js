import { defineStore } from 'pinia';
import api from '@/api/axios';

export const usePreferenceStore = defineStore('preference', {
  state: () => ({
    myPreference: null,
    groupAggregate: null,
    loading: false,
    aggregateLoading: false,
  }),

  actions: {
    async fetchMyPreference(tripId) {
      this.loading = true;
      try {
        const response = await api.get(`/trips/${tripId}/preferences/me/`);
        this.myPreference = response.status === 204 ? null : response.data;
      } catch (err) {
        this.myPreference = null;
      } finally {
        this.loading = false;
      }
    },

    async savePreference(tripId, data) {
      const response = await api.put(`/trips/${tripId}/preferences/me/`, data);
      this.myPreference = response.data;
      return response.data;
    },

    async fetchAggregate(tripId) {
      this.aggregateLoading = true;
      try {
        const response = await api.get(`/trips/${tripId}/preferences/aggregate/`);
        this.groupAggregate = response.data;
      } finally {
        this.aggregateLoading = false;
      }
    },
  },
});
