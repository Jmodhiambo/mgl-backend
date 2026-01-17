
#!/usr/bin/env python3
"""
Google reCAPTCHA v3 Verification Utility

Minimum acceptable score for reCAPTCHA v3 (0.0 to 1.0)
0.0 is very likely a bot, 1.0 is very likely a human
"""
import httpx
from typing import Optional
from fastapi import HTTPException

from app.core.logging_config import logger
from app.core.config import (
    RECAPTCHA_SECRET_KEY,
    RECAPTCHA_VERIFY_URL,
    MIN_RECAPTCHA_SCORE
)

async def verify_recaptcha(
    token: str,
    action: str,
    email: str,
    client_ip: Optional[str] = None,
) -> float:
    """
    Verify reCAPTCHA v3 token with Google's API.
    
    Args:
        token: The reCAPTCHA token from the frontend
        action: The expected action name (e.g., 'contact_form', 'login', 'register')
        email: The email associated with the token for logging
        client_ip: Optional client IP address for additional verification
    
    Returns:
        float: The reCAPTCHA score (0.0 to 1.0)
    
    Raises:
        HTTPException: If verification fails or score is too low
    """
    
    # Validate secret key is configured
    if not RECAPTCHA_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="reCAPTCHA is not configured on the server"
        )
    
    # Validate token is provided
    if not token:
        raise HTTPException(
            status_code=400,
            detail="reCAPTCHA token is required"
        )
    
    try:
        # Prepare request payload
        payload = {
            'secret': RECAPTCHA_SECRET_KEY,
            'response': token,
        }
        
        # Add client IP if provided
        if client_ip:
            payload['remoteip'] = client_ip
        
        # Make request to Google's verification API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RECAPTCHA_VERIFY_URL,
                data=payload,
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
        
        # Check if verification was successful
        if not result.get('success'):
            error_codes = result.get('error-codes', [])
            logger.warning(f"reCAPTCHA verification failed for user {email}: {error_codes}")
            
            # Handle specific error codes
            if 'timeout-or-duplicate' in error_codes:
                raise HTTPException(
                    status_code=400,
                    detail="reCAPTCHA token has expired or already been used"
                )
            elif 'invalid-input-response' in error_codes:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid reCAPTCHA token"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="reCAPTCHA verification failed"
                )
        
        # Verify the action matches
        received_action = result.get('action')
        if received_action != action:
            logger.warning(f"reCAPTCHA action verification failed for user {email}: {received_action} != {action}")
            raise HTTPException(
                status_code=400,
                detail="reCAPTCHA action verification failed"
            )
        
        # Get the score
        score = result.get('score', 0.0)
        
        # Check if score meets minimum threshold
        if score < MIN_RECAPTCHA_SCORE:
            logger.warning(f"reCAPTCHA score too low for user {email}: {score} < {MIN_RECAPTCHA_SCORE}")
            raise HTTPException(
                status_code=403,
                detail="Security verification failed. Please try again."
            )
        
        # Log successful verification (optional)
        hostname = result.get('hostname', 'unknown')
        challenge_ts = result.get('challenge_ts', 'unknown')
        logger.info(f"reCAPTCHA verification successful for user {email} from {hostname} at {challenge_ts}")        
        return score
        
    except httpx.HTTPError as e:
        logger.error(f"Error during reCAPTCHA verification: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Unable to verify reCAPTCHA. Please try again later."
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"An error occurred during reCAPTCHA verification: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during security verification"
        )


async def verify_recaptcha_lenient(
    token: str,
    action: str,
    client_ip: Optional[str] = None
) -> Optional[float]:
    """
    Lenient version of reCAPTCHA verification that returns None on failure
    instead of raising an exception. Useful for optional verification.
    
    Args:
        token: The reCAPTCHA token from the frontend
        action: The expected action name
        client_ip: Optional client IP address
    
    Returns:
        Optional[float]: The score if successful, None if verification fails
    """
    try:
        return await verify_recaptcha(token, action, client_ip)
    except HTTPException:
        return None
    except Exception:
        return None