const env = {
  couchbaseConnectionString:
    process.env.COUCHBASE_CONNECTION_STRING ?? "couchbase://localhost",
  couchbaseUsername: process.env.COUCHBASE_USERNAME ?? "Administrator",
  couchbasePassword: process.env.COUCHBASE_PASSWORD ?? "password",
  couchbaseBucket: process.env.COUCHBASE_BUCKET ?? "ams",
  couchbaseScope: process.env.COUCHBASE_SCOPE ?? "web",
  couchbaseCollection: process.env.COUCHBASE_COLLECTION ?? "session",
  adminUser: process.env.ADMIN_USER ?? "admin",
  adminPassword: process.env.ADMIN_PASSWORD ?? "password",
  chatApiUrl: process.env.CHAT_API_URL ?? "http://localhost:8088"
};

export function getEnv() {
  return env;
}
