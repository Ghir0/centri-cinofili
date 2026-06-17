"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";

export function SortSelector({ currentSort }: { currentSort: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("sort", e.target.value);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  return (
    <div className="flex items-center gap-2 text-xs text-[color:var(--ds-gray-500)]">
      <label htmlFor="sort" className="font-mono uppercase tracking-wider">
        Ordina
      </label>
      <select
        id="sort"
        defaultValue={currentSort}
        onChange={handleChange}
        className="text-xs border-0 bg-transparent font-medium text-[color:var(--ds-gray-900)] focus:outline-none cursor-pointer"
      >
        <option value="name">A → Z</option>
        <option value="recent">Più recenti</option>
        <option value="rating">Migliori votati</option>
      </select>
    </div>
  );
}