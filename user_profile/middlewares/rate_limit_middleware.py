import time
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status

class RateLimitMiddleware:
    """
    Middleware to limit the number of requests a user can make to the API within a specified time window.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.

        """
        self.get_response = get_response

    def __call__(self, request):
        """
        This method is called on every HTTP request. It checks if the number of requests made
        by a client (identified by their IP address) exceeds the allowed limit within the 
        defined rolling time window.

        Args:
            request (HttpRequest): The request object that contains details about the HTTP request.

        Returns:
            HttpResponse: The response to be sent to the client. If the rate limit is exceeded,
                           a 429 status code is returned. Otherwise, the normal response is returned.
        """
        # Get the client's IP address.
        ip = self.get_client_ip(request)

        cache_key = f"request_count_{ip}"

        # Maximum allowed requests within the rolling window (100 requests in this example).
        max_requests = 100
        rolling_window = 300  # 5 minutes in seconds

        # Get the current timestamp in seconds.
        now = time.time()

        # Retrieve the list of request timestamps for this IP from the cache.
        request_timestamps = cache.get(cache_key, [])

        # Filter out timestamps that are outside the rolling window (older than 5 minutes).
        request_timestamps = [ts for ts in request_timestamps if now - ts <= rolling_window]

        # If the user has exceeded the maximum allowed requests within the rolling window,
        # return a 429 Too Many Requests response.
        if len(request_timestamps) >= max_requests:
            return JsonResponse(
                {"error": "Too Many Requests"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,  
                headers={"X-RateLimit-Remaining": 0} 
            )
            
        request_timestamps.append(now)

        cache.set(cache_key, request_timestamps, timeout=rolling_window)

        response = self.get_response(request)

        # Calculate the remaining number of requests allowed for the current client.
        remaining_requests = max_requests - len(request_timestamps)

        # Add the X-RateLimit-Remaining header to the response, which indicates how many
        # requests the client can still make within the rolling window.
        response["X-RateLimit-Remaining"] = remaining_requests

        return response

    def get_client_ip(self, request):
        """
        Get the client's IP address from the request headers.

        The IP address is retrieved from either the `X-Forwarded-For` header (if the client is behind a proxy)
        or from the `REMOTE_ADDR` header (if the client is directly connected).

        Args:
            request (HttpRequest): The request object.

        Returns:
            str: The IP address of the client making the request.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        
        return request.META.get("REMOTE_ADDR")
