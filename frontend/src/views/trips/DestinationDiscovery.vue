<template>
  <!-- Destination Discovery Page -->
  <div class="max-w-7xl mx-auto py-8 px-4">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8 gap-4">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Destination Discovery</h2>
        <p class="text-sm text-gray-500 mt-1">Ranked by compatibility with your group's preferences</p>
      </div>
      <button @click="refresh"
        class="flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700">
        <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Refresh Scores
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <div v-for="i in 6" :key="i"
        class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden animate-pulse">
        <div class="h-48 bg-gray-200"></div>
        <div class="p-5 space-y-3">
          <div class="h-5 bg-gray-200 rounded w-2/3"></div>
          <div class="h-4 bg-gray-100 rounded w-1/2"></div>
          <div class="h-3 bg-gray-100 rounded w-full"></div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error"
      class="bg-red-50 border border-red-200 text-red-700 p-6 rounded-xl text-center">
      <p class="font-semibold">Failed to load destinations</p>
      <p class="text-sm mt-1">{{ error }}</p>
    </div>

    <!-- Results -->
    <div v-else-if="destinations.length" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <DestinationCard
        v-for="(scored, index) in destinations"
        :key="scored.destination.id"
        :scored="scored"
        :rank="index + 1"
      />
    </div>

    <div v-else class="text-center py-16 text-gray-500">
      <p class="text-lg font-medium">No destinations found</p>
      <p class="text-sm mt-1">Make sure at least one member has submitted preferences.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useDestinationStore } from '@/stores/destination';
import DestinationCard from '@/components/DestinationCard.vue';

const route = useRoute();
const destStore = useDestinationStore();

const destinations = computed(() => destStore.scoredDestinations);
const loading = computed(() => destStore.loading);
const error = computed(() => destStore.error);

onMounted(() => destStore.fetchCompatible(route.params.id));

const refresh = () => destStore.fetchCompatible(route.params.id, true);
</script>
