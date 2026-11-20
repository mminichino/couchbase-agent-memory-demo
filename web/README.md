# Web Console

Next.js frontend for `memory_demo.grpc_chat` with Couchbase-backed auth and account management.

## Environment variables

```env
COUCHBASE_CONNECTION_STRING=couchbase://localhost
COUCHBASE_USERNAME=Administrator
COUCHBASE_PASSWORD=password
COUCHBASE_BUCKET=ams
COUCHBASE_SCOPE=web
COUCHBASE_COLLECTION=session
ADMIN_USER=admin
ADMIN_PASSWORD=password
CHAT_API_URL=http://localhost:8088
```

## Run

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Layouts

The UI switches layouts via `<html data-layout="...">` (see `lib/layout.ts` and `components/layout-provider.tsx`). Tailwind exposes `projector:` and `mobile:` variants for layout-specific styles.

- `default`: standard desktop layout.
- `projector`: larger text, higher contrast and full-width panels for lower-resolution projectors. Enable with the **Projector mode** toggle (header, or top-right on the login page). The choice is stored in the `camd_layout` cookie.
- `mobile`: single-column, touch-friendly layout. Enabled automatically for mobile devices (User-Agent on the server, confirmed on the client) and takes precedence over projector mode.
