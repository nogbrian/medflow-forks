'use client';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

type Provider = 'gemini' | 'openai' | 'xai' | 'anthropic';

interface ProviderSelectorProps {
  value: Provider;
  onChange: (value: Provider) => void;
}

const providers = [
  {
    id: 'openai' as const,
    name: 'OpenAI',
    description: 'GPT-5.2 + GPT Image 1.5',
    icon: '🤖',
  },
  {
    id: 'anthropic' as const,
    name: 'Claude',
    description: 'Claude Opus 4.5',
    icon: '🧠',
  },
  {
    id: 'gemini' as const,
    name: 'Gemini',
    description: 'Gemini 3 Flash',
    icon: '✨',
  },
  {
    id: 'xai' as const,
    name: 'Grok',
    description: 'Grok 4.1 Fast',
    icon: '🚀',
  },
];

export function ProviderSelector({ value, onChange }: ProviderSelectorProps) {
  const selectedProvider = providers.find((p) => p.id === value);

  return (
    <Select value={value} onValueChange={(v) => onChange(v as Provider)}>
      <SelectTrigger className="w-[160px]">
        <SelectValue>
          <span className="flex items-center gap-2">
            <span>{selectedProvider?.icon}</span>
            <span>{selectedProvider?.name}</span>
          </span>
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {providers.map((provider) => (
          <SelectItem key={provider.id} value={provider.id}>
            <div className="flex items-center gap-2">
              <span>{provider.icon}</span>
              <div>
                <div className="font-medium">{provider.name}</div>
                <div className="text-xs text-muted-foreground">
                  {provider.description}
                </div>
              </div>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
