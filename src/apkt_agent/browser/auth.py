"""Authentication handling for APKT system."""

import getpass
from pathlib import Path
from typing import Optional, Tuple

import yaml
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

from ..config import Config
from ..errors import AuthError, ApktAuthError
from ..logging_ import get_logger
from ..workspace import RunContext


def load_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Load credentials from credentials.yaml file if exists.
    
    Returns:
        Tuple of (username, password) or (None, None) if file not found
    """
    # Try multiple paths
    cred_paths = [
        Path("credentials/credentials.yaml"),
        Path("credentials.yaml"),
    ]
    
    for cred_file in cred_paths:
        if cred_file.exists():
            try:
                with open(cred_file, 'r') as f:
                    creds = yaml.safe_load(f)
                    return creds.get('username'), creds.get('password')
            except Exception:
                pass
    return None, None


def login_apkt(page: Page, ctx: RunContext, config: Config) -> bool:
    """Login to APKT via SSO/IAM with interactive credential input.
    
    Args:
        page: Playwright page instance
        ctx: Run context
        config: Configuration object
        
    Returns:
        True if login successful
        
    Raises:
        ApktAuthError: If login fails
    """
    logger = get_logger()
    
    login_url = config.get('apkt.login_url')
    iam_login_url = config.get('apkt.iam_login_url')
    iam_totp_prefix = config.get('apkt.iam_totp_url_prefix')
    
    try:
        # Step 1: Navigate to APKT login page
        logger.info(f"Step 1: Navigating to APKT login: {login_url}")
        page.goto(login_url)
        page.wait_for_load_state("networkidle")
        logger.info(f"Current URL: {page.url}")
        
        # Step 2: Click SSO button
        logger.info("Step 2: Looking for SSO button...")
        
        # Try multiple selectors for SSO button
        sso_selectors = [
            "button:has-text('SSO')",
            "a:has-text('SSO')",
            "button:has-text('sso')",
            "a:has-text('sso')",
            "[class*='sso']",
            "text=/SSO/i",
        ]
        
        sso_button = None
        for selector in sso_selectors:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0:
                    sso_button = btn
                    logger.info(f"Found SSO button with selector: {selector}")
                    break
            except Exception:
                continue
        
        if not sso_button:
            raise ApktAuthError("Could not find SSO button on login page")
        
        logger.info("Clicking SSO button...")
        sso_button.click()
        page.wait_for_load_state("networkidle")
        
        # Step 3: Wait for IAM page
        logger.info("Step 3: Waiting for IAM page...")
        page.wait_for_url("**/iam.pln.co.id/**", timeout=30000)
        logger.info(f"Redirected to IAM: {page.url}")
        
        # Step 4: Get credentials from credentials.yaml
        logger.info("Step 4: Getting credentials from file...")
        
        # Load credentials from credentials.yaml
        username, password = load_credentials()
        
        if not username or not password:
            raise ApktAuthError("Username and password not found in credentials.yaml")
        
        # Step 5: Fill and submit IAM form (silent, using credentials from config)
        logger.info("Step 5: Filling IAM login form...")
        print("\n  ℹ Autentikasi dengan credential dari config...")
        
        # Try different selectors for username field
        username_field = page.locator("input[name='username'], input[name='email'], input[type='text']").first
        password_field = page.locator("input[name='password'], input[type='password']").first
        
        username_field.fill(username)
        logger.info("Username entered")
        
        password_field.fill(password)
        logger.info("Password entered")
        
        # Find and click submit button
        submit_button = page.locator(
            "button[type='submit'], input[type='submit'], button:has-text('Login'), button:has-text('Sign'), button:has-text('Masuk')"
        ).first
        
        logger.info("Submitting login form...")
        submit_button.click()
        page.wait_for_load_state("networkidle")
        
        logger.info(f"After login submit, URL: {page.url}")
        
        # Step 6: Check for TOTP/OTP page
        if "/totp" in page.url or (iam_totp_prefix and page.url.startswith(iam_totp_prefix)):
            logger.info("Step 6: TOTP/OTP required...")
            
            max_otp_attempts = 3
            otp_attempt = 0
            
            while otp_attempt < max_otp_attempts:
                otp_attempt += 1
                
                print("\n" + "-" * 60)
                print(f"Two-Factor Authentication Required (Attempt {otp_attempt}/{max_otp_attempts})")
                print("-" * 60)
                
                try:
                    otp_code = input("Enter OTP code: ").strip()
                except (EOFError, KeyboardInterrupt):
                    # Handle EOF error from piped input (iTerm issue)
                    # Try to read from stdin directly
                    import sys
                    try:
                        otp_code = sys.stdin.readline().strip()
                        if not otp_code:
                            raise EOFError("No OTP input available")
                    except Exception as e:
                        logger.error(f"Failed to read OTP input: {e}")
                        raise ApktAuthError(f"Failed to read OTP input: {e}")
                
                if not otp_code:
                    print("OTP code cannot be empty. Please try again.")
                    continue
                
                # Fill OTP field
                otp_field = page.locator(
                    "input[name='otp'], input[name='totp'], input[name='code'], input[type='text'], input[type='number']"
                ).first
                
                otp_field.fill(otp_code)
                logger.info("OTP code entered")
                
                # Submit OTP - try multiple strategies
                # Strategy 1: Check if there's a submit button
                otp_submit_locator = page.locator(
                    "button[type='submit'], input[type='submit'], button:has-text('Verify'), button:has-text('Submit'), button:has-text('Konfirmasi'), button:has-text('OK'), button:has-text('Continue')"
                )
                
                try:
                    if otp_submit_locator.count() > 0:
                        otp_submit = otp_submit_locator.first
                        otp_submit.wait_for(state="visible", timeout=3000)
                        logger.info("Submitting OTP via button...")
                        otp_submit.click()
                    else:
                        raise Exception("No submit button found")
                except Exception:
                    # Strategy 2: Press Enter (many OTP forms auto-submit or accept Enter)
                    logger.info("No visible submit button, pressing Enter...")
                    otp_field.press("Enter")
                
                # Wait for page transition
                page.wait_for_load_state("networkidle")
                
                # Give a bit more time for potential redirect
                page.wait_for_timeout(2000)
                
                logger.info(f"After OTP submit, URL: {page.url}")
                
                # Check if still on TOTP page (means OTP was wrong)
                if "/totp" in page.url or (iam_totp_prefix and page.url.startswith(iam_totp_prefix)):
                    logger.warning("OTP may be incorrect, still on TOTP page")
                    print("⚠ OTP appears to be incorrect. Please try again.")
                    
                    # Clear the field for retry
                    otp_field = page.locator(
                        "input[name='otp'], input[name='totp'], input[name='code'], input[type='text'], input[type='number']"
                    ).first
                    otp_field.clear()
                else:
                    # Successfully moved past OTP
                    logger.info("OTP accepted, proceeding...")
                    break
            else:
                # Exhausted all attempts
                raise ApktAuthError(f"OTP verification failed after {max_otp_attempts} attempts")
        
        # Step 7: Wait for redirect back to APKT
        logger.info("Step 7: Waiting for redirect to APKT...")
        
        # Give some time for redirect
        try:
            page.wait_for_url("**/new-apkt.pln.co.id/**", timeout=15000)
            logger.info(f"Successfully redirected to APKT: {page.url}")
        except PlaywrightTimeout:
            logger.warning(f"Not redirected to APKT yet. Current URL: {page.url}")
            
            # Step 8: Fallback - try navigating to APKT again
            if "iam.pln.co.id" in page.url:
                logger.info("Step 8: Fallback - attempting to trigger callback...")
                
                if "/home/browse" in page.url or "/home" in page.url:
                    logger.info("On IAM home page, trying to go back to APKT login...")
                    page.goto(login_url)
                    page.wait_for_load_state("networkidle")
                    
                    # Try clicking SSO again
                    sso_locator = page.locator("text=/sso/i")
                    if sso_locator.count() > 0:
                        logger.info("Clicking SSO button again...")
                        sso_locator.first.click()
                        page.wait_for_load_state("networkidle")
                        
                        # Wait for APKT redirect
                        try:
                            page.wait_for_url("**/new-apkt.pln.co.id/**", timeout=15000)
                            logger.info(f"Fallback successful. URL: {page.url}")
                        except PlaywrightTimeout:
                            pass
        
        # Final check
        if "new-apkt.pln.co.id" not in page.url:
            _save_screenshot(page, ctx, "auth_fail.png")
            raise ApktAuthError(
                f"Failed to reach APKT home page. Current URL: {page.url}"
            )
        
        page.wait_for_load_state("networkidle")
        logger.info("Login successful! APKT home page loaded.")
        print("\n✓ Login successful!")
        
        return True
        
    except ApktAuthError:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        _save_screenshot(page, ctx, "auth_fail.png")
        raise ApktAuthError(f"Login failed: {e}")


def _save_screenshot(page: Page, ctx: RunContext, filename: str) -> Path:
    """Save screenshot to raw directory.
    
    Args:
        page: Playwright page
        ctx: Run context
        filename: Screenshot filename
        
    Returns:
        Path to saved screenshot
    """
    logger = get_logger()
    screenshot_path = ctx.raw_dir / filename
    
    try:
        page.screenshot(path=str(screenshot_path))
        logger.info(f"Screenshot saved: {screenshot_path}")
    except Exception as e:
        logger.warning(f"Failed to save screenshot: {e}")
    
    return screenshot_path


# Keep class for backward compatibility (deprecated)
class Authenticator:
    """Handles authentication to APKT system (deprecated - use login_apkt function)."""
    
    def __init__(self, page, config):
        """Initialize authenticator.
        
        Args:
            page: Playwright page instance
            config: Configuration object
        """
        self.logger = get_logger()
        self.page = page
        self.config = config
    
    async def login_iam(self, username: str, password: str, totp_secret: Optional[str] = None) -> bool:
        """Login via IAM (deprecated).
        
        Args:
            username: IAM username
            password: IAM password
            totp_secret: TOTP secret for MFA
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting IAM login")
            return True
        except Exception as e:
            raise AuthError(f"IAM login failed: {e}")
    
    async def login_apkt(self) -> bool:
        """Login to APKT after IAM authentication (deprecated).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting APKT login")
            return True
        except Exception as e:
            raise AuthError(f"APKT login failed: {e}")
