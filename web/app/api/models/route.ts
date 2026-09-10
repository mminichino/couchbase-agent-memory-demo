import { NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { fetchModelInfo } from "@/lib/grpc-chat";

export async function GET() {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  }

  try {
    const models = await fetchModelInfo();
    return NextResponse.json(models);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unable to load model info.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
