'use server';

import { prisma } from './prisma';
import type {
  Workspace,
  Profile,
  AnalyticsResponse,
  TriggerScrapeResponse,
  PostFilters,
  ProfileSummary,
  ScrapeRun,
} from '@/types/database';

function toWorkspace(w: {
  id: string;
  name: string;
  description: string | null;
  color: string;
  createdAt: Date;
  updatedAt: Date;
}): Workspace {
  return {
    id: w.id,
    name: w.name,
    description: w.description,
    color: w.color,
    created_at: w.createdAt.toISOString(),
    updated_at: w.updatedAt.toISOString(),
  };
}

function toProfile(p: {
  id: string;
  workspaceId: string;
  instagramId: string | null;
  username: string;
  fullName: string | null;
  biography: string | null;
  externalUrl: string | null;
  followersCount: number;
  followsCount: number;
  postsCount: number;
  isVerified: boolean;
  isBusinessAccount: boolean;
  businessCategory: string | null;
  profilePicUrl: string | null;
  isActive: boolean;
  lastScrapedAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
}): Profile {
  return {
    id: p.id,
    workspace_id: p.workspaceId,
    instagram_id: p.instagramId,
    username: p.username,
    full_name: p.fullName,
    biography: p.biography,
    external_url: p.externalUrl,
    followers_count: p.followersCount,
    follows_count: p.followsCount,
    posts_count: p.postsCount,
    is_verified: p.isVerified,
    is_business_account: p.isBusinessAccount,
    business_category: p.businessCategory,
    profile_pic_url: p.profilePicUrl,
    is_active: p.isActive,
    last_scraped_at: p.lastScrapedAt?.toISOString() || null,
    created_at: p.createdAt.toISOString(),
    updated_at: p.updatedAt.toISOString(),
  };
}

function toScrapeRun(s: {
  id: string;
  profileId: string;
  status: string;
  scrapeType: string | null;
  postsScraped: number;
  reelsScraped: number;
  errorMessage: string | null;
  startedAt: Date | null;
  completedAt: Date | null;
  createdAt: Date;
}): ScrapeRun {
  return {
    id: s.id,
    profile_id: s.profileId,
    status: s.status as ScrapeRun['status'],
    scrape_type: s.scrapeType || '',
    posts_scraped: s.postsScraped,
    reels_scraped: s.reelsScraped,
    error_message: s.errorMessage,
    started_at: s.startedAt?.toISOString() || null,
    completed_at: s.completedAt?.toISOString() || null,
    created_at: s.createdAt.toISOString(),
  };
}

export async function getWorkspaces(): Promise<Workspace[]> {
  const workspaces = await prisma.workspace.findMany({
    orderBy: { name: 'asc' },
  });
  return workspaces.map(toWorkspace);
}

export async function getWorkspace(id: string): Promise<Workspace | null> {
  const workspace = await prisma.workspace.findUnique({
    where: { id },
  });
  return workspace ? toWorkspace(workspace) : null;
}

export async function createWorkspace(workspace: {
  name: string;
  description?: string;
  color?: string;
}): Promise<Workspace> {
  const created = await prisma.workspace.create({
    data: {
      name: workspace.name,
      description: workspace.description || null,
      color: workspace.color || '#6366f1',
    },
  });
  return toWorkspace(created);
}

export async function deleteWorkspace(id: string): Promise<void> {
  await prisma.workspace.delete({
    where: { id },
  });
}

export async function getProfiles(workspaceId?: string): Promise<Profile[]> {
  const profiles = await prisma.profile.findMany({
    where: workspaceId ? { workspaceId } : undefined,
    orderBy: { username: 'asc' },
  });
  return profiles.map(toProfile);
}

export async function getProfile(id: string): Promise<Profile | null> {
  const profile = await prisma.profile.findUnique({
    where: { id },
  });
  return profile ? toProfile(profile) : null;
}

