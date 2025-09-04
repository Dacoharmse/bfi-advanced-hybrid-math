# Production Environment Variables

## Required Environment Variables for Production Server

The following environment variables should be set on the production server:

### Essential for Password Reset Functionality
```bash
BASE_URL=https://trading.bonangfinance.co.za
```

### Other Important Variables
```bash
DISCORD_WEBHOOK_URL=your_production_webhook_url
FLASK_ENV=production
DEBUG=False
```

## How to Set on Production Server

1. SSH into the production server
2. Navigate to the application directory: `/home/bfi-signals/app`
3. Edit or create the `.env` file:
   ```bash
   nano .env
   ```
4. Add the BASE_URL variable:
   ```
   BASE_URL=https://trading.bonangfinance.co.za
   ```
5. Restart the application service:
   ```bash
   sudo systemctl restart bfi-signals.service
   ```

## Testing Password Reset

After deploying, test the password reset functionality:

1. Go to the login page
2. Click "Forgot your password?"
3. Enter a valid email address
4. Check that the email contains the correct production URLs
5. Verify the reset link works properly

## Notes

- The BASE_URL is used to generate correct links in password reset emails
- Without this variable, password reset emails will contain localhost URLs
- This fix resolves the issue where password reset was not working on the live site