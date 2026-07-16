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
