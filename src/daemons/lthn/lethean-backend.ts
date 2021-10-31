import { createApp } from "https://deno.land/x/servest@v1.3.1/mod.ts";
import { Command } from "https://deno.land/x/cliffy/command/mod.ts";
import {LetheanDaemonLetheand} from './letheand.ts';
import {LetheanDaemonLetheanWalletRpc} from './lethean-wallet-rpc.ts';
import {LetheanAccount} from '../../accounts/user.ts';
import * as path from 'https://deno.land/std/path/mod.ts';

export class LetheanBackend {
	static options: any
	constructor() {

	}

	public static run(args: any){
		const app = createApp();
		let daemons: any = {}

		console.log(args)
		app.handle("/", async (req) => {
			await req.respond({
				status: 200,
				headers: new Headers({
					"content-type": "text/plain",
				}),
				body: "Hello, I'm the Lethean Desktop API, there is not much exciting here, but it's good to see you taking a look!",
			});
		});

		app.handle("/daemon/start/letheand", async (req) => {
			daemons = {
				...daemons, letheand: new LetheanDaemonLetheand()
			};
			daemons.letheand.run()
			console.log(daemons)
			await req.respond({
				status: 200,
				headers: new Headers({
					"content-type": "text/plain",
				}),
				body: "Started",
			});
		});

		app.handle("/daemon/start/lethean-wallet-rpc", async (req) => {
			daemons = {
				...daemons, letheanWalletRpc: new LetheanDaemonLetheanWalletRpc(Deno.args)
			};
			daemons.letheanWalletRpc.run()
			console.log(daemons)
			await req.respond({
				status: 200,
				headers: new Headers({
					"content-type": "text/plain",
				}),
				body: "Started",
			});
		});

		app.handle('/account/create', async (req) => {
			let username = 'snider';
			let password = 'password';
			let result = await LetheanAccount.create({username: username, password: password})
			await req.respond({
				status: 200,
				headers: new Headers({
					"content-type": "text/plain",
				}),
				body: 'good',
			});
		})

		app.listenTls({
			"hostname": "localhost",
			"port": 36911,
			"certFile" :`${path.join(args.homeDir, 'conf', 'public.pem')}`,
			"keyFile": `${path.join(args.homeDir, 'conf', 'private.pem')}`
			});
	}

	public static config(){
		return new Command()
			.description("Backend Services for Application GUI")
			.command('start', 'Start Application Helper Daemon')
			.option("-h, --home-dir <string>", "Home directory.")
			.option("-d, --data-dir <string>", "Directory to store data.")
			.option("-c, --config-file <string>", "Daemon config(dep)")
			.option("-b, --bin-dir <string>", "Binaries location")
			.action((args) => LetheanBackend.run(args))

	}
	static async init() {
			LetheanBackend.options = await new Command()
				.name("Lethean CLI")
				.version("0.1.0")
				.description("Command line interface for Lethean")
				.option("-h, --home-dir", "Home directory.")
				.option("-d, --data-dir", "Directory to store data.")
				.option("-c, --config-file", "Daemon config(dep)")
				.option("-b, --bin-dir", "Binaries location")
				.parse(Deno.args);
			new LetheanBackend()
		}

}
