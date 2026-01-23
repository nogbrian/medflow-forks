"use client";

import { useState } from "react";
import {
  Search,
  Filter,
  Plus,
  Phone,
  Mail,
  MessageSquare,
  Calendar,
  MoreVertical,
  RefreshCw,
} from "lucide-react";
import { Shell } from "@/components/layout";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useLeads } from "@/hooks";

/**
 * CRM Contacts Page
 *
 * Lista de contatos do Twenty CRM via API proxy.
 */

function getLeadName(lead: { name?: { firstName?: string; lastName?: string } }): string {
  if (!lead.name) return "—";
  return [lead.name.firstName, lead.name.lastName].filter(Boolean).join(" ") || "—";
}

export default function ContactsPage() {
  const [offset, setOffset] = useState(0);
  const limite = 20;

  const { data, loading, error, refetch } = useLeads({ limite, offset });
  const contacts = data?.data ?? [];
  const total = data?.total ?? 0;

  const hasNext = contacts.length === limite;
  const hasPrev = offset > 0;

  return (
    <Shell>
      {/* Page Header */}
      <div className="border-b border-graphite bg-white">
        <div className="px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight uppercase mb-1">
                Contatos
              </h1>
              <p className="font-mono text-sm text-steel">
                {loading
                  ? "CARREGANDO..."
                  : `TOTAL_REGISTROS: ${total} | OFFSET: ${offset}`}
              </p>
            </div>

            <div className="flex gap-2">
              <Button variant="secondary" size="sm" onClick={() => refetch()}>
                <RefreshCw size={14} />
                Atualizar
              </Button>
              <Button>
                <Plus size={16} />
                Novo Contato
              </Button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="px-6 lg:px-8 pb-4 flex flex-wrap gap-3">
          <div className="flex-1 min-w-[200px] max-w-md">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-steel" />
              <Input
                placeholder="Buscar por nome, email ou telefone..."
                className="pl-10"
              />
            </div>
          </div>

          <div className="flex gap-2">
            <Button variant="secondary" size="sm">
              <Filter size={14} />
              Etapa
            </Button>
            <Button variant="secondary" size="sm">
              <Filter size={14} />
              Origem
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 lg:p-8">
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <p className="text-sm text-steel py-12 text-center font-mono">
                CARREGANDO CONTATOS...
              </p>
            ) : error ? (
              <div className="py-12 text-center">
                <p className="text-sm text-steel font-mono mb-4">
                  ERRO AO CARREGAR CONTATOS
                </p>
                <Button variant="secondary" size="sm" onClick={() => refetch()}>
                  Tentar Novamente
                </Button>
              </div>
            ) : contacts.length === 0 ? (
              <p className="text-sm text-steel py-12 text-center font-mono">
                NENHUM CONTATO ENCONTRADO
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Contato</TableHead>
                    <TableHead>Telefone</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Etapa</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {contacts.map((contact, idx) => (
                    <TableRow key={contact.id || idx}>
                      <TableCell>
                        <p className="font-medium">{getLeadName(contact)}</p>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-steel">
                        {contact.phones?.primaryPhoneNumber || "—"}
                      </TableCell>
                      <TableCell className="text-sm text-steel">
                        {contact.emails?.primaryEmail || "—"}
                      </TableCell>
                      <TableCell>
                        {contact.stage ? (
                          <Badge variant="info">{contact.stage}</Badge>
                        ) : (
                          <span className="text-steel">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex justify-end gap-1">
                          <button
                            className="p-2 hover:bg-paper transition-colors"
                            aria-label="Ligar"
                          >
                            <Phone size={14} />
                          </button>
                          <button
                            className="p-2 hover:bg-paper transition-colors"
                            aria-label="Email"
                          >
                            <Mail size={14} />
                          </button>
                          <button
                            className="p-2 hover:bg-paper transition-colors"
                            aria-label="WhatsApp"
                          >
                            <MessageSquare size={14} />
                          </button>
                          <button
                            className="p-2 hover:bg-paper transition-colors"
                            aria-label="Agendar"
                          >
                            <Calendar size={14} />
                          </button>
                          <button
                            className="p-2 hover:bg-paper transition-colors"
                            aria-label="Mais opções"
                          >
                            <MoreVertical size={14} />
                          </button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Pagination */}
        {!loading && contacts.length > 0 && (
          <div className="mt-4 flex items-center justify-between">
            <span className="font-mono text-xs text-steel">
              EXIBINDO {offset + 1}-{offset + contacts.length} DE {total} REGISTROS
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={!hasPrev}
                onClick={() => setOffset(Math.max(0, offset - limite))}
              >
                Anterior
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={!hasNext}
                onClick={() => setOffset(offset + limite)}
              >
                Próximo
              </Button>
            </div>
          </div>
        )}
      </div>
    </Shell>
  );
}
