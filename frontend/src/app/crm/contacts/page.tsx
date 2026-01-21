"use client";

import {
  Search,
  Filter,
  Plus,
  MoreVertical,
  Phone,
  Mail,
  MessageSquare,
  Calendar,
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

/**
 * CRM Contacts Page
 *
 * Lista de contatos com filtros e ações rápidas.
 */

const contacts = [
  {
    id: "C-001",
    name: "Maria Silva",
    email: "maria.silva@email.com",
    phone: "+55 61 99999-0001",
    origin: "Instagram",
    status: "hot",
    lastContact: "21/01/2026",
    specialty: "Dermatologia",
  },
  {
    id: "C-002",
    name: "João Santos",
    email: "joao.santos@email.com",
    phone: "+55 61 99999-0002",
    origin: "WhatsApp",
    status: "warm",
    lastContact: "20/01/2026",
    specialty: "Estética",
  },
  {
    id: "C-003",
    name: "Ana Costa",
    email: "ana.costa@email.com",
    phone: "+55 61 99999-0003",
    origin: "Google Ads",
    status: "cold",
    lastContact: "18/01/2026",
    specialty: "Dermatologia",
  },
  {
    id: "C-004",
    name: "Pedro Lima",
    email: "pedro.lima@email.com",
    phone: "+55 61 99999-0004",
    origin: "Indicação",
    status: "hot",
    lastContact: "21/01/2026",
    specialty: "Cirurgia",
  },
  {
    id: "C-005",
    name: "Clara Souza",
    email: "clara.souza@email.com",
    phone: "+55 61 99999-0005",
    origin: "Site",
    status: "warm",
    lastContact: "19/01/2026",
    specialty: "Estética",
  },
];

export default function ContactsPage() {
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
                TOTAL_REGISTROS: {contacts.length} | ATIVOS: {contacts.filter(c => c.status !== 'cold').length}
              </p>
            </div>

            <Button>
              <Plus size={16} />
              Novo Contato
            </Button>
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
              Status
            </Button>
            <Button variant="secondary" size="sm">
              <Filter size={14} />
              Origem
            </Button>
            <Button variant="secondary" size="sm">
              <Filter size={14} />
              Especialidade
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 lg:p-8">
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Contato</TableHead>
                  <TableHead>Origem</TableHead>
                  <TableHead>Interesse</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Último Contato</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {contacts.map((contact) => (
                  <TableRow key={contact.id}>
                    <TableCell className="font-mono text-xs">
                      {contact.id}
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{contact.name}</p>
                        <p className="text-sm text-steel">{contact.email}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge>{contact.origin}</Badge>
                    </TableCell>
                    <TableCell className="text-steel">
                      {contact.specialty}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          contact.status === "hot"
                            ? "warning"
                            : contact.status === "warm"
                            ? "info"
                            : "default"
                        }
                      >
                        {contact.status.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-steel">
                      {contact.lastContact}
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
          </CardContent>
        </Card>

        {/* Pagination */}
        <div className="mt-4 flex items-center justify-between">
          <span className="font-mono text-xs text-steel">
            EXIBINDO 1-5 DE 5 REGISTROS
          </span>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" disabled>
              Anterior
            </Button>
            <Button variant="secondary" size="sm" disabled>
              Próximo
            </Button>
          </div>
        </div>
      </div>
    </Shell>
  );
}
