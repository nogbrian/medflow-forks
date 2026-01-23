'use client';

import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Heart, MessageCircle, TrendingUp, Play, Image as ImageIcon, Copy, ExternalLink } from 'lucide-react';
import type { PostWithEngagement } from '@/types/database';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { getProxiedImageUrl } from '@/lib/image-proxy';

interface PostCardProps {
  post: PostWithEngagement;
}

export function PostCard({ post }: PostCardProps) {
  const [imageError, setImageError] = useState(false);

  const getTypeIcon = () => {
    if (post.is_reel) return <Play className="h-3 w-3" />;
    if (post.type === 'Sidecar') return <Copy className="h-3 w-3" />;
    return <ImageIcon className="h-3 w-3" />;
  };

  const getTypeLabel = () => {
    if (post.is_reel) return 'Reel';
    if (post.type === 'Sidecar') return 'Carrossel';
    return 'Post';
  };

  const getEngagementColor = (rate: number) => {
    if (rate >= 6) return 'text-green-600 bg-green-50';
    if (rate >= 3) return 'text-blue-600 bg-blue-50';
    if (rate >= 1) return 'text-yellow-600 bg-yellow-50';
    return 'text-gray-600 bg-gray-50';
  };

  return (
    <Card className="overflow-hidden hover:shadow-md transition-shadow">
      <div className="relative aspect-square bg-muted">
        {post.display_url && !imageError ? (
          <img
            src={getProxiedImageUrl(post.display_url) || post.display_url}
            alt={post.caption?.substring(0, 50) || 'Post'}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <ImageIcon className="h-12 w-12 text-muted-foreground" />
          </div>
        )}

        <Badge variant="secondary" className="absolute top-2 left-2 flex items-center gap-1">
          {getTypeIcon()}
          {getTypeLabel()}
        </Badge>

        <Badge className={`absolute top-2 right-2 ${getEngagementColor(post.engagement_rate)}`}>
          <TrendingUp className="h-3 w-3 mr-1" />
          {post.engagement_rate.toFixed(2)}%
        </Badge>

        {post.is_pinned && (
          <Badge variant="default" className="absolute bottom-2 left-2">
            📌 Fixado
          </Badge>
        )}
      </div>

      <CardContent className="p-4">
        <div className="flex items-center gap-4 text-sm mb-3">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger className="flex items-center gap-1">
                <Heart className="h-4 w-4 text-red-500" />
                <span className="font-medium">{post.likes_count.toLocaleString()}</span>
              </TooltipTrigger>
              <TooltipContent>Curtidas</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger className="flex items-center gap-1">
                <MessageCircle className="h-4 w-4 text-blue-500" />
                <span className="font-medium">{post.comments_count.toLocaleString()}</span>
              </TooltipTrigger>
              <TooltipContent>Comentários</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {post.video_view_count && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger className="flex items-center gap-1">
                  <Play className="h-4 w-4 text-purple-500" />
                  <span className="font-medium">{post.video_view_count.toLocaleString()}</span>
                </TooltipTrigger>
                <TooltipContent>Visualizações</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>

        {post.caption && (
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
            {post.caption}
          </p>
        )}

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {post.posted_at
              ? format(new Date(post.posted_at), "d 'de' MMM, yyyy", { locale: ptBR })
              : 'Data desconhecida'}
          </span>
          <a
            href={post.url || `https://instagram.com/p/${post.short_code}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 hover:text-foreground transition-colors"
          >
            Ver no Instagram
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
