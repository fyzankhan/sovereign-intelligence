import { Sparkles, X } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function ComingSoon({ feature, onClose }) {
  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-950/30 px-4 backdrop-blur-sm">
      <div className="relative w-full max-w-sm rounded-2xl border border-[var(--chat-border)] bg-[var(--chat-surface)] p-6 text-center shadow-2xl">
        <Button
          type="button"
          variant="ghost"
          onClick={onClose}
          aria-label="Close"
          className="absolute right-2 top-2 h-8 w-8 rounded-lg p-0 text-[var(--chat-muted)]"
        >
          <X size={16} />
        </Button>

        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-500/10 text-[var(--chat-accent)]">
          <Sparkles size={22} />
        </div>
        <h2 className="text-lg font-semibold">{feature}</h2>
        <p className="mt-2 text-sm leading-6 text-[var(--chat-muted)]">
          This feature is coming soon. We’re still putting the finishing touches on it.
        </p>
      </div>
    </div>
  );
}
