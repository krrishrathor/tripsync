import { defineStore } from 'pinia';
import api from '@/api/axios';

export const useExpenseStore = defineStore('expense', {
  state: () => ({
    expenses: [],
    settlements: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchExpenses(tripId) {
      this.loading = true;
      try {
        const res = await api.get(`/trips/${tripId}/expenses/`);
        this.expenses = res.data;
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to fetch expenses';
      } finally {
        this.loading = false;
      }
    },

    async fetchSettlements(tripId) {
      this.loading = true;
      try {
        const res = await api.get(`/trips/${tripId}/expenses/settlements/`);
        this.settlements = res.data;
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to fetch settlements';
      } finally {
        this.loading = false;
      }
    },

    async addExpense(tripId, expenseData) {
      this.loading = true;
      try {
        await api.post(`/trips/${tripId}/expenses/`, expenseData);
        await this.fetchExpenses(tripId);
        await this.fetchSettlements(tripId);
      } catch (err) {
        throw err;
      } finally {
        this.loading = false;
      }
    }
  }
});
