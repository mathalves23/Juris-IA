// Service Worker para JurisIA PWA
const CACHE_NAME = 'jurisia-v1.0.0';
const STATIC_CACHE_NAME = 'jurisia-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'jurisia-dynamic-v1.0.0';

// Recursos essenciais para cache
const STATIC_ASSETS = [
  '/',
  '/static/js/main.90492e07.js',
  '/static/css/main.37ad1ecd.css',
  '/manifest.json',
  '/favicon.ico'
];

// Páginas para cache offline
const OFFLINE_PAGES = [
  '/login',
  '/dashboard',
  '/documents',
  '/templates',
  '/profile'
];

// API endpoints para cache
const API_CACHE_PATTERNS = [
  /\/api\/documents/,
  /\/api\/templates/,
  /\/api\/user/,
  /\/api\/auth/
];

// Instalar Service Worker
self.addEventListener('install', event => {
  console.log('🔧 Service Worker: Instalando...');
  
  event.waitUntil(
    Promise.all([
      // Cache recursos estáticos
      caches.open(STATIC_CACHE_NAME).then(cache => {
        console.log('📦 Cacheing recursos estáticos...');
        return cache.addAll(STATIC_ASSETS);
      }),
      
      // Cache páginas offline
      caches.open(DYNAMIC_CACHE_NAME).then(cache => {
        console.log('📄 Cacheing páginas offline...');
        return cache.addAll(OFFLINE_PAGES);
      })
    ]).then(() => {
      console.log('✅ Service Worker instalado com sucesso!');
      self.skipWaiting();
    }).catch(error => {
      console.error('❌ Erro ao instalar Service Worker:', error);
    })
  );
});

// Ativar Service Worker
self.addEventListener('activate', event => {
  console.log('🚀 Service Worker: Ativando...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          // Remover caches antigos
          if (cacheName !== STATIC_CACHE_NAME && 
              cacheName !== DYNAMIC_CACHE_NAME &&
              cacheName !== CACHE_NAME) {
            console.log('🗑️ Removendo cache antigo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('✅ Service Worker ativado!');
      return self.clients.claim();
    })
  );
});

// Interceptar requisições (estratégia de cache)
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Ignorar requisições não-HTTP
  if (!request.url.startsWith('http')) {
    return;
  }
  
  // Estratégia para diferentes tipos de recursos
  if (request.method === 'GET') {
    
    // 1. Recursos estáticos: Cache First
    if (STATIC_ASSETS.some(asset => request.url.includes(asset))) {
      event.respondWith(cacheFirstStrategy(request));
    }
    
    // 2. APIs: Network First com fallback
    else if (url.pathname.startsWith('/api/')) {
      event.respondWith(networkFirstStrategy(request));
    }
    
    // 3. Páginas: Stale While Revalidate
    else if (request.headers.get('accept').includes('text/html')) {
      event.respondWith(staleWhileRevalidateStrategy(request));
    }
    
    // 4. Outros recursos: Cache First
    else {
      event.respondWith(cacheFirstStrategy(request));
    }
  }
});

// Estratégia: Cache First (para recursos estáticos)
async function cacheFirstStrategy(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    const cache = await caches.open(STATIC_CACHE_NAME);
    cache.put(request, networkResponse.clone());
    
    return networkResponse;
  } catch (error) {
    console.error('Cache First falhou:', error);
    return new Response('Offline', { status: 503 });
  }
}

// Estratégia: Network First (para APIs)
async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    
    // Cache apenas respostas de sucesso
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Network falhou, buscando cache:', request.url);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Fallback para APIs críticas
    if (request.url.includes('/api/user')) {
      return new Response(JSON.stringify({
        error: 'Offline',
        message: 'Dados não disponíveis offline'
      }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return new Response('API não disponível offline', { status: 503 });
  }
}

// Estratégia: Stale While Revalidate (para páginas)
async function staleWhileRevalidateStrategy(request) {
  const cache = await caches.open(DYNAMIC_CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  const fetchPromise = fetch(request).then(networkResponse => {
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  }).catch(() => {
    // Se network falhar, retorna página offline
    return caches.match('/offline.html') || 
           new Response('Página não disponível offline', { 
             status: 503,
             headers: { 'Content-Type': 'text/html' }
           });
  });
  
  return cachedResponse || fetchPromise;
}

// Mensagens entre SW e cliente
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'GET_CACHE_SIZE') {
    getCacheSize().then(size => {
      event.ports[0].postMessage({ cacheSize: size });
    });
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    clearAllCaches().then(() => {
      event.ports[0].postMessage({ success: true });
    });
  }
});

// Utilitários
async function getCacheSize() {
  const cacheNames = await caches.keys();
  let totalSize = 0;
  
  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const requests = await cache.keys();
    
    for (const request of requests) {
      const response = await cache.match(request);
      if (response) {
        const blob = await response.blob();
        totalSize += blob.size;
      }
    }
  }
  
  return totalSize;
}

async function clearAllCaches() {
  const cacheNames = await caches.keys();
  return Promise.all(
    cacheNames.map(cacheName => caches.delete(cacheName))
  );
}

// Background Sync para quando voltar online
self.addEventListener('sync', event => {
  if (event.tag === 'jurisia-sync') {
    event.waitUntil(syncData());
  }
});

async function syncData() {
  console.log('🔄 Sincronizando dados...');
  
  try {
    // Sincronizar documentos pendentes
    const pendingDocs = await getFromIndexedDB('pendingDocuments');
    for (const doc of pendingDocs) {
      await syncDocument(doc);
    }
    
    // Sincronizar ações pendentes  
    const pendingActions = await getFromIndexedDB('pendingActions');
    for (const action of pendingActions) {
      await syncAction(action);
    }
    
    console.log('✅ Sincronização concluída!');
  } catch (error) {
    console.error('❌ Erro na sincronização:', error);
  }
}

// Placeholder para IndexedDB operations
async function getFromIndexedDB(storeName) {
  // Implementar conforme necessário
  return [];
}

async function syncDocument(doc) {
  try {
    await fetch('/api/documents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(doc)
    });
  } catch (error) {
    console.error('Erro ao sincronizar documento:', error);
  }
}

async function syncAction(action) {
  try {
    await fetch(action.url, {
      method: action.method,
      headers: action.headers,
      body: action.body
    });
  } catch (error) {
    console.error('Erro ao sincronizar ação:', error);
  }
}

console.log('🚀 JurisIA Service Worker carregado!'); 