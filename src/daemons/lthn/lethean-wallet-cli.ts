import os from 'https://deno.land/x/dos@v0.11.0/mod.ts';
import {ensureDir} from 'https://deno.land/std@0.106.0/fs/mod.ts';
import {readLines} from 'https://deno.land/std@0.79.0/io/bufio.ts';
import EventEmitter from 'https://deno.land/std@0.79.0/node/events.ts';
import * as path from 'https://deno.land/std/path/mod.ts';
import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import {StringResponse} from '../../tools/string-response.ts';

export class stdOutStream extends EventEmitter {
	constructor() {
		super();
	}

	public async run(...command: Array<string>): Promise<void> {
		const p = Deno.run({
			cmd: command,
			stderr: 'piped',
			stdout: 'piped'
		});
		for await (const line of readLines(p.stdout)) {
			if (line.trim()) {
				super.emit('stdout', line);
			}
		}
		for await (const line of readLines(p.stderr)) {
			if (line.trim()) {
				super.emit('stderr', line);
			}
		}
		super.emit('end', await p.status());
		p.close();
		return;
	}
}


export class LetheanWalletCli {
	private static command: any;
	private static exeFile: string;
	private static debug: number = 1;
	private static process: stdOutStream;

	static run(args: any) {

		let homeDir = os.homeDir();


		this.exeFile = 'lethean-wallet-cli' + (os.platform() === 'windows' ? '.exe' : '');
		LetheanWalletCli.command = path.join(homeDir ? homeDir : './', 'Lethean', 'cli', this.exeFile);

		LetheanWalletCli.process = new stdOutStream();
		let cmdArgs: any = [];

		for (let arg in args) {
			if (arg !== 'igd') {
				let value = args[arg].length > 1 ? `=${args[arg]}` : '';
				cmdArgs.push('--' + arg.replace(/([A-Z])/g, (x) => '-' + x.toLowerCase()) + value);
			}

		}

		//return ensureDir(args['dataDir']).then(async () => {
		console.log(LetheanWalletCli.command, cmdArgs);
		return LetheanWalletCli.process.on('stdout', stdout => {
			console.log(stdout);
		}).on('stderr', stderr => {
			console.log(stderr);
		}).run(this.command, ...cmdArgs);


		//});
	}

	public static config() {

		let home = os.homeDir();

		return new Command()
			.description('Wallet CLI')
			.option('--daemon-address <string>', 'Use daemon instance at <host>:<port>')
			.option('--daemon-host <string>', 'Use daemon instance at host <arg> instead of localhost')
			.option('--password <string>', 'Wallet password (escape/quote as needed)')
			.option('--password-file <string>', 'Wallet password file')
			.option('--daemon-port <string>', 'Use daemon instance at port <arg> instead of 48782')
			.option('--daemon-login <string>', 'Specify username[:password] for daemon RPC client')
			.option('--testnet <boolean>', 'For testnet. Daemon must also be launched with --testnet flag')
			.option('--restricted-rpc  <boolean>', 'Restricts to view-only commands')
			.option('--wallet-file  <string>', 'Use wallet <arg>')
			.option('--generate-new-wallet  <string>', 'Generate new wallet and save it to <arg>')
			.option('--generate-from-view-key  <string>', 'Generate incoming-only wallet from view key')
			.option('--generate-from-keys  <string>', 'Generate wallet from private keys')
			.option('--generate-from-multisig-keys  <string>', 'Generate a master wallet from multisig wallet keys')
			.option('--generate-from-json  <string>', 'Generate wallet from JSON format file')
			.option('--upgrade-legacy  <string>', 'Upgrade a pre-rebase .wallet file <arg> to the new format which is compatible with this wallet')
			.option('--mnemonic-language  <string>', 'Language for mnemonic')
			.option('--command  <string>', 'run command, hint, use exit to stop auto sync')
			.option('--restore-deterministic-wallet  <boolean>', 'Recover wallet using Electrum-style mnemonic seed')
			.option('--non-deterministic  <boolean>', 'Create non-deterministic view and spend keys')
			.option('--electrum-seed  <string>', 'Specify Electrum seed for wallet recovery/creation')
			.option('--trusted-daemon  <string>', 'Enable commands which rely on a trusted daemon')
			.option('--allow-mismatched-daemon-version  <boolean>', 'Allow communicating with a daemon that uses a different RPC version')
			.option('--restore-height  <string>', 'Restore from specific blockchain height')
			.option('--disable-rpc-login  <string>', 'Disable HTTP authentication for RPC connections served by this process')
			.option('--log-file  <string>', 'Specify log file')
			.option('--log-level  <string>', '0-4 or categories')
			.option('--max-concurrency  <string>', 'Max number of threads to use for a parallel job')
			.option('--config-file  <string>', 'Config file')
			.action((args) => {
				LetheanWalletCli.run(args);
				if (Deno.env.get('REST')) {
					throw new StringResponse('Started');
				}

			});

	}
}


