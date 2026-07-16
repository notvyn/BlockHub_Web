from pywebpush import webpush, WebPushException
import json
import os

# Grab your keys from your environment variables
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY') 
VAPID_CLAIM_EMAIL = os.environ.get('VAPID_CLAIM_EMAIL') # e.g., "mailto:your@email.com"

def send_web_push(subscription_dict, notification_title, notification_body, target_url="/"):
    """
    Packages the data and sends it to the browser's Push Service.
    """
    try:
        webpush(
            subscription_info=subscription_dict,
            data=json.dumps({
                "title": notification_title, 
                "body": notification_body,
                "url": target_url
            }),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIM_EMAIL}
        )
        print("Push sent successfully!")
        return "success" # NEW: Explicitly return success!
        
    except WebPushException as ex:
        error_message = str(ex)
        print("Push failed!", repr(ex))
        
        # THE FIX: A bulletproof string-match looking for "410" or "unsubscribed"
        if "410" in error_message or "unsubscribed" in error_message:
            print("Subscription expired or revoked. Telling route to delete!")
            return "expired" 
            
        return "error"