"use client";

import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Lock, AlertCircle } from "lucide-react";
import { useAuth } from "@/components/auth/auth-provider";

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await login(email, password);
      const redirect = searchParams.get("redirect");
      if (redirect && redirect.includes("trafegoparaconsultorios.com.br")) {
        window.location.href = redirect;
      } else {
        router.push("/");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao fazer login");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="bg-white border border-graphite p-6 shadow-hard">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="email"
            className="block text-xs font-mono uppercase tracking-wider text-steel mb-1"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            className="w-full px-3 py-2 border border-graphite bg-paper font-mono text-sm focus:outline-none focus:ring-2 focus:ring-ink"
            placeholder="usuario@clinica.com"
          />
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-xs font-mono uppercase tracking-wider text-steel mb-1"
          >
            Senha
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            className="w-full px-3 py-2 border border-graphite bg-paper font-mono text-sm focus:outline-none focus:ring-2 focus:ring-ink"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2">
            <AlertCircle size={14} />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 bg-ink text-paper font-mono text-sm uppercase tracking-wider hover:bg-graphite disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          <Lock size={14} />
          {submitting ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-dvh bg-paper bg-grid flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-8 h-8 bg-ink flex items-center justify-center">
              <span className="text-paper font-bold text-sm font-mono">M</span>
            </div>
            <span className="text-xl font-bold tracking-tight uppercase">
              MedFlow
            </span>
          </div>
          <p className="text-sm text-steel font-mono uppercase tracking-widest">
            Sistema Integrado
          </p>
        </div>

        {/* Login Card */}
        <Suspense fallback={<div className="bg-white border border-graphite p-6 shadow-hard animate-pulse h-64" />}>
          <LoginForm />
        </Suspense>

        {/* Footer */}
        <p className="text-center text-xs text-steel font-mono mt-4">
          Tráfego para Consultórios &copy; {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
}
