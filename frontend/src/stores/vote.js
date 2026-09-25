import { defineStore } from 'pinia';
import api from '@/api/axios';

export const useVoteStore = defineStore('vote', {
  state: () => ({
    summary: null,       // full GET /votes/ response
    loading: false,
    casting: false,
    socket: null,
  }),

  getters: {
    myVotedDestinationId: (state) => state.summary?.my_vote?.destination_id ?? null,
    totalVoters:          (state) => state.summary?.total_voters ?? 0,
    memberCount:          (state) => state.summary?.member_count ?? 0,
    results:              (state) => state.summary?.results ?? [],
    participationPct:     (state) => state.summary?.participation_pct ?? 0,
  },

  actions: {
    async fetchSummary(tripId) {
      this.loading = true;
      try {
        const res = await api.get(`/trips/${tripId}/votes/`);
        this.summary = res.data;
      } finally {
        this.loading = false;
      }
    },

    connectWebSocket(tripId) {
      if (this.socket) {
        this.socket.close();
      }
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
      const wsUrl = baseUrl.replace(/^http/, 'ws').replace('/api', `/ws/trips/${tripId}/votes/`);
      
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'vote_update') {
          // Keep my_vote from the current state because broadcast_vote_update doesn't send it
          const myVote = this.summary?.my_vote;
          this.summary = data.summary;
          if (myVote) {
            this.summary.my_vote = myVote;
          }
        } else if (data.type === 'destination_selected') {
          import('@/stores/trip').then(({ useTripStore }) => {
             const tripStore = useTripStore();
             tripStore.fetchTripDetail(tripId);
          });
          this.fetchSummary(tripId);
        }
      };
      
      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    },

    disconnectWebSocket() {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
    },

    async castVote(tripId, destinationId) {
      this.casting = true;
      try {
        // Optimistic UI could be added here, but the WebSocket will also quickly send the update.
        await api.post(`/trips/${tripId}/votes/`, { destination_id: destinationId });
        await this.fetchSummary(tripId);
      } finally {
        this.casting = false;
      }
    },

    async retractVote(tripId) {
      this.casting = true;
      try {
        await api.delete(`/trips/${tripId}/votes/`);
        await this.fetchSummary(tripId);
      } finally {
        this.casting = false;
      }
    },

    async selectDestination(tripId, destinationId) {
      const res = await api.post(`/trips/${tripId}/select-destination/`, {
        destination_id: destinationId,
      });
      return res.data;
    },
  },
});
