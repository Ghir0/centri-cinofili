import { createClient } from '@supabase/supabase-js';

/**
 * Static Supabase client for use in generateStaticParams and other
 * build-time contexts where cookies() / next/headers are NOT available.
 * Uses the service_role or anon key directly without cookie auth.
 */
export function createStaticClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      auth: {
        persistSession: false,
        autoRefreshToken: false,
      },
    }
  );
}
