export interface ShowcaseItem {
	name: string;
	href: string;
	stack: string;
	badge?: string;
	desc: string;
}

export const showcase: ShowcaseItem[] = [
	{
		name: "landstrip",
		href: "https://github.com/alexander-potemkin/landstrip",
		stack: "TypeScript · Agents",
		badge: "OSS",
		desc: "A sandbox for coding agents with parametrized state.",
	},
	{
		name: "pi-automode",
		href: "https://github.com/alexander-potemkin/pi-automode",
		stack: "TypeScript · CLI",
		badge: "OSS",
		desc: "Think Claude Code's auto mode but for pi. Selectable model, sensible defaults.",
	},
	{
		name: "toolbelt",
		href: "https://github.com/PotemkinCo/toolbelt",
		stack: "Shell · Ops",
		badge: "OSS",
		desc: "Ubuntu and FreeBSD setup scripts and ops niceties.",
	},
	{
		name: "depenguin-run",
		href: "https://github.com/alexander-potemkin/depenguin-run",
		stack: "Shell · FreeBSD",
		badge: "OSS",
		desc: "Installer script for mfsBSD to put FreeBSD on ZFS-on-root via qemu.",
	},
];
