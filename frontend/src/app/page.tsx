"use client";

import {
  Users,
  Calendar,
  MessageSquare,
  TrendingUp,
  ArrowRight,
  BarChart3,
  Target,
  Clock,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { Shell } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Metric } from "@/components/ui/metric";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDashboardMetrics, useRecentLeads, useUpcomingBookings } from "@/hooks";
import { formatDate, formatCurrency } from "@/lib/utils";

/**
 * Dashboard Principal - Intelligent Flow Design
 *
 * Visão geral do sistema com métricas e atividades recentes.
 * Design moderno com glassmorphism, gradients e animações.
 */

function getLeadName(lead: { name?: { firstName?: string; lastName?: string } }): string {
  if (!lead.name) return "—";
  return [lead.name.firstName, lead.name.lastName].filter(Boolean).join(" ") || "—";
}

export default function DashboardPage() {
  const { data: metrics, loading: metricsLoading, refetch: refetchMetrics } = useDashboardMetrics();
  const { data: leadsData, loading: leadsLoading } = useRecentLeads();
  const { data: bookingsData, loading: bookingsLoading } = useUpcomingBookings();

  const leads = leadsData?.data ?? [];
  const bookings = bookingsData?.data ?? [];
  const now = new Date().toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });

  return (
    <Shell>
      {/* Hero Section with Mesh Gradient */}
      <div className="relative overflow-hidden border-b border-eng-blue/[0.06] bg-gradient-to-br from-tech-white to-white">
        {/* Mesh Gradient Background */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: `
              radial-gradient(ellipse 80% 50% at 20% -10%, rgba(255,100,0,0.08) 0%, transparent 50%),
              radial-gradient(ellipse 60% 40% at 85% 110%, rgba(15,48,56,0.06) 0%, transparent 50%)
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
        <div className="absolute top-[10%] right-[-5%] w-[300px] h-[300px] rounded-full bg-alert/[0.06] blur-[100px] animate-float" />
        <div className="absolute bottom-[-10%] left-[-5%] w-[200px] h-[200px] rounded-full bg-eng-blue/[0.04] blur-[80px] animate-float" style={{ animationDelay: '-3s' }} />

        {/* Content */}
        <div className="relative z-10 px-6 lg:px-8 py-8 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            {/* Tag Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-alert/[0.08] rounded-full mb-4 animate-fade-in-up animate-fill-both">
              <Sparkles className="w-4 h-4 text-alert" />
              <span className="text-xs font-mono font-medium tracking-wide text-alert uppercase">
                IA + Marketing Médico
              </span>
            </div>

            {/* Title with highlight */}
            <h1 className="font-display text-3xl md:text-4xl font-semibold text-eng-blue tracking-tight mb-2 animate-fade-in-up animate-fill-both animate-delay-100">
              <span className="relative inline-block">
                Dashboard
                <span className="absolute bottom-[0.1em] left-0 right-0 h-[0.15em] bg-alert/25 rounded-sm -z-10" />
              </span>
            </h1>

            <div className="flex items-center gap-3 animate-fade-in-up animate-fill-both animate-delay-200">
              <Badge variant="success">
                <span className="size-1.5 rounded-full bg-green-500 animate-pulse" />
                Live
              </Badge>
              <p className="font-mono text-sm text-concrete">
                Última atualização: {now}
              </p>
            </div>
          </div>

          <div className="flex gap-3 animate-fade-in-up animate-fill-both animate-delay-300">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => refetchMetrics()}
            >
              <RefreshCw size={14} />
              Atualizar
            </Button>
            <Button size="sm">
              Nova Campanha <ArrowRight size={14} />
            </Button>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="p-6 lg:p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Metric
            label="Leads (Mês)"
            value={metricsLoading ? "—" : `+${metrics?.leads_total ?? 0}`}
            icon={<Users size={24} />}
          />
          <Metric
            label="Consultas Agendadas"
            value={metricsLoading ? "—" : String(metrics?.bookings_upcoming ?? 0)}
            icon={<Calendar size={24} />}
          />
          <Metric
            label="Conversas Ativas"
            value={metricsLoading ? "—" : String(metrics?.conversations_active ?? 0)}
            icon={<MessageSquare size={24} />}
          />
          <Metric
            label="Taxa de Conversão"
            value={metricsLoading ? "—" : `${metrics?.conversion_rate ?? 0}%`}
            icon={<TrendingUp size={24} />}
          />
        </div>
      </div>

      {/* Content Grid */}
      <div className="px-6 lg:px-8 pb-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Leads */}
        <div className="lg:col-span-2">
          <Card hoverable={false}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Leads Recentes</CardTitle>
                <Badge>
                  <Target size={12} />
                  Pipeline Ativo
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {leadsLoading ? (
                <p className="text-sm text-concrete py-8 text-center font-sans">
                  Carregando...
                </p>
              ) : leads.length === 0 ? (
                <p className="text-sm text-concrete py-8 text-center font-sans">
                  Nenhum lead encontrado
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nome</TableHead>
                      <TableHead>Telefone</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Etapa</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leads.slice(0, 8).map((lead, idx) => (
                      <TableRow key={lead.id || idx}>
                        <TableCell className="font-sans font-medium">
                          {getLeadName(lead)}
                        </TableCell>
                        <TableCell className="font-mono text-xs text-concrete">
                          {lead.phones?.primaryPhoneNumber || "—"}
                        </TableCell>
                        <TableCell className="text-concrete text-sm font-sans">
                          {lead.emails?.primaryEmail || "—"}
                        </TableCell>
                        <TableCell>
                          {lead.stage ? (
                            <Badge variant="info">{lead.stage}</Badge>
                          ) : (
                            <span className="text-concrete">—</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Upcoming Appointments */}
        <div>
          <Card hoverable={false}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Agenda Hoje</CardTitle>
                <Badge variant="active">
                  <Clock size={12} />
                  {bookings.length} Consulta{bookings.length !== 1 ? "s" : ""}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {bookingsLoading ? (
                <p className="text-sm text-concrete py-4 text-center font-sans">
                  Carregando...
                </p>
              ) : bookings.length === 0 ? (
                <p className="text-sm text-concrete py-4 text-center font-sans">
                  Nenhuma consulta hoje
                </p>
              ) : (
                <div className="space-y-4">
                  {bookings.slice(0, 5).map((booking, idx) => {
                    const time = booking.inicio
                      ? new Date(booking.inicio).toLocaleTimeString("pt-BR", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "—";
                    const attendee = booking.attendees?.[0]?.nome || booking.titulo || "—";

                    return (
                      <div
                        key={booking.uid || idx}
                        className="flex items-start gap-4 pb-4 border-b border-eng-blue-10 last:border-0 last:pb-0"
                      >
                        <div className="bg-eng-blue text-white px-3 py-2 text-center min-w-[60px] rounded-md">
                          <span className="font-mono text-sm font-bold">
                            {time}
                          </span>
                        </div>
                        <div className="flex-1">
                          <p className="font-sans font-medium text-eng-blue">{attendee}</p>
                          <p className="text-sm text-concrete font-sans">
                            {booking.titulo || "Consulta"} • {booking.status || "CONFIRMED"}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <a
                href="/agenda"
                className="block w-full mt-6 px-6 py-3 text-center text-sm font-sans font-semibold rounded-md border-2 border-eng-blue-30 bg-white text-eng-blue hover:border-eng-blue hover:bg-eng-blue-05 hover:-translate-y-0.5 transition-all duration-300"
              >
                Ver Agenda Completa
              </a>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card className="mt-6 bg-gradient-to-br from-eng-blue to-[#1A4A55] text-white" hoverable={false}>
            <CardContent className="py-6">
              <div className="flex items-center gap-4 mb-4">
                <BarChart3 size={24} className="text-alert" />
                <div>
                  <p className="font-mono text-[10px] uppercase text-white/60">
                    Conversão
                  </p>
                  <p className="text-3xl font-display font-semibold tabular-nums">
                    {metricsLoading ? "—" : `${metrics?.conversion_rate ?? 0}%`}
                  </p>
                </div>
              </div>
              <p className="text-sm text-white/60 font-sans">
                Taxa de conversão leads → consultas agendadas.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </Shell>
  );
}
