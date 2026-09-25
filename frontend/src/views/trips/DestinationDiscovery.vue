<template>
  <!-- Destination Discovery Page -->
  <div class="max-w-7xl mx-auto py-8 px-4">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
      <div>
        <div class="flex items-center gap-3 mb-2">
          <button @click="$router.push(`/trips/${route.params.id}`)" class="text-gray-500 hover:text-gray-700">
            ← Back to Trip
          </button>
          <span v-if="tripStatus === 'DESTINATION_SELECTED'" class="px-2.5 py-0.5 rounded-full bg-green-100 text-green-800 text-xs font-bold">
            Voting Closed
          </span>
          <span v-else class="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 text-xs font-bold">
            Voting Open
          </span>
        </div>
        <h2 class="text-3xl font-bold text-gray-900">Destination Discovery</h2>
        <p class="text-sm text-gray-500 mt-1">Ranked by compatibility with your group's preferences</p>
      </div>
      
      <!-- Voting Summary Banner -->
      <div v-if="!loading" class="bg-indigo-50 border border-indigo-100 rounded-xl px-5 py-3 flex items-center gap-4">
        <div>
          <div class="text-sm text-indigo-900 font-medium">Voting Progress</div>
          <div class="text-xs text-indigo-700">{{ voteStore.totalVoters }} / {{ voteStore.memberCount }} members voted</div>
        </div>
        <div class="w-24 h-2 bg-indigo-200 rounded-full overflow-hidden">
          <div class="h-full bg-indigo-600 transition-all" :style="{ width: `${voteStore.participationPct}%` }"></div>
        </div>
        <button @click="refresh" class="p-2 ml-2 text-indigo-600 hover:bg-indigo-100 rounded-lg transition-colors" title="Refresh">
          <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Error message for voting/selection actions -->
    <div v-if="actionError" class="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center">
      <span>{{ actionError }}</span>
      <button @click="actionError = null" class="text-red-500 hover:text-red-700 font-bold">&times;</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <div v-for="i in 6" :key="i" class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden animate-pulse flex flex-col h-[500px]">
        <div class="h-48 bg-gray-200 shrink-0"></div>
        <div class="p-5 flex-1 flex flex-col space-y-3">
          <div class="h-5 bg-gray-200 rounded w-2/3"></div>
          <div class="h-4 bg-gray-100 rounded w-1/2 mb-4"></div>
          <div class="h-2 bg-gray-100 rounded w-full"></div>
          <div class="h-2 bg-gray-100 rounded w-full"></div>
          <div class="h-2 bg-gray-100 rounded w-5/6 mb-4"></div>
          <div class="mt-auto h-10 bg-gray-100 rounded"></div>
        </div>
      </div>
    </div>

    <!-- Page Error -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 p-6 rounded-xl text-center max-w-2xl mx-auto mt-12">
      <p class="font-semibold text-lg">Failed to load destinations</p>
      <p class="text-sm mt-2 mb-4">{{ error }}</p>
      <button @click="refresh" class="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-800 rounded-lg font-medium transition-colors">
        Try Again
      </button>
    </div>

    <!-- Results -->
    <div v-else-if="destinations.length" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 items-stretch">
      <DestinationCard
        v-for="(scored, index) in destinations"
        :key="scored.destination.id"
        :scored="scored"
        :rank="index + 1"
        
        :voteCount="getVoteCount(scored.destination.id)"
        :voters="getVoters(scored.destination.id)"
        :isMyVote="voteStore.myVotedDestinationId === scored.destination.id"
        :isOwner="isOwner"
        :tripStatus="tripStatus"
        :isVoting="voteStore.casting && currentActionDestId === scored.destination.id"
        :isSelected="tripStatus === 'DESTINATION_SELECTED' && tripStore.currentTrip?.selected_destination === scored.destination.id"
        
        @vote="handleVote(scored.destination.id)"
        @select-final="handleSelectFinal(scored.destination.id)"
      />
    </div>

    <div v-else class="text-center py-16 text-gray-500 max-w-xl mx-auto mt-12 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
      <div class="text-4xl mb-4">🤷</div>
      <p class="text-lg font-medium text-gray-900">No destinations found</p>
      <p class="text-sm mt-1 mb-6">Make sure at least one member has submitted preferences to generate compatibility scores.</p>
      <button @click="$router.push(`/trips/${route.params.id}`)" class="px-5 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 font-medium">
        Back to Trip Dashboard
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useDestinationStore } from '@/stores/destination';
import { useVoteStore } from '@/stores/vote';
import { useTripStore } from '@/stores/trip';
import { useAuthStore } from '@/stores/auth';
import DestinationCard from '@/components/DestinationCard.vue';

const route = useRoute();
const router = useRouter();
const destStore = useDestinationStore();
const voteStore = useVoteStore();
const tripStore = useTripStore();
const authStore = useAuthStore();

const actionError = ref(null);
const currentActionDestId = ref(null);

const destinations = computed(() => destStore.scoredDestinations);
const loading = computed(() => destStore.loading || voteStore.loading || tripStore.loading);
const error = computed(() => destStore.error || tripStore.error);

const isOwner = computed(() => {
  return tripStore.currentTrip?.owner?.id === authStore.user?.id;
});
const tripStatus = computed(() => tripStore.currentTrip?.status || 'PLANNING');

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchUser();
  }
  
  const tripId = route.params.id;
  await Promise.all([
    tripStore.fetchTripDetail(tripId),
    destStore.fetchCompatible(tripId),
    voteStore.fetchSummary(tripId)
  ]);
});

const refresh = async () => {
  actionError.value = null;
  const tripId = route.params.id;
  await Promise.all([
    tripStore.fetchTripDetail(tripId),
    destStore.fetchCompatible(tripId, true), // force refresh scores
    voteStore.fetchSummary(tripId)
  ]);
};

// Map vote summary data to specific destinations
const getVoteResult = (destId) => {
  return voteStore.results.find(r => r.destination.id === destId);
};

const getVoteCount = (destId) => {
  const res = getVoteResult(destId);
  return res ? res.vote_count : 0;
};

const getVoters = (destId) => {
  const res = getVoteResult(destId);
  return res ? res.voters : [];
};

const handleVote = async (destId) => {
  actionError.value = null;
  currentActionDestId.value = destId;
  const tripId = route.params.id;
  
  try {
    if (voteStore.myVotedDestinationId === destId) {
      // Toggle off if already voted for this one
      await voteStore.retractVote(tripId);
    } else {
      // Cast new vote
      await voteStore.castVote(tripId, destId);
    }
  } catch (err) {
    actionError.value = err.response?.data?.detail || 'Failed to record vote.';
  } finally {
    currentActionDestId.value = null;
  }
};

const handleSelectFinal = async (destId) => {
  if (!confirm('Are you sure you want to lock in this destination? This will close voting and finalize the decision for the group.')) {
    return;
  }
  
  actionError.value = null;
  currentActionDestId.value = destId;
  const tripId = route.params.id;
  
  try {
    await voteStore.selectDestination(tripId, destId);
    // Refresh trip to get updated status
    await tripStore.fetchTripDetail(tripId);
    // Optionally redirect back to dashboard
    router.push(`/trips/${tripId}`);
  } catch (err) {
    actionError.value = err.response?.data?.detail || 'Failed to select destination.';
  } finally {
    currentActionDestId.value = null;
  }
};
</script>
