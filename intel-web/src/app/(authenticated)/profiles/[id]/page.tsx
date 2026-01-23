'use client';

import { use, useState } from 'react';
import { useProfile } from '@/hooks/use-profiles';
import { useAnalytics } from '@/hooks/use-analytics';
import { useTriggerScrape } from '@/hooks/use-scraping';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatCard } from '@/components/ui/stat-card';
import { PostCard } from '@/components/posts/post-card';
import { EmptyState } from '@/components/ui/empty-state';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ArrowLeft,
  RefreshCw,
  TrendingUp,
  Heart,
  MessageCircle,
  Hash,
  AtSign,
  Instagram,
  ExternalLink,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  BarChart3,
} from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';
import type { OrderBy, SortDirection, PostType } from '@/types/database';
import { getProxiedImageUrl } from '@/lib/image-proxy';

export default function ProfileDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [tab, setTab] = useState('posts');
  const [orderBy, setOrderBy] = useState<OrderBy>('engagement');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [imageError, setImageError] = useState(false);

  // Map tab to PostType for API - only filter when on posts or reels tab
  const postType: PostType = tab === 'posts' || tab === 'reels' ? (tab as PostType) : 'all';

  const { data: profile, isLoading: profileLoading } = useProfile(id);
  const { data: analytics, isLoading: analyticsLoading } = useAnalytics(id, {
    order_by: orderBy,
    sort_direction: sortDirection,
    type: postType,
  });
  const scrapeMutation = useTriggerScrape();

  const toggleSortDirection = () => {
    setSortDirection((prev) => (prev === 'desc' ? 'asc' : 'desc'));
  };

  const handleScrape = async () => {
    try {
      await scrapeMutation.mutateAsync({
        action: 'full',
        profile_id: id,
      });
      toast.success('Scraping iniciado!');
    } catch {
      toast.error('Erro ao iniciar scraping');
    }
  };

  if (profileLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-48" />
          <div className="h-32 bg-muted rounded" />
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-8">
        <EmptyState
          icon={Instagram}
          title="Perfil não encontrado"
          description="O perfil solicitado não existe."
          action={{ label: 'Voltar', onClick: () => window.history.back() }}
        />
      </div>
    );
  }

  const stats = analytics?.stats;
  const posts = analytics?.posts || [];

  return (
    <div className="p-8">
      <div className="flex items-center gap-4 mb-8">
        <Link href={`/workspaces/${profile.workspace_id}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex items-center gap-4 flex-1">
          {profile.profile_pic_url && !imageError ? (
            <img
              src={getProxiedImageUrl(profile.profile_pic_url) || profile.profile_pic_url}
              alt={profile.username}
              className="w-16 h-16 rounded-full object-cover"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Instagram className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              @{profile.username}
              {profile.is_verified && <Badge variant="secondary">✓ Verificado</Badge>}
            </h1>
            {profile.full_name && (
              <p className="text-muted-foreground">{profile.full_name}</p>
            )}
            {profile.biography && (
              <p className="text-sm mt-1 max-w-xl">{profile.biography}</p>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <a
              href={`https://instagram.com/${profile.username}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Ver no Instagram
            </a>
          </Button>
          <Button onClick={handleScrape} disabled={scrapeMutation.isPending}>
            <RefreshCw className={`h-4 w-4 mr-2 ${scrapeMutation.isPending ? 'animate-spin' : ''}`} />
            {scrapeMutation.isPending ? 'Scraping...' : 'Atualizar Dados'}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <StatCard
          title="Seguidores"
          value={profile.followers_count.toLocaleString()}
          icon={Instagram}
        />
        <StatCard
          title="Taxa de Engagement"
          value={stats ? `${stats.avg_engagement_rate.toFixed(2)}%` : '--'}
          description={stats ? `Min: ${stats.min_engagement_rate.toFixed(2)}% | Max: ${stats.max_engagement_rate.toFixed(2)}%` : undefined}
          icon={TrendingUp}
        />
        <StatCard
          title="Likes"
          value={stats ? Math.round(stats.avg_likes).toLocaleString() : '--'}
          description={stats ? `Min: ${stats.min_likes.toLocaleString()} | Max: ${stats.max_likes.toLocaleString()}` : undefined}
          icon={Heart}
        />
        <StatCard
          title="Comentários"
          value={stats ? Math.round(stats.avg_comments).toLocaleString() : '--'}
          description={stats ? `Min: ${stats.min_comments.toLocaleString()} | Max: ${stats.max_comments.toLocaleString()}` : undefined}
          icon={MessageCircle}
        />
      </div>

      {stats && (
        <Card className="mb-8">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Estatísticas Detalhadas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-6 text-sm">
              <div>
                <h4 className="font-medium text-muted-foreground mb-2">Likes</h4>
                <div className="space-y-1">
                  <div className="flex justify-between"><span>Média:</span><span className="font-medium">{Math.round(stats.avg_likes).toLocaleString()}</span></div>
                  <div className="flex justify-between"><span>Mínimo:</span><span>{stats.min_likes.toLocaleString()}</span></div>
                  <div className="flex justify-between"><span>Máximo:</span><span>{stats.max_likes.toLocaleString()}</span></div>
                  <div className="flex justify-between"><span>Desvio Padrão:</span><span>{Math.round(stats.std_dev_likes).toLocaleString()}</span></div>
                </div>
              </div>
              <div>
                <h4 className="font-medium text-muted-foreground mb-2">Comentários</h4>
                <div className="space-y-1">
                  <div className="flex justify-between"><span>Média:</span><span className="font-medium">{Math.round(stats.avg_comments).toLocaleString()}</span></div>
                  <div className="flex justify-between"><span>Mínimo:</span><span>{stats.min_comments.toLocaleString()}</span></div>
                  <div className="flex justify-between"><span>Máximo:</span><span>{stats.max_comments.toLocaleString()}</span></div>
                  <div className="flex justify-between"><span>Desvio Padrão:</span><span>{Math.round(stats.std_dev_comments).toLocaleString()}</span></div>
                </div>
              </div>
              <div>
                <h4 className="font-medium text-muted-foreground mb-2">Engagement Rate</h4>
                <div className="space-y-1">
                  <div className="flex justify-between"><span>Média:</span><span className="font-medium">{stats.avg_engagement_rate.toFixed(2)}%</span></div>
                  <div className="flex justify-between"><span>Mínimo:</span><span>{stats.min_engagement_rate.toFixed(2)}%</span></div>
                  <div className="flex justify-between"><span>Máximo:</span><span>{stats.max_engagement_rate.toFixed(2)}%</span></div>
                  <div className="flex justify-between"><span>Desvio Padrão:</span><span>{stats.std_dev_engagement_rate.toFixed(2)}%</span></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="posts">Posts ({stats?.total_posts || 0})</TabsTrigger>
          <TabsTrigger value="reels">Reels ({stats?.total_reels || 0})</TabsTrigger>
          <TabsTrigger value="hashtags">Hashtags</TabsTrigger>
          <TabsTrigger value="mentions">Menções</TabsTrigger>
        </TabsList>

        <TabsContent value="posts" className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-muted-foreground">
              {posts.length} posts encontrados
            </p>
            <div className="flex items-center gap-2">
              <Select value={orderBy} onValueChange={(value) => setOrderBy(value as OrderBy)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Ordenar por" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="engagement">Engagement</SelectItem>
                  <SelectItem value="likes">Likes</SelectItem>
                  <SelectItem value="comments">Comentários</SelectItem>
                  <SelectItem value="date">Data</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="icon"
                onClick={toggleSortDirection}
                title={sortDirection === 'desc' ? 'Maior para menor' : 'Menor para maior'}
              >
                {sortDirection === 'desc' ? (
                  <ArrowDown className="h-4 w-4" />
                ) : (
                  <ArrowUp className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
          {analyticsLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-64 bg-muted rounded animate-pulse" />
              ))}
            </div>
          ) : posts.length === 0 ? (
            <EmptyState
              icon={Instagram}
              title="Nenhum post"
              description="Faça o scraping para carregar os posts."
            />
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {posts.map(post => (
                <PostCard key={post.id} post={post} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="reels" className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-muted-foreground">
              {posts.length} reels encontrados
            </p>
            <div className="flex items-center gap-2">
              <Select value={orderBy} onValueChange={(value) => setOrderBy(value as OrderBy)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Ordenar por" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="engagement">Engagement</SelectItem>
                  <SelectItem value="likes">Likes</SelectItem>
                  <SelectItem value="comments">Comentários</SelectItem>
                  <SelectItem value="views">Visualizações</SelectItem>
                  <SelectItem value="date">Data</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="icon"
                onClick={toggleSortDirection}
                title={sortDirection === 'desc' ? 'Maior para menor' : 'Menor para maior'}
              >
                {sortDirection === 'desc' ? (
                  <ArrowDown className="h-4 w-4" />
                ) : (
                  <ArrowUp className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
          {analyticsLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-64 bg-muted rounded animate-pulse" />
              ))}
            </div>
          ) : posts.length === 0 ? (
            <EmptyState
              icon={Instagram}
              title="Nenhum reel"
              description="Faça o scraping para carregar os reels."
            />
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {posts.map(post => (
                <PostCard key={post.id} post={post} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="hashtags" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Hash className="h-5 w-5" />
                Top Hashtags
              </CardTitle>
              <CardDescription>Hashtags mais usadas e com melhor performance</CardDescription>
            </CardHeader>
            <CardContent>
              {analytics?.top_hashtags?.length === 0 ? (
                <p className="text-muted-foreground">Nenhuma hashtag encontrada</p>
              ) : (
                <div className="space-y-2">
                  {analytics?.top_hashtags?.map((h, i) => (
                    <div key={h.tag} className="flex items-center justify-between p-2 rounded hover:bg-muted">
                      <span className="font-medium">#{h.tag}</span>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{h.usage_count}x usado</span>
                        <span>{h.avg_engagement_rate.toFixed(2)}% eng.</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="mentions" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AtSign className="h-5 w-5" />
                Top Menções
              </CardTitle>
              <CardDescription>Perfis mais mencionados</CardDescription>
            </CardHeader>
            <CardContent>
              {analytics?.top_mentions?.length === 0 ? (
                <p className="text-muted-foreground">Nenhuma menção encontrada</p>
              ) : (
                <div className="space-y-2">
                  {analytics?.top_mentions?.map((m, i) => (
                    <div key={m.username} className="flex items-center justify-between p-2 rounded hover:bg-muted">
                      <a
                        href={`https://instagram.com/${m.username}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium text-primary hover:underline"
                      >
                        @{m.username}
                      </a>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{m.usage_count}x mencionado</span>
                        <span>{m.avg_engagement_rate.toFixed(2)}% eng.</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
