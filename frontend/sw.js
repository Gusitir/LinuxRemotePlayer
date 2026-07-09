const CACHE = 'lrp-v16';
const ASSETS = ['./', './index.html', './app.js', './tailwind-lite.css', './skins.css', './manifest.json', './icon.svg', './icon-192.png', './icon-512.png', './apple-touch-icon.png', './skins/anime-bg.webp', './fonts/space-grotesk-regular.woff2', './fonts/space-grotesk-bold.woff2'];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    // Never cache dynamic backend traffic (REST API / WebSocket).
    if (url.pathname.startsWith('/api') || url.pathname.startsWith('/ws')) {
        return;
    }

    const path = url.pathname;
    const isCoreShell = path.endsWith('/') || path.endsWith('index.html') || path.endsWith('app.js');

    if (isCoreShell) {
        // Network-First with 3s timeout
        event.respondWith(
            new Promise((resolve) => {
                const timeoutId = setTimeout(() => {
                    caches.match(event.request).then((cached) => {
                        if (cached) resolve(cached);
                    });
                }, 3000);

                fetch(event.request)
                    .then((response) => {
                        clearTimeout(timeoutId);
                        if (response.status === 200) {
                            const clone = response.clone();
                            caches.open(CACHE).then((cache) => cache.put(event.request, clone));
                        }
                        resolve(response);
                    })
                    .catch(() => {
                        clearTimeout(timeoutId);
                        caches.match(event.request).then((cached) => {
                            if (cached) resolve(cached);
                            else resolve(new Response("Offline", { status: 503, statusText: "Offline" }));
                        });
                    });
            })
        );
    } else {
        // Cache-First for static assets
        event.respondWith(
            caches.match(event.request).then((cached) => {
                if (cached) return cached;
                return fetch(event.request).then((response) => {
                    if (response.status === 200) {
                        const clone = response.clone();
                        caches.open(CACHE).then((cache) => cache.put(event.request, clone));
                    }
                    return response;
                });
            })
        );
    }
});
