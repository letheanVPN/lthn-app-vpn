import {createApp} from 'https://deno.land/x/servest@v1.3.1/mod.ts';
import {cors} from 'https://deno.land/x/servest@v1.3.1/middleware/cors.ts';
import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import * as path from 'https://deno.land/std/path/mod.ts';
import os from 'https://deno.land/x/dos@v0.11.0/mod.ts';
import {LetheanCli} from '../lethean-cli.ts';
import {Filter} from '../tools/toHTML.ts';

export class RestService {

	static app = createApp();

	static pathPerms: any = {
		backend: false,
		filesystem: true,
		daemon: true,
		update: true,
		help: false,
		completions: false
	};

	static discoverRoute(base: string, routes: any) {
		for (let dat of routes) {
			let key = dat[0], value = dat[1];
			if (RestService.pathPerms[key] === undefined || RestService.pathPerms[key] !== false) {
				console.log(`Adding route: ${[base, key].join('/')}`);
				this.addRoute([base, key].join('/'), value);
				if (value.commands) {
					this.discoverRoute([base, key].join('/'), value.commands);
				}
			}
		}
	}

	static addRoute(path: string, handle: any) {
		this.app.get(path, async (req) => {
			await req.respond({
				status: 200,
				headers: new Headers({
					'content-type': 'text/html',
					'Access-Control-Allow-Origin': '*'
				}),
				body: RestService.templateOutput(handle.getHelp())
			});
		});

		this.app.post(path, async (req) => {

			let cmdArgs: any = req.url.replace('/', '').split('/');

			let payload = await req.json();
			for (let key in payload) {
				console.log(payload[key]);
				//@ts-ignore
				let value = payload[key].length > 1 ? `=${payload[key]}` : '';
				cmdArgs.push('--' + key.replace(/([A-Z])/g, (x: any) => '-' + x.toLowerCase()) + value);
			}
			try {

				await LetheanCli.run(cmdArgs);

			} catch (error) {
				return await req.respond({
					status: 200,
					headers: new Headers({
						'content-type': 'text/plain',
						'Access-Control-Allow-Origin': '*'
					}),
					body: error.message
				});
			}

		});
	}

	public static run(args: any) {

		Deno.env.set('REST', '1');

		this.discoverRoute('', LetheanCli.options.commands);


		this.app.handle('/', async (req) => {
			await req.respond({
				status: 200,
				headers: new Headers({
					'content-type': 'text/html',
					'Access-Control-Allow-Origin': 'https://localhost'
				}),
				body: RestService.templateOutput(LetheanCli.options.getHelp())
			});
		});

		this.app.use(cors({
			origin: '*'
		}));

		this.app.listenTls({
			'hostname': 'localhost',
			'port': 36911,
			'certFile': `${path.join(args.homeDir, 'conf', 'public.pem')}`,
			'keyFile': `${path.join(args.homeDir, 'conf', 'private.pem')}`
		});
	}

	static templateOutput(input: string) {
		return new Filter().toHtml(`<html><head></head><body  style="background: radial-gradient(circle,#08f2b5 0%,#158297 100%); "><pre style=" margin-left: 2vw; width: 96vw; background: rgb(33, 33, 33);">${input}</pre></body></html>`);
	}

	public static config() {
		let home = os.homeDir();
		return new Command()
			.description('Backend Services for Application GUI')
			.command('start', 'Start Application Helper Daemon')
			.option('-h, --home-dir <string>', 'Home directory.', {default: path.join(home ? home : '/', 'Lethean')})
			.action((args) => RestService.run(args));

	}

}
