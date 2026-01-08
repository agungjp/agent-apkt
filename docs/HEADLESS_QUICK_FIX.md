# Headless Mode Quick Reference

## Quick Summary

**Problem:** ❌ Headless mode fails at period selection  
**Fix:** ✅ Added `wait_for(state="visible")` before all selectors  
**Commit:** `2f92a77`

## Why Headless Mode Failed

```
Visible mode (headless=false):
- Browser window renders DOM
- You see what's happening
- Implicit synchronization via rendering
- ✅ Works without explicit waits

Headless mode (headless=true):
- No visual rendering overhead
- Faster but less synchronized
- JavaScript may lag behind page rendering
- ❌ Failed: Element not visible when trying to select
```

## The Fix

### Before (Problematic)

```python
month_select = page.locator("select[name='vc-component-4']").first
month_select.select_option(label=month_name)  # ❌ Timeout in headless
```

### After (Fixed)

```python
month_select = page.locator("select[name='vc-component-4']").first
month_select.wait_for(state="visible", timeout=15000)  # ✅ Wait first!
month_select.select_option(label=month_name)  # Now safe
```

## Changes Summary

| Function                 | Change                                 |
| ------------------------ | -------------------------------------- |
| `_set_unit_filter()`     | Added 10s wait_for                     |
| `_set_period_filter()`   | Added 15s wait_for (month), 10s (year) |
| `_click_export_excel()`  | Added 5s wait_for for buttons          |
| `_navigate_to_dataset()` | Added domcontentloaded + 2s buffer     |

## Testing Headless Fix

### Run with headless=true

```bash
venv/bin/apkt-agent
# When prompted:
#  Period: 202503
#  Headless: y
#  Confirm: y
```

### Expected output:

```
✓ Unit selector visible, selecting: 11 - WILAYAH ACEH
✓ Month selector visible, selecting: Maret
✓ Year selector visible, selecting: 2025
✓ Eksport button found, clicking...
✓ Excel option found, clicking...
[continues to download...]
```

### Should NOT see:

```
✗ Fatal error: Locator.select_option: Timeout 30000ms exceeded
```

## If Still Issues

1. **Check logs for exact error:**

   ```
   2026-01-08 HH:MM:SS - apkt_agent - ERROR - ✗ Failed to select month: ...
   ```

2. **Try with longer timeout:**
   Edit `multi_download.py`, change:

   ```python
   month_select.wait_for(state="visible", timeout=30000)  # 30s instead of 15s
   ```

3. **Try with visible mode to confirm logic:**

   ```bash
   # When prompted: Headless: n
   # Should work perfectly with visible browser
   ```

4. **Check network/authentication:**
   The error at period selection means auth worked, so it's just timing.

## Key Takeaway

**Headless mode is faster but needs explicit synchronization.**

Playwright's `wait_for()` method is the right tool for this - it tells the browser "wait until this element is actually visible before I proceed."

---

**Status:** ✅ Fixed  
**Last Updated:** 2026-01-08  
**Test Status:** Pending (needs user verification)
