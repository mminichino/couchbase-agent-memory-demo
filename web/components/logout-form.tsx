"use client";

import { useSyncExternalStore } from "react";
import { Button } from "@/components/ui/button";

const noopSubscribe = () => () => {};

function getOriginSnapshot() {
  return typeof window !== "undefined" ? window.location.origin : "";
}

function getServerOriginSnapshot() {
  return "";
}

export function LogoutForm() {
  const clientOrigin = useSyncExternalStore(
    noopSubscribe,
    getOriginSnapshot,
    getServerOriginSnapshot
  );

  return (
    <form action="/api/auth/logout" method="post">
      <input type="hidden" name="client_origin" value={clientOrigin} />
      <Button variant="secondary" type="submit" className="mobile:h-11 projector:h-11">
        Log out
      </Button>
    </form>
  );
}
