const CACHE_NAME = 'fincontrol-v4';

// Arquivos locais: obrigatórios para a instalação do PWA
const LOCAL_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './assets/icon.svg',
  './css/tailwind.css',
  './js/db.js',
  './js/theme.js'
];

// CDNs essenciais: cacheadas individualmente (falha de uma não impede a instalação)
const CDN_ASSETS = [
  'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/sql-wasm.js',
  'https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/sql-wasm.wasm',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap'
];

/**
 * Tenta cachear em modo CORS (necessário para o .wasm via fetch);
 * se o servidor não suportar, guarda a resposta opaca (suficiente para <script>/<link>)
 */
async function cachearCDN(cache, url) {
  try {
    const resp = await fetch(url, { mode: 'cors' });
    if (resp.ok) return cache.put(url, resp);
  } catch (e) { /* tenta no-cors abaixo */ }
  try {
    const opaca = await fetch(url, { mode: 'no-cors' });
    return cache.put(url, opaca);
  } catch (e) {
    console.warn('[SW] Não foi possível cachear:', url);
  }
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      await cache.addAll(LOCAL_ASSETS);
      await Promise.all(CDN_ASSETS.map((url) => cachearCDN(cache, url)));
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Permite à página consultar a versão do cache ativa
self.addEventListener('message', (event) => {
  if (event.data === 'GET_VERSION' && event.ports[0]) {
    event.ports[0].postMessage(CACHE_NAME);
  }
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  // Network first with fallback to cache for offline availability
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        // Respostas opacas (CDN carregada via <script>/<link>) também são cacheadas
        if (networkResponse && (networkResponse.status === 200 || networkResponse.type === 'opaque')) {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return networkResponse;
      })
      .catch(() => caches.match(event.request))
  );
});
