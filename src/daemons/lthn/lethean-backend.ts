import { createApp } from "https://deno.land/x/servest@v1.3.1/mod.ts";
import { Command } from "https://deno.land/x/cliffy/command/mod.ts";
import type { WebSocket } from "https://deno.land/std/ws/mod.ts";
import {LetheanDaemonLetheand} from './letheand.ts';
import {LetheanDaemonLetheanWalletRpc} from './lethean-wallet-rpc.ts';

export class LetheanBackend {
	static options: any
	constructor() {

	}

	public static run(){
		const app = createApp();
		let daemons: any = {}

		function handleHandshake(sock: WebSocket) {
			async function handleMessage(sock: WebSocket) {
				for await (const msg of sock) {
					if (typeof msg === "string") {
						sock.send(msg);
					}
				}
			}

			handleMessage(sock);
		}

		app.ws("/ws", handleHandshake);
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

		app.listen({port: 36911});
	}

	public static config(){
		return new Command()
			.description("Backend Services for Application GUI")
			.command('start', 'Start Application Helper Daemon')
			.option("-h, --home-dir", "Home directory.")
			.option("-d, --data-dir", "Directory to store data.")
			.option("-c, --config-file", "Daemon config(dep)")
			.option("-b, --bin-dir", "Binaries location")
			.action(() => LetheanBackend.run())

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
