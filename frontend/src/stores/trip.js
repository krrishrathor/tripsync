import { defineStore } from 'pinia';
import api from '@/api/axios';

export const useTripStore = defineStore('trip', {
  state: () => ({
    trips: [],
    currentTrip: null,
    loading: false,
    error: null
  }),
  
  actions: {
    async fetchTrips() {
      this.loading = true;
      try {
        const response = await api.get('/trips/');
        this.trips = response.data;
      } catch (error) {
        this.error = error;
      } finally {
        this.loading = false;
      }
    },
    
    async fetchTripDetail(id) {
      this.loading = true;
      try {
        const response = await api.get(`/trips/${id}/`);
        this.currentTrip = response.data;
        return response.data;
      } catch (error) {
        this.error = error;
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async createTrip(tripData) {
      try {
        const response = await api.post('/trips/', tripData);
        this.trips.push(response.data);
        return response.data;
      } catch (error) {
        throw error;
      }
    },
    
    async joinTrip(inviteCode) {
      try {
        const response = await api.post(`/trips/join/${inviteCode}/`);
        return response.data;
      } catch (error) {
        throw error;
      }
    },
    
    async generateInvite(tripId) {
      try {
        const response = await api.post(`/trips/${tripId}/invite/`);
        if (this.currentTrip && this.currentTrip.id === tripId) {
          this.currentTrip.invite_code = response.data.invite_code;
        }
        return response.data;
      } catch (error) {
        throw error;
      }
    }
  }
});
