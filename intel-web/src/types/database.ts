// API Response Types (snake_case for JSON compatibility)

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  color: string;
  created_at: string;
  updated_at: string;
}

export interface Profile {
  id: string;
  workspace_id: string;
  instagram_id: string | null;
  username: string;
  full_name: string | null;
  biography: string | null;
  external_url: string | null;
  followers_count: number;
  follows_count: number;
  posts_count: number;
  is_verified: boolean;
  is_business_account: boolean;
  business_category: string | null;
  profile_pic_url: string | null;
  is_active: boolean;
  last_scraped_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Post {
  id: string;
  profile_id: string;
  instagram_id: string;
  short_code: string | null;
  type: 'Image' | 'Video' | 'Sidecar';
  url: string | null;
  display_url: string | null;
  caption: string | null;
  likes_count: number;
  comments_count: number;
  video_view_count: number | null;
  video_play_count: number | null;
  video_duration: number | null;
  is_reel: boolean;
  is_pinned: boolean;
  is_sponsored: boolean;
  is_comments_disabled: boolean;
  location_name: string | null;
  location_id: string | null;
  alt_text: string | null;
  posted_at: string | null;
  scraped_at: string;
  created_at: string;
  updated_at: string;
}

export interface PostWithEngagement extends Post {
  profile_username: string;
  profile_full_name: string | null;
  profile_followers: number;
  profile_is_verified: boolean;
  engagement_absolute: number;
  engagement_rate: number;
}

export interface ProfileSummary extends Profile {
  workspace_name: string;
  workspace_color: string;
  total_posts: number;
  total_reels: number;
  avg_engagement_rate: number;
  last_post_date: string | null;
}

export interface ProfileStats {
  total_posts: number;
  total_reels: number;
  avg_likes: number;
  avg_comments: number;
  avg_engagement_rate: number;
  min_likes: number;
  max_likes: number;
  std_dev_likes: number;
  min_comments: number;
  max_comments: number;
  std_dev_comments: number;
  min_engagement_rate: number;
  max_engagement_rate: number;
  std_dev_engagement_rate: number;
  period: { from: string | null; to: string | null };
}

export interface HashtagAnalytics {
  tag: string;
  usage_count: number;
  avg_likes: number;
  avg_engagement_rate: number;
}

export interface MentionAnalytics {
  username: string;
  usage_count: number;
  avg_likes: number;
  avg_engagement_rate: number;
}

export interface ScrapeRun {
  id: string;
  profile_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  scrape_type: string;
  posts_scraped: number;
  reels_scraped: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export type OrderBy = 'likes' | 'comments' | 'engagement' | 'date' | 'views';
export type SortDirection = 'asc' | 'desc';
export type PostType = 'all' | 'posts' | 'reels';
export type DatePreset = 'all' | 'week' | 'month' | '3months' | 'custom';

export interface PostFilters {
  order_by: OrderBy;
  sort_direction: SortDirection;
  type: PostType;
  date_preset: DatePreset;
  date_from?: string;
  date_to?: string;
  limit: number;
}

export const DEFAULT_FILTERS: PostFilters = {
  order_by: 'engagement',
  sort_direction: 'desc',
  type: 'all',
  date_preset: 'all',
  limit: 500,
};

export interface AnalyticsMeta {
  filters: {
    order_by: string;
    limit: number;
    type: string;
    date_from: string | null;
    date_to: string | null;
  };
  posts_returned: number;
}

export interface AnalyticsResponse {
  success: boolean;
  profile: Profile;
  stats: ProfileStats;
  top_hashtags: HashtagAnalytics[];
  top_mentions: MentionAnalytics[];
  posts: PostWithEngagement[];
  meta?: AnalyticsMeta;
}

export interface TriggerScrapeResponse {
  success: boolean;
  job_id?: string;
  message: string;
  details?: {
    action?: string;
    profile_id?: string;
    username?: string;
  };
}
