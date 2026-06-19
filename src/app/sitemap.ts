import { createStaticClient } from "@/lib/supabase/static";
import type { MetadataRoute } from "next";

const BASE_URL = "https://centri-cinofili.it";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const supabase = createStaticClient();

  const entries: MetadataRoute.Sitemap = [
    {
      url: BASE_URL,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 1.0,
    },
    {
      url: `${BASE_URL}/mappa`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.8,
    },
  ];

  // Fetch all regions
  const { data: regioni } = await supabase.from("regioni").select("slug");
  if (regioni) {
    for (const r of regioni) {
      entries.push({
        url: `${BASE_URL}/centri-cinofili/${r.slug}`,
        lastModified: new Date(),
        changeFrequency: "weekly",
        priority: 0.6,
      });
    }
  }

  // Fetch all province + their regions
  const { data: province } = await supabase
    .from("province")
    .select("slug, regione:regione_id(slug)");
  if (province) {
    for (const p of province) {
      const regSlug = (p.regione as any)?.slug || "italia";
      entries.push({
        url: `${BASE_URL}/centri-cinofili/${regSlug}/${p.slug}`,
        lastModified: new Date(),
        changeFrequency: "weekly",
        priority: 0.5,
      });
    }
  }

  // Fetch all centro slugs
  const { data: centri } = await supabase.from("centri").select("slug, updated_at");
  if (centri) {
    for (const c of centri) {
      entries.push({
        url: `${BASE_URL}/centro/${c.slug}`,
        lastModified: c.updated_at ? new Date(c.updated_at) : new Date(),
        changeFrequency: "monthly",
        priority: 0.7,
      });
    }
  }

  return entries;
}
