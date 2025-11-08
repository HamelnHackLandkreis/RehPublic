<template>
  <div class="sidebar">
    <nav>
      <ul>
        <li><NuxtLink to="/upload">Upload</NuxtLink></li>
        <li><NuxtLink to="/statistics">Statistics</NuxtLink></li>
        <li><NuxtLink to="/map">Map</NuxtLink></li>
        <li><NuxtLink to="/match">Match</NuxtLink></li>
      </ul>
    </nav>
  </div>
</template>

<style scoped>
.sidebar {
  width: 250px;
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 20px;
  border-right: 1px solid #ddd;
}

nav ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

nav li {
  margin-bottom: 10px;
}

nav a {
  display: block;
  padding: 10px 15px;
  text-decoration: none;
  color: #333;
  border-radius: 4px;
  transition: background-color 0.2s;
}

nav a:hover {
  background-color: #e0e0e0;
}

nav a.router-link-active {
  background-color: #007bff;
  color: white;
}
</style>
