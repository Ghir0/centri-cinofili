import Link from "next/link";

interface MetodologiaGuideItem {
  nome: string;
  slug: string;
  descrizione: string | null;
  principi: string[];
  adattoA: string;
  icona: string;
}

export function MethodologyGuide() {
  const metodi: MetodologiaGuideItem[] = [
    {
      nome: "Cognitivo-Relazionale",
      slug: "cognitivo-relazionale",
      descrizione:
        "L'approccio cognitivo-relazionale si basa sullo studio dei processi mentali del cane — percezione, memoria, apprendimento, emozioni — e sulla relazione come fondamento di ogni percorso educativo. Il cane non è un esecutore passivo di comandi: è un individuo pensante con cui costruire un dialogo.",
      principi: [
        "Il cane apprende per insight (comprensione), non per condizionamento meccanico",
        "La relazione uomo-cane è il prerequisito, non il risultato dell'addestramento",
        "Ogni comportamento ha una causa emotiva o cognitiva — si lavora sulla causa, non sul sintomo",
        "Rispetto dei tempi individuali: ogni cane ha il suo percorso",
      ],
      adattoA:
        "Proprietari che vogliono capire davvero il proprio cane, non solo addestrarlo. Ideale per cani con problematiche comportamentali complesse, cuccioli in fase di sviluppo cognitivo, e famiglie.",
      icona: "🧠",
    },
    {
      nome: "Gentile",
      slug: "gentile",
      descrizione:
        "Il metodo gentile — o 'force-free' — rifiuta qualsiasi strumento coercitivo (collari a strozzo, elettrici, strattoni) e si basa esclusivamente sul rinforzo positivo. Il cane collabora perché motivato, non perché intimorito. Il benessere emotivo è il parametro di riferimento costante.",
      principi: [
        "Rinforzo positivo: premiare il comportamento desiderato, ignorare o reindirizzare quello indesiderato",
        "Zero coercizione: nessun collare a strozzo, elettrico, punizione fisica o intimidazione",
        "Comunicazione chiara: segnali coerenti, timing preciso, sessioni brevi",
        "Rispetto della soglia di stress: il lavoro si ferma prima che il cane vada in difficoltà",
      ],
      adattoA:
        "La scelta più etica per qualsiasi cane — dai cuccioli ai cani adulti con traumi pregressi. Particolarmente indicato per cani sensibili o paurosi, dove i metodi tradizionali peggiorerebbero il problema.",
      icona: "💚",
    },
    {
      nome: "Tradizionale / Utilitaristico",
      slug: "tradizionale",
      descrizione:
        "L'approccio tradizionale discende dall'addestramento militare e da lavoro. Si basa su una gerarchia chiara uomo-cane, con comandi impartiti in modo direttivo. Il focus è sull'obbedienza immediata e sull'affidabilità del comando in ogni contesto.",
      principi: [
        "Comando → esecuzione: struttura gerarchica chiara",
        "Correzioni fisiche o strumentali per comportamenti indesiderati",
        "Sessioni strutturate con obiettivi misurabili",
        "Focus su obbedienza, disciplina e autocontrollo situazionale",
      ],
      adattoA:
        "Cani da lavoro, sport cinofili ad alta competizione, razze selezionate per compiti specifici (pastore, guardiania). Meno indicato per cani da compagnia o soggetti sensibili, dove il rischio di effetti collaterali emotivi è maggiore.",
      icona: "⚡",
    },
    {
      nome: "Non Specificato",
      slug: "non-specificato",
      descrizione:
        "Molti centri non dichiarano esplicitamente una metodologia. Questo può significare un approccio eclettico che attinge a più scuole, oppure la mancanza di una formazione metodologica strutturata nell'équipe. La trasparenza sul metodo è un indicatore di professionalità.",
      principi: [
        "Approccio non formalizzato o misto",
        "Può variare da istruttore a istruttore all'interno dello stesso centro",
        "Difficile per il proprietario sapere cosa aspettarsi",
      ],
      adattoA:
        "Proprietari che già conoscono il centro per passaparola. Consigliamo sempre di chiedere un colloquio conoscitivo e di osservare una sessione prima di iscriversi.",
      icona: "❓",
    },
  ];

  return (
    <section className="mx-auto max-w-7xl px-6 py-12">
      <div className="mb-12 max-w-3xl">
        <div className="flex items-center gap-2 mb-4">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-[color:var(--ds-verified)]" />
          <span className="text-eyebrow">Guida alla scelta</span>
        </div>
        <h2 className="text-h1 mb-4">
          Quale metodo educativo per il tuo cane?
        </h2>
        <p className="text-lg leading-relaxed text-[color:var(--ds-gray-600)]">
          Non tutte le scuole di pensiero sono uguali. La metodologia educativa è il
          fondamento di ogni percorso — definisce come il cane imparerà, che tipo di
          relazione costruirete e quale sarà il suo benessere emotivo durante
          l'addestramento. Ecco cosa distingue i quattro approcci principali.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {metodi.map((m) => (
          <article key={m.slug} className="card p-6 flex flex-col gap-4">
            <div className="flex items-start gap-4">
              <span aria-hidden className="text-3xl leading-none shrink-0 mt-0.5">
                {m.icona}
              </span>
              <div className="min-w-0">
                <h3 className="text-h2 mb-2">{m.nome}</h3>
                <p className="text-sm leading-relaxed text-[color:var(--ds-gray-600)]">
                  {m.descrizione}
                </p>
              </div>
            </div>

            <div>
              <div className="text-eyebrow mb-2">Principi chiave</div>
              <ul className="space-y-2">
                {m.principi.map((p, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-[color:var(--ds-gray-600)]">
                    <span className="mt-1 shrink-0 text-[color:var(--ds-verified)]">
                      <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden>
                        <path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z" />
                      </svg>
                    </span>
                    {p}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-auto rounded-md bg-[color:var(--ds-gray-50)] p-4">
              <div className="text-eyebrow mb-1 text-[color:var(--ds-gray-500)]">Adatto a</div>
              <p className="text-sm text-[color:var(--ds-gray-600)]">{m.adattoA}</p>
            </div>

            <Link href={`/?metodologia=${m.slug}`} className="btn-secondary w-full">
              Vedi centri con metodo {m.nome.split(" ")[0].toLowerCase()}
              <span aria-hidden className="text-[color:var(--ds-gray-500)]">→</span>
            </Link>
          </article>
        ))}
      </div>

      <div className="mt-10 card-flat p-6 text-center">
        <div className="text-eyebrow mb-2">Non sai da dove partire?</div>
        <p className="text-sm text-[color:var(--ds-gray-600)] max-w-xl mx-auto">
          Usa la barra di ricerca per digitare il tuo comune, oppure seleziona
          una regione e una metodologia. I filtri a sinistra ti permettono di
          incrociare metodo, discipline e infrastrutture per trovare il centro
          perfetto per te e il tuo cane.
        </p>
      </div>
    </section>
  );
}
