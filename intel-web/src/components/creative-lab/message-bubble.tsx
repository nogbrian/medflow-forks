'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Copy, Check, User, Bot, Loader2, Download, ZoomIn } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogTrigger,
} from '@/components/ui/dialog';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  images?: string[];
  isThinking?: boolean;
}

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadImage = (imageUrl: string, index: number) => {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `generated-image-${index + 1}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (message.isThinking) {
    return (
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-orange-500/10">
          <Bot className="h-4 w-4 text-orange-500" />
        </div>
        <div className="flex items-center gap-2 rounded-lg bg-muted px-4 py-3">
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Pensando...</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex items-start gap-3',
        isUser && 'flex-row-reverse'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-primary/10' : 'bg-orange-500/10'
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-primary" />
        ) : (
          <Bot className="h-4 w-4 text-orange-500" />
        )}
      </div>

      {/* Content */}
      <div
        className={cn(
          'group relative max-w-[80%] rounded-lg px-4 py-3',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted'
        )}
      >
        {/* User uploaded images */}
        {isUser && message.images && message.images.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {message.images.map((img, idx) => (
              <Dialog key={idx}>
                <DialogTrigger asChild>
                  <button className="relative overflow-hidden rounded-md border border-white/20 transition-transform hover:scale-105">
                    <img
                      src={img}
                      alt={`Upload ${idx + 1}`}
                      className="h-20 w-auto object-cover"
                    />
                    <div className="absolute inset-0 flex items-center justify-center bg-black/0 transition-colors hover:bg-black/20">
                      <ZoomIn className="h-4 w-4 text-white opacity-0 transition-opacity group-hover:opacity-100" />
                    </div>
                  </button>
                </DialogTrigger>
                <DialogContent className="max-w-4xl">
                  <img
                    src={img}
                    alt={`Upload ${idx + 1}`}
                    className="w-full rounded-lg"
                  />
                </DialogContent>
              </Dialog>
            ))}
          </div>
        )}

        {/* Text content */}
        {message.content && (
          <div
            className={cn(
              'prose prose-sm max-w-none',
              isUser ? 'prose-invert' : 'dark:prose-invert'
            )}
          >
            <ReactMarkdown
              components={{
                // Custom code block styling
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  const isInline = !match;
                  return isInline ? (
                    <code
                      className={cn(
                        'rounded bg-black/10 px-1 py-0.5 text-sm',
                        isUser ? 'bg-white/10' : 'bg-black/10 dark:bg-white/10'
                      )}
                      {...props}
                    >
                      {children}
                    </code>
                  ) : (
                    <pre className="overflow-x-auto rounded-md bg-black/10 p-3 dark:bg-white/10">
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </pre>
                  );
                },
                // Custom link styling
                a({ href, children }) {
                  return (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-orange-500 underline hover:text-orange-600"
                    >
                      {children}
                    </a>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {/* Assistant generated images */}
        {!isUser && message.images && message.images.length > 0 && (
          <div className="mt-3 grid gap-3">
            {message.images.map((img, idx) => (
              <div key={idx} className="relative group/image">
                <Dialog>
                  <DialogTrigger asChild>
                    <button className="block w-full overflow-hidden rounded-lg border transition-transform hover:scale-[1.02]">
                      <img
                        src={img}
                        alt={`Generated ${idx + 1}`}
                        className="w-full"
                      />
                    </button>
                  </DialogTrigger>
                  <DialogContent className="max-w-4xl">
                    <img
                      src={img}
                      alt={`Generated ${idx + 1}`}
                      className="w-full rounded-lg"
                    />
                    <div className="mt-4 flex justify-end">
                      <Button
                        variant="outline"
                        onClick={() => handleDownloadImage(img, idx)}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>

                {/* Quick download button */}
                <Button
                  variant="secondary"
                  size="icon"
                  className="absolute bottom-2 right-2 h-8 w-8 opacity-0 transition-opacity group-hover/image:opacity-100"
                  onClick={() => handleDownloadImage(img, idx)}
                >
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* Copy button for assistant messages */}
        {!isUser && message.content && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute -right-10 top-0 h-8 w-8 opacity-0 transition-opacity group-hover:opacity-100"
            onClick={handleCopy}
          >
            {copied ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