export async function getProfileSummaries(workspaceId: string): Promise<ProfileSummary[]> {
  const profiles = await prisma.profile.findMany({
    where: { workspaceId },
    include: {
      workspace: true,
      posts: {
        select: {
          isReel: true,
          likesCount: true,
          commentsCount: true,
          postedAt: true,
        },
      },
    },
    orderBy: { username: 'asc' },
  });

  return profiles.map((p) => {
    const totalPosts = p.posts.filter((post) => !post.isReel).length;
    const totalReels = p.posts.filter((post) => post.isReel).length;
    const totalEngagement = p.posts.reduce(
      (sum, post) => sum + post.likesCount + post.commentsCount,
      0
    );
    const avgEngagementRate =
      p.followersCount > 0 && p.posts.length > 0
        ? (totalEngagement / p.posts.length / p.followersCount) * 100
        : 0;

    const sortedPosts = p.posts
      .filter((post) => post.postedAt)
      .sort((a, b) => (b.postedAt?.getTime() || 0) - (a.postedAt?.getTime() || 0));
    const lastPostDate = sortedPosts[0]?.postedAt?.toISOString() || null;

    return {
      ...toProfile(p),
      workspace_name: p.workspace.name,
      workspace_color: p.workspace.color,
      total_posts: totalPosts,
      total_reels: totalReels,
      avg_engagement_rate: avgEngagementRate,
      last_post_date: lastPostDate,
    };
  });
}

export async function deleteProfile(id: string): Promise<void> {
  await prisma.profile.delete({
    where: { id },
  });
}

