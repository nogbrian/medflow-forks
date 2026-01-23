import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { Prisma } from '@prisma/client';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const profileId = searchParams.get('profile_id');
    const dateFrom = searchParams.get('date_from');
    const dateTo = searchParams.get('date_to');
    const orderBy = searchParams.get('order_by') || 'engagement';
    const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 200);
    const type = searchParams.get('type') || 'all';

    if (!profileId) {
      return NextResponse.json(
        { success: false, error: 'profile_id is required' },
        { status: 400 }
      );
    }

    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(profileId)) {
      return NextResponse.json(
        { success: false, error: 'Invalid profile_id format' },
        { status: 400 }
      );
    }

    const validOrderBy = ['likes', 'comments', 'engagement', 'date'];
    if (!validOrderBy.includes(orderBy)) {
      return NextResponse.json(
        { success: false, error: 'Invalid order_by' },
        { status: 400 }
      );
    }

    const validTypes = ['all', 'posts', 'reels'];
    if (!validTypes.includes(type)) {
      return NextResponse.json(
        { success: false, error: 'Invalid type' },
        { status: 400 }
      );
    }

    const profile = await prisma.profile.findUnique({
      where: { id: profileId },
    });

    if (!profile) {
      return NextResponse.json(
        { success: false, error: 'Profile not found' },
        { status: 404 }
      );
    }

    const dateFilter: Prisma.PostWhereInput = {};
    if (dateFrom) {
      dateFilter.postedAt = { ...dateFilter.postedAt as object, gte: new Date(dateFrom) };
    }
    if (dateTo) {
      dateFilter.postedAt = { ...dateFilter.postedAt as object, lte: new Date(dateTo) };
    }

    const typeFilter: Prisma.PostWhereInput = {};
    if (type === 'posts') {
      typeFilter.isReel = false;
    } else if (type === 'reels') {
      typeFilter.isReel = true;
    }

    const stats = await prisma.post.aggregate({
      where: {
        profileId,
        ...dateFilter,
      },
      _count: true,
      _avg: {
        likesCount: true,
        commentsCount: true,
      },
      _max: {
        likesCount: true,
      },
    });

    const reelsCount = await prisma.post.count({
      where: {
        profileId,
        isReel: true,
        ...dateFilter,
      },
    });

    const postsCount = await prisma.post.count({
      where: {
        profileId,
        isReel: false,
        ...dateFilter,
      },
    });

    const avgEngagementRate =
      profile.followersCount > 0
        ? ((stats._avg.likesCount || 0) + (stats._avg.commentsCount || 0)) /
          profile.followersCount *
          100
        : 0;

    const maxEngagementPost = await prisma.post.findFirst({
      where: {
        profileId,
        ...dateFilter,
      },
      orderBy: [
        { likesCount: 'desc' },
        { commentsCount: 'desc' },
      ],
    });

    const maxEngagementRate =
      profile.followersCount > 0 && maxEngagementPost
        ? ((maxEngagementPost.likesCount + maxEngagementPost.commentsCount) /
            profile.followersCount) *
          100
        : 0;

    const orderByClause: Prisma.PostOrderByWithRelationInput =
      orderBy === 'likes'
        ? { likesCount: 'desc' }
        : orderBy === 'comments'
          ? { commentsCount: 'desc' }
          : orderBy === 'date'
            ? { postedAt: 'desc' }
            : { likesCount: 'desc' };

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
        type: post.type,
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

    if (orderBy === 'engagement') {
      postsWithEngagement.sort((a, b) => b.engagement_rate - a.engagement_rate);
    }

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
        ${dateFrom ? Prisma.sql`AND p.posted_at >= ${new Date(dateFrom)}` : Prisma.empty}
        ${dateTo ? Prisma.sql`AND p.posted_at <= ${new Date(dateTo)}` : Prisma.empty}
      GROUP BY h.tag, pr.followers_count
      ORDER BY usage_count DESC
      LIMIT 20
    `;

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
        ${dateFrom ? Prisma.sql`AND p.posted_at >= ${new Date(dateFrom)}` : Prisma.empty}
        ${dateTo ? Prisma.sql`AND p.posted_at <= ${new Date(dateTo)}` : Prisma.empty}
      GROUP BY m.username, pr.followers_count
      ORDER BY usage_count DESC
      LIMIT 20
    `;

    const response = {
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
        avg_likes: stats._avg.likesCount || 0,
        avg_comments: stats._avg.commentsCount || 0,
        avg_engagement_rate: avgEngagementRate,
        max_likes: stats._max.likesCount || 0,
        max_engagement_rate: maxEngagementRate,
        period: { from: dateFrom, to: dateTo },
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
        filters: { order_by: orderBy, limit, type, date_from: dateFrom, date_to: dateTo },
        posts_returned: postsWithEngagement.length,
      },
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Error in analytics:', error);
    return NextResponse.json(
      { success: false, error: (error as Error).message },
      { status: 500 }
    );
  }
}
