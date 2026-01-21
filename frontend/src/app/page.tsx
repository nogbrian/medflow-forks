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

/**
 * Dashboard Principal
 *
 * Visão geral do sistema com métricas e atividades recentes.
 * Estilo: Relatório técnico / Bloomberg Terminal.
 */

const recentLeads = [
  { id: "L-001", name: "Maria Silva", origin: "Instagram", status: "hot", date: "21/01/2026" },
  { id: "L-002", name: "João Santos", origin: "WhatsApp", status: "warm", date: "21/01/2026" },
  { id: "L-003", name: "Ana Costa", origin: "Google Ads", status: "cold", date: "20/01/2026" },
  { id: "L-004", name: "Pedro Lima", origin: "Indicação", status: "hot", date: "20/01/2026" },
  { id: "L-005", name: "Clara Souza", origin: "Site", status: "warm", date: "19/01/2026" },
];

const upcomingAppointments = [
  { time: "09:00", patient: "Maria Silva", type: "Consulta", doctor: "Dr. Roberto" },
  { time: "10:30", patient: "João Santos", type: "Retorno", doctor: "Dra. Ana" },
  { time: "14:00", patient: "Pedro Lima", type: "Avaliação", doctor: "Dr. Roberto" },
];

export default function DashboardPage() {
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
              ÚLTIMA_ATUALIZAÇÃO: 21/01/2026 08:30:00
            </p>
          </div>

          <div className="flex gap-3">
            <Button variant="secondary" size="sm">
              Exportar Relatório
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
            value="+420"
            change={{ value: 12, trend: "up" }}
            icon={<Users size={24} />}
          />
          <Metric
            label="Consultas Agendadas"
            value="89"
            change={{ value: 8, trend: "up" }}
            icon={<Calendar size={24} />}
          />
          <Metric
            label="Conversas Ativas"
            value="34"
            change={{ value: -5, trend: "down" }}
            icon={<MessageSquare size={24} />}
          />
          <Metric
            label="Taxa de Conversão"
            value="21.2%"
            change={{ value: 3, trend: "up" }}
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
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Nome</TableHead>
                    <TableHead>Origem</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Data</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentLeads.map((lead) => (
                    <TableRow key={lead.id}>
                      <TableCell className="font-mono text-xs">
                        {lead.id}
                      </TableCell>
                      <TableCell className="font-medium">{lead.name}</TableCell>
                      <TableCell className="text-steel">{lead.origin}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            lead.status === "hot"
                              ? "warning"
                              : lead.status === "warm"
                              ? "info"
                              : "default"
                          }
                        >
                          {lead.status.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-steel">
                        {lead.date}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
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
                  3 Consultas
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {upcomingAppointments.map((apt, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-4 pb-4 border-b border-graphite last:border-0 last:pb-0"
                  >
                    <div className="bg-ink text-white px-3 py-2 text-center min-w-[60px]">
                      <span className="font-mono text-sm font-bold">
                        {apt.time}
                      </span>
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{apt.patient}</p>
                      <p className="text-sm text-steel">
                        {apt.type} • {apt.doctor}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <Button variant="secondary" className="w-full mt-6">
                Ver Agenda Completa
              </Button>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card className="mt-6 bg-ink text-white">
            <CardContent className="py-6">
              <div className="flex items-center gap-4 mb-4">
                <BarChart3 size={24} className="text-accent-orange" />
                <div>
                  <p className="font-mono text-[10px] uppercase text-white/60">
                    CPA Atual
                  </p>
                  <p className="text-3xl font-bold tabular-nums">R$ 12,40</p>
                </div>
              </div>
              <p className="text-sm text-white/60">
                Custo por aquisição otimizado nos últimos 30 dias.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </Shell>
  );
}
