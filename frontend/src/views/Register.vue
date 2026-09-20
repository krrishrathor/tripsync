<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-sm border border-gray-100">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">Create an account</h2>
      </div>
      <form class="mt-8 space-y-6" @submit.prevent="handleRegister">
        <div class="rounded-md shadow-sm -space-y-px">
          <div>
            <label for="username" class="sr-only">Username</label>
            <input id="username" name="username" type="text" v-model="form.username" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" placeholder="Username">
          </div>
          <div>
            <label for="first-name" class="sr-only">First Name</label>
            <input id="first-name" name="first_name" type="text" v-model="form.first_name" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" placeholder="First Name">
          </div>
          <div>
            <label for="last-name" class="sr-only">Last Name</label>
            <input id="last-name" name="last_name" type="text" v-model="form.last_name" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" placeholder="Last Name">
          </div>
          <div>
            <label for="email-address" class="sr-only">Email address</label>
            <input id="email-address" name="email" type="email" v-model="form.email" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" placeholder="Email address">
          </div>
          <div>
            <label for="password" class="sr-only">Password</label>
            <input id="password" name="password" type="password" v-model="form.password" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" placeholder="Password">
          </div>
        </div>

        <div v-if="error" class="text-red-500 text-sm text-center">
          <p v-for="(msg, field) in error" :key="field">{{ field }}: {{ Array.isArray(msg) ? msg[0] : msg }}</p>
        </div>

        <div>
          <button type="submit" :disabled="loading" class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            {{ loading ? 'Registering...' : 'Register' }}
          </button>
        </div>
        
        <div class="text-sm text-center mt-4">
          <router-link to="/login" class="font-medium text-blue-600 hover:text-blue-500">
            Already have an account? Sign in
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const form = reactive({
  username: '',
  first_name: '',
  last_name: '',
  email: '',
  password: ''
});
const error = ref(null);
const loading = ref(false);
const router = useRouter();
const authStore = useAuthStore();

const handleRegister = async () => {
  error.value = null;
  loading.value = true;
  try {
    await authStore.register(form);
    router.push('/dashboard');
  } catch (err) {
    error.value = err.response?.data || { detail: 'Registration failed. Please try again.' };
  } finally {
    loading.value = false;
  }
};
</script>
