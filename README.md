# Potemkin & Co

Personal site for [Alex @ Potemkin & Co](https://potemkin.co) — notes, projects, and whatever is on the desk.

Built with [Astro Sienna](https://github.com/anjay-goel/astro-sienna).

## Local development

```sh
pnpm install
pnpm dev
```

Open http://localhost:4321.

| Command        | What it does                                 |
|----------------|----------------------------------------------|
| `pnpm dev`     | Start the dev server with HMR                |
| `pnpm build`   | Type-check, build, and run Pagefind indexing |
| `pnpm preview` | Preview the production build locally         |

## Deploy

The site deploys to GitHub Pages from [PotemkinCo/www](https://github.com/PotemkinCo/www), with custom domain [potemkin.co](https://potemkin.co). Push to `main` triggers the workflow in `.github/workflows/deploy.yml`.

## License

[MIT](./LICENSE).
