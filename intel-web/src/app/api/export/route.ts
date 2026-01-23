import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

function toCSV(data: Record<string, unknown>[], columns: string[]): string {
  const header = columns.join(',');
  const rows = data.map((item) =>
    columns
      .map((col) => {
        const value = item[col];
        if (value === null || value === undefined) return '';
        if (
          typeof value === 'string' &&
          (value.includes(',') || value.includes('"') || value.includes('\n'))
        ) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return String(value);
      })
      .join(',')
  );
  return [header, ...rows].join('\n');
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const profileId = searchParams.get('profile_id');
    const format = searchParams.get('format') || 'csv';
    const dateFrom = searchParams.get('date_from');
    const dateTo = searchParams.get('date_to');

    if (!profileId) {
      return NextResponse.json(
        { success: false, error: 'profile_id is required' },
        { status: 400 }
      );
    }

    const profile = await prisma.profile.findUnique({
      where: { id: profileId },
      select: { username: true, followersCount: true },
    });

    if (!profile) {
      return NextResponse.json(
        { success: false, error: 'Profile not found' },
        { status: 404 }
      );
    }

    const dateFilter: { postedAt?: { gte?: Date; lte?: Date } } = {};
    if (dateFrom) {
      dateFilter.postedAt = { ...dateFilter.postedAt, gte: new Date(dateFrom) };
    }
    if (dateTo) {
      dateFilter.postedAt = { ...dateFilter.postedAt, lte: new Date(dateTo) };
    }

    const posts = await prisma.post.findMany({
      where: {
        profileId,
        ...dateFilter,
      },
      orderBy: { likesCount: 'desc' },
    });

    const exportData = posts.map((post) => {
      const engagementAbsolute = post.likesCount + post.commentsCount;
      const engagementRate =
        profile.followersCount > 0
          ? (engagementAbsolute / profile.followersCount) * 100
          : 0;

      return {
        instagram_id: post.instagramId,
        short_code: post.shortCode,
        type: post.type,
        is_reel: post.isReel,
        caption: (post.caption || '').substring(0, 500),
        likes_count: post.likesCount,
        comments_count: post.commentsCount,
        engagement_absolute: engagementAbsolute,
        engagement_rate: engagementRate.toFixed(4),
        video_view_count: post.videoViewCount,
        posted_at: post.postedAt?.toISOString() || '',
        url: post.url || '',
      };
    });

    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `${profile.username}_posts_${timestamp}`;

    if (format === 'json') {
      return new NextResponse(
        JSON.stringify(
          {
            profile: profile.username,
            exported_at: new Date().toISOString(),
            total_posts: exportData.length,
            posts: exportData,
          },
          null,
          2
        ),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Content-Disposition': `attachment; filename="${filename}.json"`,
          },
        }
      );
    }

    const columns = [
      'instagram_id',
      'short_code',
      'type',
      'is_reel',
      'likes_count',
      'comments_count',
      'engagement_absolute',
      'engagement_rate',
      'video_view_count',
      'posted_at',
      'url',
      'caption',
    ];

    const csv = toCSV(exportData, columns);

    return new NextResponse(csv, {
      status: 200,
      headers: {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': `attachment; filename="${filename}.csv"`,
      },
    });
  } catch (error) {
    console.error('Error in export:', error);
    return NextResponse.json(
      { success: false, error: (error as Error).message },
      { status: 500 }
    );
  }
}
