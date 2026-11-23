# Centri Cinofili Italia

> Registro nazionale aperto e indipendente dei centri educativi cinofili in Italia.  
> Online su: **[https://www.centri-cinofili.it](https://www.centri-cinofili.it)**

---

## Il Progetto

Trovare informazioni chiare su come lavorano realmente i centri cinofili sul territorio italiano è spesso complicato: siti web datati, pagine social non aggiornate o descrizioni generiche rendono difficile per i proprietari di cani orientarsi e confrontare le strutture.

**Centri Cinofili Italia** nasce come anagrafe aperta e gratuita con l'obiettivo di fare trasparenza nel settore, permettendo di filtrare e consultare i centri non solo per posizione geografica o disciplina, ma soprattutto per **metodologia educativa dichiarata** (cognitivo-relazionale, gentile, tradizionale/utilitaristico, etologico, misto).

Ogni scheda include:
- Metodo educativo adottato e descrizione dell'approccio
- Attività e discipline praticate (puppy class, agility, obedience, recupero comportamentale, ecc.)
- Strutture del campo (indoor, recinzione, illuminazione, aree socializzazione)
- Contatti diretti (telefono, email, sito web, canali social)
- Posizione geolocalizzata su mappa interattiva (OpenStreetMap / Leaflet)
- Badge di stato (**Verificato** / **Non verificato**) per distinguere i dati importati da registri pubblici rispetto a quelli confermati o aggiornati direttamente dai responsabili del centro.

---

## Stack Tecnologico

- **Framework**: [Next.js](https://nextjs.org) (App Router, Server Components, TypeScript)
- **Styling**: Tailwind CSS v4
- **Database**: [Supabase](https://supabase.com) (PostgreSQL + estensione PostGIS per geolocalizzazione e query spaziali)
- **Mappe**: Leaflet / React-Leaflet su cartografia OpenStreetMap
- **SEO & Dati strutturati**: Schema.org (`DogTrainer`), OpenGraph, Sitemap dinamica e percorsi pre-renderizzati

---

## Avvio in Locale

### Prerequisiti
- Node.js 20+
- Un'istanza o progetto Supabase con PostGIS abilitato

### 1. Clonare il repository
```bash
git clone https://github.com/Ghir0/centri-cinofili.git
cd centri-cinofili
npm install
```

### 2. Configurare le variabili d'ambiente
Creare un file `.env.local` nella root del progetto:
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 3. Avviare il server di sviluppo
```bash
npm run dev
```

L'applicazione sarà accessibile all'indirizzo [http://localhost:3000](http://localhost:3000).

---

## Contribuire, Segnalazioni e Rivendicazioni

Il portale è aperto e a disposizione della community cinofila.
- Per richiedere la **rivendicazione gratuita** di una scheda esistente (assegnazione del badge *Verificato*)
- Per segnalare **nuovi centri** non ancora censiti
- Per correzioni di dati o rimozione di attività cessate

È possibile utilizzare l'apposito pulsante presente sul portale ([centri-cinofili.it](https://www.centri-cinofili.it)) oppure aprire una segnalazione/pull request su questo repository.

---

## Licenza

I dati e il codice sorgente sono rilasciati con finalità aperte per la consultazione pubblica.
