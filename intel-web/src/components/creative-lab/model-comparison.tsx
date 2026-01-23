'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Loader2, Zap, Clock, Check, X, Copy, RotateCcw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import { useWorkspaces } from '@/hooks/use-workspaces';
import { getFrontierModels, compareChatModels, type FrontierModel, type MultiModelResponse } from '@/lib/ai-api';

// Provider colors
const PROVIDER_COLORS: Record<string, string> = {
  openai: 'bg-green-500/10 border-green-500/30 text-green-600',
  anthropic: 'bg-orange-500/10 border-orange-500/30 text-orange-600',
  google: 'bg-blue-500/10 border-blue-500/30 text-blue-600',
  xai: 'bg-purple-500/10 border-purple-500/30 text-purple-600',
};

interface ModelComparisonProps {
  systemPrompt?: string;
}

export function ModelComparison({ systemPrompt }: ModelComparisonProps) {
  const { data: workspaces } = useWorkspaces();
  const workspaceId = workspaces?.[0]?.id;

  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [message, setMessage] = useState('');
  const [responses, setResponses] = useState<MultiModelResponse[]>([]);

  // Fetch available models
  const { data: modelsData, isLoading: isLoadingModels } = useQuery({
    queryKey: ['frontier-models'],
    queryFn: getFrontierModels,
  });

  // Compare mutation
  const compareMutation = useMutation({
    mutationFn: () =>
      compareChatModels(workspaceId!, selectedModels, message, undefined, systemPrompt),
    onSuccess: (data) => {
      setResponses(data.responses);
    },
  });

  const availableModels = modelsData?.models.filter((m) => m.available) || [];

  // Group models by provider
  const modelsByProvider = availableModels.reduce(
    (acc, model) => {
      if (!acc[model.provider]) acc[model.provider] = [];
      acc[model.provider].push(model);
      return acc;
    },
    {} as Record<string, FrontierModel[]>
  );

  const handleToggleModel = (modelKey: string) => {
    setSelectedModels((prev) =>
      prev.includes(modelKey) ? prev.filter((k) => k !== modelKey) : [...prev, modelKey]
    );
  };

  const handleCompare = () => {
    if (!workspaceId || selectedModels.length === 0 || !message.trim()) return;
    setResponses([]);
    compareMutation.mutate();
  };

  const handleCopyResponse = async (content: string) => {
    await navigator.clipboard.writeText(content);
  };

  const handleReset = () => {
    setResponses([]);
    setMessage('');
  };

  if (isLoadingModels) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Model Selection */}
      <div className="border-b p-4">
        <h3 className="font-medium mb-3">Selecione os modelos para comparar</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(modelsByProvider).map(([provider, models]) => (
            <div key={provider}>
              <div className="text-sm font-medium text-muted-foreground mb-2 capitalize">
                {provider}
              </div>
              <div className="space-y-2">
                {models.map((model) => (
                  <label
                    key={model.key}
                    className={cn(
                      'flex items-center gap-2 p-2 rounded border cursor-pointer transition-colors',
                      selectedModels.includes(model.key)
                        ? PROVIDER_COLORS[provider]
                        : 'hover:bg-muted'
                    )}
                  >
                    <Checkbox
                      checked={selectedModels.includes(model.key)}
                      onCheckedChange={() => handleToggleModel(model.key)}
                    />
                    <span className="text-sm">{model.display_name}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="border-b p-4">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Digite sua mensagem para comparar entre os modelos..."
          rows={3}
          className="mb-3"
        />
        <div className="flex gap-2">
          <Button
            onClick={handleCompare}
            disabled={
              selectedModels.length === 0 || !message.trim() || compareMutation.isPending
            }
            className="bg-orange-500 hover:bg-orange-600"
          >
            {compareMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Zap className="mr-2 h-4 w-4" />
            )}
            Comparar {selectedModels.length} modelo{selectedModels.length !== 1 ? 's' : ''}
          </Button>
          {responses.length > 0 && (
            <Button variant="outline" onClick={handleReset}>
              <RotateCcw className="mr-2 h-4 w-4" />
              Limpar
            </Button>
          )}
        </div>
      </div>

      {/* Responses Grid */}
      {responses.length > 0 && (
        <div className="flex-1 overflow-auto p-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {responses.map((response) => (
              <Card
                key={response.model_id}
                className={cn(
                  'relative',
                  response.error && 'border-destructive'
                )}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <span
                        className={cn(
                          'inline-flex items-center px-2 py-0.5 rounded text-xs',
                          PROVIDER_COLORS[response.provider]
                        )}
                      >
                        {response.display_name}
                      </span>
                    </span>
                    <span className="flex items-center gap-2 text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {response.latency_ms.toFixed(0)}ms
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {response.error ? (
                    <div className="flex items-center gap-2 text-destructive">
                      <X className="h-4 w-4" />
                      <span className="text-sm">{response.error}</span>
                    </div>
                  ) : (
                    <>
                      <div className="prose prose-sm dark:prose-invert max-w-none max-h-64 overflow-auto">
                        <ReactMarkdown>{response.content}</ReactMarkdown>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute top-2 right-2"
                        onClick={() => handleCopyResponse(response.content)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {responses.length === 0 && !compareMutation.isPending && (
        <div className="flex-1 flex items-center justify-center text-muted-foreground">
          <div className="text-center">
            <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Selecione modelos e envie uma mensagem para comparar</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {compareMutation.isPending && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">
              Consultando {selectedModels.length} modelo{selectedModels.length !== 1 ? 's' : ''}...
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
