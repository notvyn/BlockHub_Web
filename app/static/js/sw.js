// static/sw.js

// This "listens" for the push notification sent from your Python backend
self.addEventListener('push', function(event) {
    const data = event.data ? event.data.json() : {};
    const title = data.title || "BlockHub Update";
    
    const options = {
        body: data.body || "You have a new update!",
        icon: '/static/img/logo.png',
        badge: '/static/img/logo.png',
        // Store the URL securely inside the notification's data property
        data: {
            url: data.url || '/' 
        }
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function(event) {
    // 1. Close the small OS notification popup
    event.notification.close();
    
    // 2. Grab the URL we saved in the payload
    const targetUrl = event.notification.data.url;
    
    // 3. Open a new browser window/tab to that exact link
    event.waitUntil(clients.openWindow(targetUrl)); 
});