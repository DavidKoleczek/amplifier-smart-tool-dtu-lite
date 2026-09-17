import { Check, Copy, ExternalLink, Info, X } from "lucide-react";
import { useState } from "react";

import { DestroyDialog } from "@/components/DestroyDialog";
import { StatusDot } from "@/components/StatusDot";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { capitalize } from "@/lib/status";
import { relativeTime } from "@/lib/time";
import type { Universe } from "@/lib/types";

function readiness(universe: Universe) {
  const checked = universe.services.filter(
    (service) => service.health !== null,
  );
  const failing = checked.filter((service) => service.health !== "healthy");
  return {
    checked,
    failing,
    ready: checked.length > 0 && failing.length === 0,
  };
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 text-sm">
      <span className="shrink-0 text-muted-foreground">{label}</span>
      <span className="text-right break-all">{value}</span>
    </div>
  );
}

function CopyCommand({ command }: { command: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }
  return (
    <div className="flex items-center gap-2 rounded-md bg-muted px-2.5 py-1.5 font-mono text-xs">
      <span className="flex-1 truncate" title={command}>
        {command}
      </span>
      <Button
        variant="ghost"
        size="icon-xs"
        onClick={copy}
        aria-label="Copy command"
      >
        {copied ? <Check /> : <Copy />}
      </Button>
    </div>
  );
}

export function UniversePanel({
  universe,
  now,
  checking,
  onCheck,
  onClose,
  onDestroyed,
}: {
  universe: Universe;
  now: number;
  checking: boolean;
  onCheck: () => void;
  onClose: () => void;
  onDestroyed: () => void;
}) {
  const twin = universe.services.find(
    (service) => service.name === universe.twin_machine,
  );
  const { checked, failing, ready } = readiness(universe);
  const created = new Date(universe.created_at);

  return (
    <aside className="flex flex-col gap-5 self-start rounded-lg border p-6">
      <div className="flex items-start justify-between gap-2">
        <h2 className="text-lg font-semibold break-all">{universe.id}</h2>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={onClose}
          aria-label="Close"
        >
          <X />
        </Button>
      </div>

      <div className="flex flex-col gap-1">
        <Row label="Profile" value={universe.name} />
        {universe.description && (
          <p className="text-sm text-muted-foreground">
            {universe.description}
          </p>
        )}
      </div>

      <Separator />

      <div className="flex flex-col gap-2">
        <Row
          label="Container"
          value={
            <StatusDot
              tone={twin?.state === "running" ? "green" : "gray"}
              label={twin ? capitalize(twin.state) : "Not present"}
              className="font-medium"
            />
          }
        />
        <Row
          label="Readiness"
          value={
            <StatusDot
              tone={ready ? "green" : checked.length === 0 ? "gray" : "orange"}
              label={
                checked.length === 0
                  ? "No healthchecks"
                  : ready
                    ? "Ready"
                    : "Not ready"
              }
              className="font-medium"
            />
          }
        />
        {checked.length > 0 && !ready && (
          <div className="flex items-start gap-2 rounded-md border border-orange-200 bg-orange-50 p-3 text-sm">
            <Info className="mt-0.5 size-4 shrink-0 text-orange-500" />
            <div className="flex-1">
              <p className="font-medium text-orange-900">
                {checked.length - failing.length} of {checked.length} checks
                passed
              </p>
              {failing.map((service) => (
                <p key={service.name} className="text-muted-foreground">
                  {service.name} &middot; {service.health}
                </p>
              ))}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={onCheck}
              disabled={checking}
            >
              {checking ? "Checking..." : "Check again"}
            </Button>
          </div>
        )}
      </div>

      <Separator />

      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">Access</h3>
        {universe.urls.length === 0 && (
          <p className="text-sm text-muted-foreground">No published ports.</p>
        )}
        {universe.urls.map((url) => (
          <div key={url.url} className="flex flex-col text-sm">
            <a
              href={url.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-primary hover:underline"
            >
              {url.label ?? url.path}
              <ExternalLink className="size-3.5" />
            </a>
            <span className="text-muted-foreground">
              {url.url.replace(/^https?:\/\//, "")}
            </span>
          </div>
        ))}
      </div>

      <Separator />

      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">Details</h3>
        <Row
          label="Created"
          value={
            <span title={created.toLocaleString()}>
              {relativeTime(universe.created_at, now, true)}
            </span>
          }
        />
        <Row label="Twin" value={universe.twin_machine} />
        <Row label="Profile path" value={universe.profile_path} />
        <Row label="State path" value={universe.state_path} />
        <CopyCommand command={`dtu-lite exec --id ${universe.id}`} />
      </div>

      <Separator />

      <DestroyDialog id={universe.id} onDestroyed={onDestroyed} />
    </aside>
  );
}
