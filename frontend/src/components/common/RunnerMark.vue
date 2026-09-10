<template>
  <span class="runner-mark" aria-hidden="true">
    <img src="/runquest-runner-badge.png" alt="" />
  </span>
</template>

<style scoped>
.runner-mark {
  display: grid;
  overflow: hidden;
  place-items: center;
  line-height: 1;
  border-radius: 50%;
}

.runner-mark img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: inherit;
}
</style>
