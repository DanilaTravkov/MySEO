# Manual setup

Stage 1 needs no third-party credentials.

1. Install Docker Desktop, Node.js 22 or newer, and npm.
2. Copy `.env.example` to `.env` and change the local database password if desired.
3. Run `docker compose up --build` for PostgreSQL and the API.
4. Run `npm install && npm run dev:web` for the frontend, or enable the Compose `full` profile.

Google Ads and OpenAI setup will be documented at their respective manual gates. Do not add credentials before those stages.

