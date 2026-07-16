import { randomUUID } from "crypto";
import {
  Cluster,
  Collection,
  DocumentNotFoundError,
  connect
} from "couchbase";
import { getEnv } from "@/lib/env";
import { hashPassword, verifyPassword } from "@/lib/password";
import {
  type Account,
  type Session,
  type UserSettings,
  defaultUserSettings
} from "@/lib/types";

const ACCOUNT_INDEX_KEY = "camd:accounts:index";
const ACCOUNT_KEY_PREFIX = "camd:account:";
const SESSION_KEY_PREFIX = "camd:session:";
const SESSION_TTL_SECONDS = 60 * 60 * 24;

type AccountDocument = Account & {
  document_type: "account";
  password_hash: string;
};

type SessionDocument = Session & {
  document_type: "session";
};

type AccountIndexDocument = {
  user_ids: string[];
};

let clusterPromise: Promise<Cluster> | null = null;
let adminEnsured = false;

async function getCluster(): Promise<Cluster> {
  if (!clusterPromise) {
    const env = getEnv();
    clusterPromise = connect(env.couchbaseConnectionString, {
      username: env.couchbaseUsername,
      password: env.couchbasePassword
    });
  }
  return clusterPromise;
}

async function getCollection(): Promise<Collection> {
  const env = getEnv();
  const cluster = await getCluster();
  return cluster
    .bucket(env.couchbaseBucket)
    .scope(env.couchbaseScope)
    .collection(env.couchbaseCollection);
}

function accountKey(userId: string): string {
  return `${ACCOUNT_KEY_PREFIX}${encodeURIComponent(userId)}`;
}

function sessionKey(token: string): string {
  return `${SESSION_KEY_PREFIX}${token}`;
}

async function getDocument<T>(key: string): Promise<T | null> {
  const collection = await getCollection();
  try {
    const result = await collection.get(key);
    return result.content as T;
  } catch (error) {
    if (error instanceof DocumentNotFoundError) return null;
    throw error;
  }
}

async function getAccountIds(): Promise<string[]> {
  const index = await getDocument<AccountIndexDocument>(ACCOUNT_INDEX_KEY);
  return index?.user_ids ?? [];
}

async function addAccountId(userId: string): Promise<void> {
  const collection = await getCollection();
  const ids = await getAccountIds();
  if (!ids.includes(userId)) {
    await collection.upsert(ACCOUNT_INDEX_KEY, {
      user_ids: [...ids, userId]
    } satisfies AccountIndexDocument);
  }
}

function mergeUserSettings(value: unknown): UserSettings {
  if (!value || typeof value !== "object") return { ...defaultUserSettings };
  const settings = value as Record<string, unknown>;
  return {
    ...defaultUserSettings,
    ...(typeof settings.show_tool_responses === "boolean"
      ? { show_tool_responses: settings.show_tool_responses }
      : {})
  };
}

function mapAccount(document: AccountDocument | null): Account | null {
  if (!document?.user_id) return null;
  return {
    user_id: document.user_id,
    first_name: document.first_name ?? "",
    last_name: document.last_name ?? "",
    email: document.email || undefined,
    is_admin: document.is_admin,
    created_at: document.created_at,
    updated_at: document.updated_at,
    settings: mergeUserSettings(document.settings)
  };
}

async function ensureAdminAccount(): Promise<void> {
  if (adminEnsured) return;

  const env = getEnv();
  const collection = await getCollection();
  const now = new Date().toISOString();
  const existing = await getDocument<AccountDocument>(accountKey(env.adminUser));
  const document: AccountDocument = {
    document_type: "account",
    user_id: env.adminUser,
    first_name: existing?.first_name ?? "Admin",
    last_name: existing?.last_name ?? "User",
    email: existing?.email,
    is_admin: true,
    password_hash: hashPassword(env.adminPassword),
    created_at: existing?.created_at ?? now,
    updated_at: now,
    settings: mergeUserSettings(existing?.settings)
  };

  await collection.upsert(accountKey(env.adminUser), document);
  await addAccountId(env.adminUser);
  adminEnsured = true;
}

export async function initAuthStore(): Promise<void> {
  await ensureAdminAccount();
}

