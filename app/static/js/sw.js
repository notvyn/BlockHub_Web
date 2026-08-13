// static/sw.js

// This "listens" for the push notification sent from the Python backend
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
    // Close the small OS notification popup
    event.notification.close();
    
    // Grab the URL we saved in the payload
    const targetUrl = event.notification.data.url;
    
    // Open a new browser window/tab to that exact link
    event.waitUntil(clients.openWindow(targetUrl)); 
});