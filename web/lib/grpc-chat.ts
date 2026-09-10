import fs from "fs";
import path from "path";
import { credentials, loadPackageDefinition, type ServiceError } from "@grpc/grpc-js";
import { loadSync } from "@grpc/proto-loader";
import { getEnv } from "@/lib/env";
import type { ModelDisplayInfo } from "@/lib/model-config";

function resolveProtoPath(): string {
  const inWebApp = path.join(process.cwd(), "protos", "chat_service.proto");
  const monorepo = path.resolve(
    process.cwd(),
    "..",
    "src",
    "memory_demo",
    "protos",
    "chat_service.proto"
  );
  if (fs.existsSync(inWebApp)) return inWebApp;
  if (fs.existsSync(monorepo)) return monorepo;
  throw new Error(
    `chat_service.proto not found. Tried: ${inWebApp} and ${monorepo}`
  );
}

type ProcessInputPayload = {
  content: string;
  session_id: string;
  user_id: string;
};

type ChunkData = {
  message_json?: string;
  audit_json?: string;
};

type ModelInfoPayload = {
  llm_provider?: string;
  llm_model?: string;
  embedding_model?: string;
  embedding_provider?: string;
};

type ChatClient = {
  ProcessInput(
    payload: ProcessInputPayload
  ): NodeJS.EventEmitter & {
    cancel: () => void;
  };
  GetModelInfo(
    payload: Record<string, never>,
    callback: (error: ServiceError | null, response?: ModelInfoPayload) => void
  ): void;
};

let cachedClient: ChatClient | null = null;

function getClient(): ChatClient {
  if (cachedClient) return cachedClient;
  const protoPath = resolveProtoPath();
  const packageDefinition = loadSync(protoPath, {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
  });
  const loaded = loadPackageDefinition(packageDefinition) as unknown as {
    memory_demo: {
      chat: {
        v1: {
          ChatService: new (
            target: string,
            creds: ReturnType<typeof credentials.createInsecure>
          ) => ChatClient;
        };
      };
    };
  };
  const target = getEnv().chatApiUrl.replace(/^https?:\/\//, "");
  const service = loaded.memory_demo.chat.v1.ChatService;
  cachedClient = new service(target, credentials.createInsecure());
  return cachedClient;
}

export function streamChat(payload: ProcessInputPayload) {
  return getClient().ProcessInput(payload) as NodeJS.EventEmitter & {
    cancel: () => void;
    on(event: "data", listener: (chunk: ChunkData) => void): void;
    on(event: "error", listener: (error: Error) => void): void;
    on(event: "end", listener: () => void): void;
  };
}

export function fetchModelInfo(): Promise<ModelDisplayInfo> {
  return new Promise((resolve, reject) => {
    getClient().GetModelInfo({}, (error, response) => {
      if (error) {
        reject(error);
        return;
      }
      resolve({
        llmProvider: response?.llm_provider || "—",
        llmModel: response?.llm_model || "—",
        embeddingModel: response?.embedding_model || "—",
        embeddingProvider: response?.embedding_provider || "—"
      });
    });
  });
}
