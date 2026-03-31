// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
	integrations: [
		starlight({
			title: 'Glicko Arena',
			description: 'Glicko-2 powered arena evaluation for LLM agents and pipelines.',
			logo: {
				light: './src/assets/logo-light.svg',
				dark: './src/assets/logo-dark.svg',
				replacesTitle: false,
			},
			social: [
				{
					icon: 'github',
					label: 'GitHub',
					href: 'https://github.com/whanyu1212/glicko-arena',
				},
			],
			editLink: {
				baseUrl: 'https://github.com/whanyu1212/glicko-arena/edit/main/docs/',
			},
			customCss: ['./src/styles/custom.css'],
			sidebar: [
				{
					label: 'Overview',
					items: [
						{ label: 'Introduction', slug: 'overview/introduction' },
						{ label: 'Architecture', slug: 'overview/architecture' },
						{ label: 'Packages', slug: 'overview/packages' },
					],
				},
				{
					label: 'glicko2',
					items: [
						{ label: 'Getting Started', slug: 'glicko2/getting-started' },
						{ label: 'Core Concepts', slug: 'glicko2/core-concepts' },
						{ label: 'Algorithm', slug: 'glicko2/algorithm' },
						{ label: 'Tournament Formats', slug: 'glicko2/tournament-formats' },
						{ label: 'Storage Backends', slug: 'glicko2/storage' },
					],
				},
				{
					label: 'glicko_eval',
					badge: { text: 'Coming Soon', variant: 'caution' },
					items: [
						{ label: 'Overview', slug: 'glicko-eval/overview' },
					],
				},
				{
					label: 'Contributing',
					items: [
						{ label: 'Dev Workflow', slug: 'contributing/dev-workflow' },
						{ label: 'Testing', slug: 'contributing/testing' },
						{ label: 'Releasing', slug: 'contributing/releasing' },
					],
				},
			],
		}),
	],
});
