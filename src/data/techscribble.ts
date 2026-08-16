import { type CollectionEntry, getCollection } from "astro:content";

/** Fetch all tech scribbles. Drafts are excluded in production builds. */
export async function getAllTechScribbles(): Promise<CollectionEntry<"techscribble">[]> {
	return await getCollection("techscribble", ({ data }) => {
		return import.meta.env.PROD ? !data.draft : true;
	});
}

/** Sort tech scribbles alphabetically A-Z by title. Mutates copy. */
export function sortTechScribblesByTitle(
	scribbles: CollectionEntry<"techscribble">[],
): CollectionEntry<"techscribble">[] {
	return [...scribbles].sort((a, b) => {
		const titleA = a.data.title.replace(/^[^a-zA-Z0-9]+/, "").toLowerCase();
		const titleB = b.data.title.replace(/^[^a-zA-Z0-9]+/, "").toLowerCase();
		return titleA.localeCompare(titleB);
	});
}

/** Sort tech scribbles by date, newest first. */
export function sortTechScribblesByDate(
	scribbles: CollectionEntry<"techscribble">[],
): CollectionEntry<"techscribble">[] {
	return [...scribbles].sort((a, b) => {
		const dateA = (a.data.updatedDate ?? a.data.publishDate ?? new Date(0)).valueOf();
		const dateB = (b.data.updatedDate ?? b.data.publishDate ?? new Date(0)).valueOf();
		return dateB - dateA;
	});
}

/** Every tag across the given tech scribbles, including duplicates. */
export function getAllTechScribbleTags(scribbles: CollectionEntry<"techscribble">[]): string[] {
	return scribbles.flatMap((scribble) => scribble.data.tags);
}

/** Unique tags across the given tech scribbles, sorted alphabetically. */
export function getUniqueTechScribbleTags(scribbles: CollectionEntry<"techscribble">[]): string[] {
	return [...new Set(getAllTechScribbleTags(scribbles))].sort((a, b) => a.localeCompare(b));
}

/** Unique tags with counts across tech scribbles. */
export function getUniqueTechScribbleTagsWithCount(
	scribbles: CollectionEntry<"techscribble">[],
): [string, number][] {
	const counts = getAllTechScribbleTags(scribbles).reduce((map, tag) => {
		map.set(tag, (map.get(tag) ?? 0) + 1);
		return map;
	}, new Map<string, number>());
	return [...counts.entries()].sort(([aTag, aCount], [bTag, bCount]) =>
		bCount === aCount ? aTag.localeCompare(bTag) : bCount - aCount,
	);
}

/** Tech scribbles carrying the given tag. */
export function getTechScribblesByTag(
	scribbles: CollectionEntry<"techscribble">[],
	tag: string,
): CollectionEntry<"techscribble">[] {
	return scribbles.filter((scribble) => scribble.data.tags.includes(tag.toLowerCase()));
}

export interface LetterGroup {
	letter: string;
	scribbles: CollectionEntry<"techscribble">[];
}

/** Group tech scribbles alphabetically by the first character of their clean title. */
export function groupTechScribblesByLetter(
	scribbles: CollectionEntry<"techscribble">[],
): LetterGroup[] {
	const sorted = sortTechScribblesByTitle(scribbles);
	const groups = new Map<string, CollectionEntry<"techscribble">[]>();

	for (const scribble of sorted) {
		const firstChar = scribble.data.title.trim().charAt(0).toUpperCase();
		const letter = /^[A-Z]$/.test(firstChar) ? firstChar : "#";
		if (!groups.has(letter)) {
			groups.set(letter, []);
		}
		groups.get(letter)!.push(scribble);
	}

	// Sort letters A-Z, putting # at the end if present
	const sortedKeys = [...groups.keys()].sort((a, b) => {
		if (a === "#") return 1;
		if (b === "#") return -1;
		return a.localeCompare(b);
	});

	return sortedKeys.map((letter) => ({
		letter,
		scribbles: groups.get(letter)!,
	}));
}