export async function authenticateUser(
  userId: string,
  password: string
): Promise<Account | null> {
  await ensureAdminAccount();
  const document = await getDocument<AccountDocument>(accountKey(userId));
  if (!document?.password_hash) return null;
  if (!verifyPassword(password, document.password_hash)) return null;
  return mapAccount(document);
}

export async function createSession(userId: string): Promise<Session> {
  const token = randomUUID();
  const createdAt = new Date().toISOString();
  const document: SessionDocument = {
    document_type: "session",
    token,
    user_id: userId,
    created_at: createdAt
  };
  const collection = await getCollection();
  await collection.upsert(sessionKey(token), document, {
    expiry: SESSION_TTL_SECONDS
  });
  return document;
}

export async function getSession(token: string): Promise<Session | null> {
  if (!token) return null;
  await ensureAdminAccount();
  const document = await getDocument<SessionDocument>(sessionKey(token));
  if (!document?.user_id) return null;
  const collection = await getCollection();
  await collection.touch(sessionKey(token), SESSION_TTL_SECONDS);
  return {
    token,
    user_id: document.user_id,
    created_at: document.created_at
  };
}

export async function deleteSession(token: string): Promise<void> {
  if (!token) return;
  const collection = await getCollection();
  try {
    await collection.remove(sessionKey(token));
  } catch (error) {
    if (!(error instanceof DocumentNotFoundError)) throw error;
  }
}

export async function getAccount(userId: string): Promise<Account | null> {
  await ensureAdminAccount();
  return mapAccount(
    await getDocument<AccountDocument>(accountKey(userId))
  );
}

export async function isAdminUser(userId: string): Promise<boolean> {
  const account = await getAccount(userId);
  return Boolean(account?.is_admin);
}

export async function listAccounts(): Promise<Account[]> {
  await ensureAdminAccount();
  const env = getEnv();
  const ids = await getAccountIds();
  const accounts = await Promise.all(ids.map((id) => getAccount(id)));
  return accounts
    .filter((item): item is Account => Boolean(item))
    .filter((item) => item.user_id !== env.adminUser)
    .sort((a, b) => a.user_id.localeCompare(b.user_id));
}

type UpsertInput = {
  user_id: string;
  first_name: string;
  last_name: string;
  email?: string;
  password?: string;
};

export async function upsertAccount(input: UpsertInput): Promise<Account> {
  await ensureAdminAccount();
  const collection = await getCollection();
  const now = new Date().toISOString();
  const existing = await getDocument<AccountDocument>(accountKey(input.user_id));
  const document: AccountDocument = {
    document_type: "account",
    user_id: input.user_id,
    first_name: input.first_name,
    last_name: input.last_name,
    email: input.email,
    is_admin: false,
    password_hash: input.password
      ? hashPassword(input.password)
      : existing?.password_hash ?? "",
    created_at: existing?.created_at ?? now,
    updated_at: now,
    settings: mergeUserSettings(existing?.settings)
  };
  if (!document.password_hash) {
    throw new Error("A password is required when creating an account.");
  }

  await collection.upsert(accountKey(input.user_id), document);
  await addAccountId(input.user_id);
  return mapAccount(document) as Account;
}

export async function deleteAccount(userId: string): Promise<void> {
  await ensureAdminAccount();
  const collection = await getCollection();
  try {
    await collection.remove(accountKey(userId));
  } catch (error) {
    if (!(error instanceof DocumentNotFoundError)) throw error;
  }
  const ids = await getAccountIds();
  await collection.upsert(ACCOUNT_INDEX_KEY, {
    user_ids: ids.filter((id) => id !== userId)
  } satisfies AccountIndexDocument);
}

export async function updateUserSettings(
  userId: string,
  partial: Partial<UserSettings>
): Promise<UserSettings> {
  await ensureAdminAccount();
  const collection = await getCollection();
  const document = await getDocument<AccountDocument>(accountKey(userId));
  if (!document) throw new Error("Account not found");

  const settings = { ...mergeUserSettings(document.settings), ...partial };
  await collection.upsert(accountKey(userId), {
    ...document,
    settings,
    updated_at: new Date().toISOString()
  } satisfies AccountDocument);
  return settings;
}