export async function getProfileAnalytics(
  profileId: string,
  filters: Partial<PostFilters> = {}
): Promise<AnalyticsResponse> {
  const orderBy = filters.order_by || 'engagement';
  const sortDirection = filters.sort_direction || 'desc';
  const limit = filters.limit || 500;
  const type = filters.type || 'all';
  const dateFrom = filters.date_from;
  const dateTo = filters.date_to;

  const profile = await prisma.profile.findUnique({
    where: { id: profileId },
  });

  if (!profile) {
    throw new Error('Profile not found');
  }

  // Build date filter
  const dateFilter: { postedAt?: { gte?: Date; lte?: Date } } = {};
  if (dateFrom) {
    dateFilter.postedAt = { ...dateFilter.postedAt, gte: new Date(dateFrom) };
  }
  if (dateTo) {
    dateFilter.postedAt = { ...dateFilter.postedAt, lte: new Date(dateTo) };
  }

  // Build type filter
  const typeFilter: { isReel?: boolean } = {};
  if (type === 'posts') {
    typeFilter.isReel = false;
  } else if (type === 'reels') {
    typeFilter.isReel = true;
  }

  // Get all posts for statistics calculation
  const allPosts = await prisma.post.findMany({
    where: {
      profileId,
      ...dateFilter,
    },
    select: {
      likesCount: true,
      commentsCount: true,
      isReel: true,
    },
  });

  const postsCount = allPosts.filter((p) => !p.isReel).length;
  const reelsCount = allPosts.filter((p) => p.isReel).length;

  // Calculate statistics
  const likesValues = allPosts.map((p) => p.likesCount);
  const commentsValues = allPosts.map((p) => p.commentsCount);
  const engagementRates = allPosts.map((p) =>
    profile.followersCount > 0
      ? ((p.likesCount + p.commentsCount) / profile.followersCount) * 100
      : 0
  );

  const calcStats = (values: number[]) => {
    if (values.length === 0) {
      return { min: 0, max: 0, avg: 0, stdDev: 0 };
    }
    const min = Math.min(...values);
    const max = Math.max(...values);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const variance =
      values.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);
    return { min, max, avg, stdDev };
  };

  const likesStats = calcStats(likesValues);
  const commentsStats = calcStats(commentsValues);
  const engagementStats = calcStats(engagementRates);

  // Build order by clause
  type SortDir = 'asc' | 'desc';
  type OrderByClause = { likesCount?: SortDir; commentsCount?: SortDir; postedAt?: SortDir; videoViewCount?: SortDir };
  const dir: SortDir = sortDirection;
  const orderByClause: OrderByClause =
    orderBy === 'likes'
      ? { likesCount: dir }
      : orderBy === 'comments'
        ? { commentsCount: dir }
        : orderBy === 'date'
          ? { postedAt: dir }
          : orderBy === 'views'
            ? { videoViewCount: dir }
            : { likesCount: dir };

  // Get posts with profile data
  const posts = await prisma.post.findMany({
    where: {
      profileId,
      ...dateFilter,
      ...typeFilter,
    },
    orderBy: orderByClause,
    take: limit,
    include: {
      profile: {
        select: {
          username: true,
          fullName: true,
          followersCount: true,
          isVerified: true,
        },
      },
    },
  });

  // Transform posts and add engagement data
  const postsWithEngagement = posts.map((post) => {
    const engagementAbsolute = post.likesCount + post.commentsCount;
    const engagementRate =
      post.profile.followersCount > 0
        ? (engagementAbsolute / post.profile.followersCount) * 100
        : 0;

    return {
      id: post.id,
      profile_id: post.profileId,
      instagram_id: post.instagramId,
      short_code: post.shortCode,
      type: post.type as 'Image' | 'Video' | 'Sidecar',
      url: post.url,
      display_url: post.displayUrl,
      caption: post.caption,
      likes_count: post.likesCount,
      comments_count: post.commentsCount,
      video_view_count: post.videoViewCount,
      video_play_count: post.videoPlayCount,
      video_duration: post.videoDuration,
      is_reel: post.isReel,
      is_pinned: post.isPinned,
      is_sponsored: post.isSponsored,
      is_comments_disabled: post.isCommentsDisabled,
      location_name: post.locationName,
      location_id: post.locationId,
      alt_text: post.altText,
      posted_at: post.postedAt?.toISOString() || null,
      scraped_at: post.scrapedAt.toISOString(),
      created_at: post.createdAt.toISOString(),
      updated_at: post.updatedAt.toISOString(),
      profile_username: post.profile.username,
      profile_full_name: post.profile.fullName,
      profile_followers: post.profile.followersCount,
      profile_is_verified: post.profile.isVerified,
      engagement_absolute: engagementAbsolute,
      engagement_rate: engagementRate,
    };
  });

  // Sort by engagement if needed
  if (orderBy === 'engagement') {
    postsWithEngagement.sort((a, b) =>
      sortDirection === 'desc'
        ? b.engagement_rate - a.engagement_rate
        : a.engagement_rate - b.engagement_rate
    );
  }

  // Get top hashtags
  const topHashtags = await prisma.$queryRaw<
    { tag: string; usage_count: bigint; avg_likes: number; avg_engagement_rate: number }[]
  >`
    SELECT
      h.tag,
      COUNT(*)::bigint as usage_count,
      AVG(p.likes_count)::float as avg_likes,
      CASE
        WHEN pr.followers_count > 0
        THEN AVG((p.likes_count + p.comments_count)::float / pr.followers_count * 100)
        ELSE 0
      END as avg_engagement_rate
    FROM hashtags h
    JOIN posts p ON h.post_id = p.id
    JOIN profiles pr ON p.profile_id = pr.id
    WHERE p.profile_id = ${profileId}::uuid
    GROUP BY h.tag, pr.followers_count
    ORDER BY usage_count DESC
    LIMIT 20
  `;

  // Get top mentions
  const topMentions = await prisma.$queryRaw<
    { username: string; usage_count: bigint; avg_likes: number; avg_engagement_rate: number }[]
  >`
    SELECT
      m.username,
      COUNT(*)::bigint as usage_count,
      AVG(p.likes_count)::float as avg_likes,
      CASE
        WHEN pr.followers_count > 0
        THEN AVG((p.likes_count + p.comments_count)::float / pr.followers_count * 100)
        ELSE 0
      END as avg_engagement_rate
    FROM mentions m
    JOIN posts p ON m.post_id = p.id
    JOIN profiles pr ON p.profile_id = pr.id
    WHERE p.profile_id = ${profileId}::uuid
    GROUP BY m.username, pr.followers_count
    ORDER BY usage_count DESC
    LIMIT 20
  `;

  return {
    success: true,
    profile: {
      id: profile.id,
      workspace_id: profile.workspaceId,
      instagram_id: profile.instagramId,
      username: profile.username,
      full_name: profile.fullName,
      biography: profile.biography,
      external_url: profile.externalUrl,
      followers_count: profile.followersCount,
      follows_count: profile.followsCount,
      posts_count: profile.postsCount,
      is_verified: profile.isVerified,
      is_business_account: profile.isBusinessAccount,
      business_category: profile.businessCategory,
      profile_pic_url: profile.profilePicUrl,
      is_active: profile.isActive,
      last_scraped_at: profile.lastScrapedAt?.toISOString() || null,
      created_at: profile.createdAt.toISOString(),
      updated_at: profile.updatedAt.toISOString(),
    },
    stats: {
      total_posts: postsCount,
      total_reels: reelsCount,
      avg_likes: likesStats.avg,
      avg_comments: commentsStats.avg,
      avg_engagement_rate: engagementStats.avg,
      min_likes: likesStats.min,
      max_likes: likesStats.max,
      std_dev_likes: likesStats.stdDev,
      min_comments: commentsStats.min,
      max_comments: commentsStats.max,
      std_dev_comments: commentsStats.stdDev,
      min_engagement_rate: engagementStats.min,
      max_engagement_rate: engagementStats.max,
      std_dev_engagement_rate: engagementStats.stdDev,
      period: { from: dateFrom || null, to: dateTo || null },
    },
    top_hashtags: topHashtags.map((h) => ({
      tag: h.tag,
      usage_count: Number(h.usage_count),
      avg_likes: h.avg_likes,
      avg_engagement_rate: h.avg_engagement_rate,
    })),
    top_mentions: topMentions.map((m) => ({
      username: m.username,
      usage_count: Number(m.usage_count),
      avg_likes: m.avg_likes,
      avg_engagement_rate: m.avg_engagement_rate,
    })),
    posts: postsWithEngagement,
    meta: {
      filters: { order_by: orderBy, limit, type, date_from: dateFrom || null, date_to: dateTo || null },
      posts_returned: postsWithEngagement.length,
    },
  };
}

