"use client";

import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Lock, AlertCircle, Sparkles } from "lucide-react";
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
    <div className="bg-white/80 backdrop-blur-sm border border-eng-blue/[0.08] rounded-xl p-8 shadow-lg">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-sans font-medium text-eng-blue mb-2"
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
            className="w-full px-5 py-3 border-2 border-eng-blue-10 bg-white/80 rounded-md font-sans text-sm text-eng-blue placeholder:text-concrete/50 focus:outline-none focus:border-alert focus:ring-4 focus:ring-alert-10 transition-all duration-300"
            placeholder="usuario@clinica.com"
          />
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-sm font-sans font-medium text-eng-blue mb-2"
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
            className="w-full px-5 py-3 border-2 border-eng-blue-10 bg-white/80 rounded-md font-sans text-sm text-eng-blue placeholder:text-concrete/50 focus:outline-none focus:border-alert focus:ring-4 focus:ring-alert-10 transition-all duration-300"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 px-4 py-3 rounded-md">
            <AlertCircle size={16} />
            <span className="font-sans">{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3 bg-alert text-white font-sans font-semibold text-sm rounded-md shadow-md shadow-glow-orange hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none transition-all duration-300 flex items-center justify-center gap-2"
        >
          <Lock size={16} />
          {submitting ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-dvh bg-tech-white flex items-center justify-center p-4 relative overflow-hidden">
      {/* Mesh Gradient Background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `
            radial-gradient(ellipse 80% 50% at 20% -10%, rgba(255,100,0,0.08) 0%, transparent 50%),
            radial-gradient(ellipse 60% 40% at 85% 110%, rgba(15,48,56,0.06) 0%, transparent 50%),
            linear-gradient(180deg, #F5F5F2 0%, #FFFFFF 100%)
          `
        }}
      />

      {/* Grid Pattern */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(15,48,56,0.03) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(15,48,56,0.03) 1px, transparent 1px)
          `,
          backgroundSize: '80px 80px',
          maskImage: 'radial-gradient(ellipse 100% 80% at center, black 20%, transparent 80%)'
        }}
      />

      {/* Floating Blobs */}
      <div className="absolute top-[10%] right-[-5%] w-[400px] h-[400px] rounded-full bg-alert/[0.06] blur-[100px] animate-float" />
      <div className="absolute bottom-[-10%] left-[-5%] w-[300px] h-[300px] rounded-full bg-eng-blue/[0.04] blur-[80px] animate-float" style={{ animationDelay: '-3s' }} />

      <div className="w-full max-w-sm relative z-10">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in-up animate-fill-both">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-md bg-gradient-to-br from-eng-blue to-[#1A4A55] flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <span className="font-display text-2xl font-semibold text-eng-blue tracking-tight">
              MedFlow
            </span>
          </div>
          <p className="text-sm text-concrete font-sans">
            Sistema Integrado de Marketing Médico
          </p>
        </div>

        {/* Login Card */}
        <div className="animate-fade-in-up animate-fill-both animate-delay-100">
          <Suspense fallback={<div className="bg-white/80 border border-eng-blue/[0.08] rounded-xl p-8 shadow-lg animate-pulse h-64" />}>
            <LoginForm />
          </Suspense>
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-concrete font-sans mt-6 animate-fade-in-up animate-fill-both animate-delay-200">
          Tráfego para Consultórios © {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
}
