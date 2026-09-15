/* Robo Doctor service worker — offline-first shell */
const CACHE = 'robo-doctor-v1';
const SHELL = ['/', '/static/manifest.webmanifest',
               '/static/icons/icon-192.png', '/static/icons/icon-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // API calls: network first, never cache patient data offline
  if (url.pathname.startsWith('/api/')) {
    e.respondWith(fetch(e.request).catch(() =>
      new Response(JSON.stringify({offline: true, detail: 'Robo Doctor is offline. Cached shell works; live analysis needs the local server.'}),
                   {status: 503, headers: {'Content-Type': 'application/json'}})));
    return;
  }
  // Static shell: cache first
  e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request)));
});
