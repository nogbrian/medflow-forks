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
 * Dashboard Principal
 *
 * Visão geral do sistema com métricas e atividades recentes.
 * Dados vêm do backend via API proxy routes.
 * Fallback para estados vazios quando API está indisponível.
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
      {/* Page Header */}
      <div className="border-b border-graphite bg-white">
        <div className="px-6 lg:px-8 py-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold tracking-tight uppercase">
                Dashboard
              </h1>
              <Badge variant="active">
                <span className="size-1.5 bg-[#22C55E]" />
                Live
              </Badge>
            </div>
            <p className="font-mono text-sm text-steel">
              ÚLTIMA_ATUALIZAÇÃO: {now}
            </p>
          </div>

          <div className="flex gap-3">
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px bg-graphite border border-graphite">
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
          <Card>
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
                <p className="text-sm text-steel py-8 text-center font-mono">
                  CARREGANDO...
                </p>
              ) : leads.length === 0 ? (
                <p className="text-sm text-steel py-8 text-center font-mono">
                  NENHUM LEAD ENCONTRADO
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
                        <TableCell className="font-medium">
                          {getLeadName(lead)}
                        </TableCell>
                        <TableCell className="font-mono text-xs text-steel">
                          {lead.phones?.primaryPhoneNumber || "—"}
                        </TableCell>
                        <TableCell className="text-steel text-sm">
                          {lead.emails?.primaryEmail || "—"}
                        </TableCell>
                        <TableCell>
                          {lead.stage ? (
                            <Badge variant="info">{lead.stage}</Badge>
                          ) : (
                            <span className="text-steel">—</span>
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
          <Card folded>
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
                <p className="text-sm text-steel py-4 text-center font-mono">
                  CARREGANDO...
                </p>
              ) : bookings.length === 0 ? (
                <p className="text-sm text-steel py-4 text-center font-mono">
                  NENHUMA CONSULTA HOJE
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
                        className="flex items-start gap-4 pb-4 border-b border-graphite last:border-0 last:pb-0"
                      >
                        <div className="bg-ink text-white px-3 py-2 text-center min-w-[60px]">
                          <span className="font-mono text-sm font-bold">
                            {time}
                          </span>
                        </div>
                        <div className="flex-1">
                          <p className="font-medium">{attendee}</p>
                          <p className="text-sm text-steel">
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
                className="block w-full mt-6 px-6 py-3 text-center text-sm font-medium uppercase tracking-wider border border-graphite bg-white text-ink shadow-hard hover:bg-paper transition-all duration-100"
              >
                Ver Agenda Completa
              </a>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card className="mt-6 bg-ink text-white">
            <CardContent className="py-6">
              <div className="flex items-center gap-4 mb-4">
                <BarChart3 size={24} className="text-accent-orange" />
                <div>
                  <p className="font-mono text-[10px] uppercase text-white/60">
                    Conversão
                  </p>
                  <p className="text-3xl font-bold tabular-nums">
                    {metricsLoading ? "—" : `${metrics?.conversion_rate ?? 0}%`}
                  </p>
                </div>
              </div>
              <p className="text-sm text-white/60">
                Taxa de conversão leads → consultas agendadas.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </Shell>
  );
}
