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


export class LetheanBlockchainExport {
	private static command: any;
	private static exeFile: string;
	private static debug: number = 1;
	private static process: stdOutStream;

	static run(args: any) {

		let homeDir = os.homeDir();


		this.exeFile = 'lethean-blockchain-export' + (os.platform() === 'windows' ? '.exe' : '');
		LetheanBlockchainExport.command = path.join(homeDir ? homeDir : './', 'Lethean', 'cli', this.exeFile);

		LetheanBlockchainExport.process = new stdOutStream();
		let cmdArgs: any = [];

		for (let arg in args) {
			if (arg !== 'igd') {
				let value = args[arg].length > 1 ? `=${args[arg]}` : '';
				cmdArgs.push('--' + arg.replace(/([A-Z])/g, (x) => '-' + x.toLowerCase()) + value);
			}

		}

		//return ensureDir(args['dataDir']).then(async () => {
		console.log(LetheanBlockchainExport.command, cmdArgs);
		return LetheanBlockchainExport.process.on('stdout', stdout => {
			console.log(stdout);
		}).on('stderr', stderr => {
			console.log(stderr);
		}).run(this.command, ...cmdArgs);


		//});
	}

	public static config() {

		let home = os.homeDir();

		return new Command()
			.description('Blockchain Export')
			.option('--daemon-address <string>', 'Use daemon instance at <host>:<port>')
			.option('--data-dir  <string>', 'Specify data directory', {default: path.join(home ? home : '/', 'Lethean', 'data')})
			.option('--testnet-data-dir  <string>', 'Specify testnet data directory', {default: path.join(home ? home : '/', 'Lethean', 'data', 'testnet')})
			.option('--output-file  <string>', 'Specify output file')
			.option('--testnet  <boolean>', 'Run on testnet.')
			.option('--log-level <string>', '0-4 or categories')
			.option('--database <string>', 'available: lmdb')
			.option('--block-stop <string>', 'Stop at block number')
			.option('--blocksdat <boolean>', 'Output in blocks.dat format')
			.action((args) => {
				LetheanBlockchainExport.run(args);
				if (Deno.env.get('REST')) {
					throw new StringResponse('Started');
				}
			});

	}
}


