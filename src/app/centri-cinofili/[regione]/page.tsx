import Link from "next/link";
import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { createStaticClient } from "@/lib/supabase/static";
import { Provincia, Regione } from "@/types/centro";

export const dynamicParams = false;

export async function generateStaticParams() {
  const supabase = createStaticClient();
  const { data: regioni } = await supabase.from("regioni").select("slug");
  if (!regioni) return [];
  return regioni.map((r: { slug: string }) => ({ regione: r.slug }));
}

interface RegionePageProps {
  params: Promise<{ regione: string }>;
}

export default async function RegionePage({ params }: RegionePageProps) {
  const { regione: regioneSlug } = await params;
  const supabase = await createClient();

  // Fetch region
  const { data: regioneData } = await supabase
    .from("regioni")
    .select("*")
    .eq("slug", regioneSlug)
    .single();

  if (!regioneData) notFound();

  const regione: Regione = {
    id: regioneData.id,
    nome: regioneData.nome,
    slug: regioneData.slug,
  };

  // Fetch provinces + centri count
  const { data: provinceData } = await supabase
    .from("province")
    .select("*")
    .eq("regione_id", regione.id)
    .order("nome");

  const province: Provincia[] = (provinceData || []).map((p) => ({
    id: p.id,
    nome: p.nome,
    slug: p.slug,
    sigla: p.sigla,
    regione_id: p.regione_id,
  }));

  const { count: centriCount } = await supabase
    .from("centri")
    .select("id", { count: "exact", head: true })
    .eq("provincia.regione_id", regione.id);

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: `Centri Cinofili in ${regione.nome}`,
    description: `Elenco di centri cinofili in ${regione.nome} organizzati per provincia.`,
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Hero */}
      <section className="border-b border-[color:var(--ds-gray-100)] bg-white">
        <div className="mx-auto max-w-7xl px-6 pt-14 pb-12">
          <nav aria-label="Breadcrumb" className="mb-6 text-sm">
            <ol className="flex flex-wrap items-center gap-1.5 text-[color:var(--ds-gray-500)]">
              <li>
                <Link href="/" className="hover:text-[color:var(--ds-gray-900)]">
                  Home
                </Link>
              </li>
              <li aria-hidden>›</li>
              <li className="text-[color:var(--ds-gray-900)] font-medium">
                {regione.nome}
              </li>
            </ol>
          </nav>

          <div className="flex items-center gap-2 mb-5">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-[color:var(--ds-verified)]" />
            <span className="text-eyebrow">
              Regione · {province.length} province
            </span>
          </div>

          <h1 className="text-display max-w-3xl">
            Centri cinofili in {regione.nome}.
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-relaxed text-[color:var(--ds-gray-600)]">
            Esplora i centri cinofili registrati in {regione.nome}, organizzati
            per provincia. Ogni scheda include metodo educativo, discipline
            praticate, infrastrutture e contatti.
          </p>

          <div className="mt-7 flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-5 text-xs font-mono text-[color:var(--ds-gray-500)]">
              <div>
                <span className="text-[color:var(--ds-gray-900)] font-semibold text-base">
                  {centriCount ?? 0}
                </span>{" "}
                centri
              </div>
              <div className="h-3 w-px bg-[color:var(--ds-gray-200)]" />
              <div>
                <span className="text-[color:var(--ds-gray-900)] font-semibold text-base">
                  {province.length}
                </span>{" "}
                province
              </div>
            </div>
            <Link
              href={`/?regione=${regione.slug}`}
              className="btn-primary"
            >
              <span aria-hidden>⌘</span>
              Filtra recordset
            </Link>
          </div>
        </div>
      </section>

      {/* Province grid */}
      <section className="mx-auto max-w-7xl px-6 py-10">
        <div className="text-eyebrow mb-5">Scegli una provincia</div>
        {province.length === 0 ? (
          <div className="card-flat p-12 text-center">
            <p className="text-sm text-[color:var(--ds-gray-500)]">
              Nessuna provincia trovata per questa regione.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {province.map((prov) => (
              <Link
                key={prov.id}
                href={`/centri-cinofili/${regione.slug}/${prov.slug}/`}
                className="card-flat p-4 flex items-center justify-between hover:bg-[color:var(--ds-gray-50)] transition-colors group"
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium text-[color:var(--ds-gray-900)] truncate">
                    {prov.nome}
                  </div>
                  <div className="text-xs text-[color:var(--ds-gray-500)] font-mono mt-0.5">
                    {prov.sigla}
                  </div>
                </div>
                <span
                  aria-hidden
                  className="text-[color:var(--ds-gray-400)] group-hover:text-[color:var(--ds-gray-900)] transition-colors"
                >
                  →
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </>
  );
}