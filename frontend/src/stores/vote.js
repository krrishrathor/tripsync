import { defineStore } from 'pinia';
import api from '@/api/axios';

export const useVoteStore = defineStore('vote', {
  state: () => ({
    summary: null,       // full GET /votes/ response
    loading: false,
    casting: false,
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

    async castVote(tripId, destinationId) {
      this.casting = true;
      try {
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