export async function triggerScrape(params: {
  action: 'full' | 'posts_only' | 'reels_only' | 'profile_only';
  profile_id?: string;
  username?: string;
  workspace_id?: string;
  save_profile?: boolean;
}): Promise<TriggerScrapeResponse> {
  const n8nBaseUrl = process.env.N8N_WEBHOOK_BASE_URL;

  if (!n8nBaseUrl) {
    throw new Error('N8N_WEBHOOK_BASE_URL not configured');
  }

  // Fetch Instagram session cookie if available
  let sessionCookie: string | null = null;
  try {
    const cookieSetting = await prisma.setting.findUnique({
      where: { key: 'instagram_session_cookie' },
    });
    sessionCookie = cookieSetting?.value || null;
  } catch {
    // Ignore - cookie is optional
  }

  const webhookUrl = `${n8nBaseUrl}/instagram-orchestrator`;

  const response = await fetch(webhookUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      action: params.action,
      profile_id: params.profile_id,
      username: params.username,
      workspace_id: params.workspace_id,
      save_profile: params.save_profile ?? true,
      session_cookie: sessionCookie,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`n8n webhook failed: ${errorText}`);
  }

  const result = await response.json();

  return {
    success: true,
    job_id: result.scrape_run_id || result.job_id,
    message: 'Scraping started successfully',
    details: {
      action: params.action,
      profile_id: params.profile_id || result.profile_id,
      username: params.username,
    },
  };
}

export async function getScrapeStatus(scrapeRunId: string): Promise<ScrapeRun | null> {
  const scrapeRun = await prisma.scrapeRun.findUnique({
    where: { id: scrapeRunId },
  });
  return scrapeRun ? toScrapeRun(scrapeRun) : null;
}
