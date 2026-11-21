# Dailyform

A phone-friendly academic and workout tracker with username-and-password accounts, private records, backup import/export and home-screen support.

## Deploy on Render

Push this directory to its own GitHub, GitLab or Bitbucket repository. In Render, create a Blueprint from that repository and review `render.yaml`. It creates a Python web service and a Postgres database in Singapore. Render generates the signing secret and supplies the database connection privately.

The configuration uses free preview resources. Render's free Postgres database expires after 30 days. Upgrade the database before expiry for continued use and export records regularly. The free web service sleeps after 15 idle minutes and can take about a minute to wake. Review the current Render pricing before selecting a paid plan.

The first startup applies database migrations. The `/health/` endpoint verifies database connectivity. Do not put a SQLite database on a Render ephemeral filesystem.

## Use the app

Open the deployed URL, select **Create an account**, choose a username and password, then log your revision and exercises. Sign in with the same account on another device and use **Refresh records** to load the latest entries. Saves are checked against a revision number so a stale device cannot overwrite newer records.

Under **App & backup**, import a JSON export from the original Dailyform HTML file. Import merges records by their IDs. Changes stay unsaved if a request fails, and the page reports the error. Account pages require an internet connection.

On iPhone, use Safari's share menu and **Add to Home Screen**. On Android, use Chrome's menu and **Add to Home screen** or **Install app**, where offered.

## Local development

Use Python 3.12 or later. Install `requirements.txt`. Set `DEBUG=true` and a randomly generated `SECRET_KEY` in your environment. Run `python manage.py migrate`, then `python manage.py runserver`. Development uses an ignored SQLite database. Production requires `DATABASE_URL`, disables debug output, and uses secure session cookies.

Run `python manage.py test` for authentication, record isolation, CSRF, and conflict checks. Run `python manage.py check --deploy` with production environment settings before deployment.

## Accounts

Passwords use Django's scrypt hasher. Login attempts are throttled in the database. Log out through the account controls. Change password while signed in. Email delivery and self-service password recovery are not configured. The operator can recover an account using `python manage.py changepassword USERNAME` in a trusted Render shell when available.

## References

- [Django authentication](https://docs.djangoproject.com/en/5.2/topics/auth/default/)
- [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
- [Render free resource limits](https://render.com/docs/free)
