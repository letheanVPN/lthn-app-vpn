import { createApp } from "https://deno.land/x/servest@v1.3.1/mod.ts";
import { Command } from "https://deno.land/x/cliffy/command/mod.ts";
import * as path from 'https://deno.land/std/path/mod.ts';
import {LetheanCli} from '../../lethean-cli.ts';
import {Filter} from '../../tools/toHTML.ts';

export class LetheanBackend {

	static app = createApp();

	static pathPerms:any = {
		backend: false,
		filesystem: true,
		daemon: true,
		update: true,
		help: false,
		completions: false
	}

	static discoverRoute(base: string, routes: any){
		for (let dat of routes) {
			let key = dat[0],value = dat[1];
			if(LetheanBackend.pathPerms[key] === undefined || LetheanBackend.pathPerms[key] !== false){
				console.log(`Adding route: ${[base, key].join('/')}`)
				this.addRoute( [base, key].join('/'), value);
				if(value.commands){
					this.discoverRoute([base, key].join('/'), value.commands)
				}
			}
		}
	}

	static addRoute(path: string, handle: any){
		this.app.get(path, async (req) => {
			await req.respond({
				status: 200,
				headers: new Headers({
					"content-type": "text/html",
				}),
				body: LetheanBackend.templateOutput(handle.getHelp()),
			});
		});

		this.app.post(path, async (req) => {

			let cmdArgs:any = req.url.replace('/','').split('/')
			for (let dat of await req.formData()) {

				//@ts-ignore
				let value = dat[1].length > 1 ? `=${dat[1]}` : ''
				cmdArgs.push('--' + dat[0].replace(/([A-Z])/g, (x) => '-'+x.toLowerCase())+ value)
			}
			try {
				await LetheanCli.run(cmdArgs)
			} catch (error) {
				await req.respond({
					status: 200,
					headers: new Headers({
						"content-type": "text/html",
					}),
					body: error.message,
				});
			}

			})
	}

	public static run(args: any){

		this.discoverRoute('',LetheanCli.options.commands);

		this.app.handle("/", async (req) => {
			await req.respond({
				status: 200,
				headers: new Headers({
					"content-type": "text/html",
				}),
				body: LetheanBackend.templateOutput(LetheanCli.options.getHelp()),
			});
		});

		this.app.listenTls({
			"hostname": "localhost",
			"port": 36911,
			"certFile" :`${path.join(args.homeDir, 'conf', 'public.pem')}`,
			"keyFile": `${path.join(args.homeDir, 'conf', 'private.pem')}`
			});
	}

	static templateOutput(input: string){
		return new Filter().toHtml(`<html><head></head><body  style="background: radial-gradient(circle,#08f2b5 0%,#158297 100%); "><pre style=" margin-left: 2vw; width: 96vw; background: rgb(33, 33, 33);">${input}</pre></body></html>`);
	}
	public static config(){
		return new Command()
			.description("Backend Services for Application GUI")
			.command('start', 'Start Application Helper Daemon')
			.option("-h, --home-dir <string>", "Home directory.")
			.action((args) => LetheanBackend.run(args))

	}

}
