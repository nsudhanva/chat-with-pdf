import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: {
			'/api': process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'
		}
	}
});
