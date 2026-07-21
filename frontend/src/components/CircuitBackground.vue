<template>
  <div class="hex-bg" aria-hidden="true">
    <svg xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" viewBox="0 0 1600 900">
      <g fill="none" stroke="currentColor" stroke-width="1.2">
        <!-- left hex cluster -->
        <path d="M80 120 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M160 168 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M80 216 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M160 264 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M80 360 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M160 456 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M80 552 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M40 40 V860" />
        <path d="M220 40 V860" />
        <path d="M120 40 V860" opacity="0.55" />
        <path d="M40 200 H260" opacity="0.45" />
        <path d="M40 480 H260" opacity="0.45" />
        <path d="M40 720 H200" opacity="0.4" />

        <!-- right hex cluster -->
        <path d="M1360 140 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M1440 188 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M1360 284 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M1440 380 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M1360 476 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M1440 572 l40 -24 l40 24 v48 l-40 24 l-40 -24 z" />
        <path d="M1380 40 V860" />
        <path d="M1560 40 V860" />
        <path d="M1480 40 V860" opacity="0.55" />
        <path d="M1340 160 H1560" opacity="0.45" />
        <path d="M1340 420 H1560" opacity="0.45" />
        <path d="M1400 680 H1560" opacity="0.4" />
      </g>
    </svg>
  </div>
</template>

<script>
export default { name: 'CircuitBackground' }
</script>
