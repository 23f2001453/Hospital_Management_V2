<template>
  <div class="container">
    <h1>Login Form</h1>
    <form>
      <div class="mb-3">
        <label for="email" class="form-label">User Email</label>
        <input type="email" class="form-control" id="email" placeholder="Enter email" v-model="email">
      </div>
      <div class="mb-3">
        <label for="password" class="form-label">Password</label>
        <input type="password" class="form-control" id="password" placeholder="Enter password" v-model="password">
      </div>
      <button type="submit" class="btn btn-primary">Login</button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const email = ref('');
const password = ref('');

</script>



<style scoped>
</style>