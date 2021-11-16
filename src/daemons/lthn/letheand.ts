import os from 'https://deno.land/x/dos@v0.11.0/mod.ts';
import {ensureDir} from 'https://deno.land/std@0.106.0/fs/mod.ts';
import {readLines} from 'https://deno.land/std@0.79.0/io/bufio.ts';
import EventEmitter from 'https://deno.land/std@0.79.0/node/events.ts';
import * as path from 'https://deno.land/std/path/mod.ts';
import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import {StringResponse} from '../../tools/string-response.ts';
import {LetheanBlockchainExport} from './lethean-blockchain-export.ts';
import {LetheanBlockchainImport} from './lethean-blockchain-import.ts';

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


export class LetheanDaemonLetheand {
	private static command: any;
	private static exeFile: string;
	private static debug: number = 1;
	private static process: stdOutStream;

	static run(args: any) {

		let homeDir = os.homeDir();


		this.exeFile = 'letheand' + (os.platform() === 'windows' ? '.exe' : '');
		LetheanDaemonLetheand.command = path.join(homeDir ? homeDir : './', 'Lethean', 'cli', this.exeFile);

		LetheanDaemonLetheand.process = new stdOutStream();
		let cmdArgs: any = [];

		for (let arg in args) {
			if (arg !== 'igd') {
				let value = args[arg].length > 1 ? `=${args[arg]}` : '';
				cmdArgs.push('--' + arg.replace(/([A-Z])/g, (x) => '-' + x.toLowerCase()) + value);
			}

		}

		return ensureDir(args['dataDir']).then(async () => {

			return this.process.on('stdout', stdout => {
				if (this.debug) {
					console.log(stdout);
				}

			}).on('stderr', stderr => {
				if (this.debug) {
					console.log(stderr);
				}

			}).on('end', status => {
				if (this.debug) {
					console.log(status);
				}
			}).run(this.command, ...cmdArgs);


		});
	}

	public static config() {

		let home = os.homeDir();

		return new Command()
			.description('Blockchain Functions')
			.command('start', 'Start chain daemon')
			.option('--config-file <string>', 'Specify configuration file')
			.option('--detach', 'Run as daemon')
			.option('--pidfile <string>', 'File path to write the daemon\'s PID to (optional, requires --detach)')
			.option('--non-interactive', 'Run non-interactive', {default: true})
			.option('--log-file <string>', 'Specify log file')
			.option('--log-level <number>', '1-4')
			.option('--max-concurrency <number>', 'Max number of threads to use for a parallel job')
			.option('--data-dir <string>', 'Specify data directory', {default: path.join(home ? home : '/', 'Lethean', 'data')})
			.option('--testnet-data-dir <string>', 'Specify testnet data directory')
			.option('--test-drop-download', 'For net tests: in download, discard ALL blocks instead checking/saving them (very fast)')
			.option('--test-drop-download-height <number>', 'Like test-drop-download but disards only after around certain height')
			.option('--testnet', 'Run on testnet. The wallet must be launched with --testnet flag.')
			.option('--enforce-dns-checkpointing', 'checkpoints from DNS server will be enforced')
			.option('--prep-blocks-threads <number>', 'Max number of threads to use when preparing block hashes in groups.')
			.option('--fast-block-sync', 'Sync up most of the way by using embedded, known block hashes.')
			.option('--show-time-stats', 'Show time-stats when processingblocks/txs and disk synchronization')
			.option('--block-sync-size <number>', 'How many blocks to sync at once during chain synchronization (0 = adaptive)')
			.option('--check-updates <string>', 'Check for new versions of Lethean: [disabled|notify|download|update]')
			.option('--fluffy-blocks', 'Relay blocks as fluffy blocks where possible (automatic on testnet)')
			.option('--standard-json', 'Force standard JSON output (do not  return binary data in json fields)')
			.option('--testnet-p2p-bind-port <number>', 'Port for testnet p2p network protocol')
			.option('--p2p-bind-port <number>', 'Port for p2p network protocol')
			.option('--extra-messages-file <string>', 'Specify file for extra messages to include into coinbase transactions')
			.option('--start-mining <string>', 'Specify wallet address to mining for')
			.option('--mining-threads <number>', 'Specify mining threads count')
			.option('--bg-mining-enable', 'enable/disable background mining')
			.option('--bg-mining-ignore-battery', 'if true, assumes plugged in when unable to query system power status')
			.option('--bg-mining-min-idle-interval <number>', 'Specify min lookback interval in seconds for determining idle state')
			.option('--bg-mining-idle-threshold <number>', 'Specify minimum avg idle percentage over lookback interval')
			.option('--bg-mining-miner-target <string>', 'Specify maximum percentage cpu use by miner(s)')
			.option('--db-type <string>', 'Specify database type, available: lmdb')
			.option('--db-sync-mode <string>', 'Specify sync option, using format [safe|fast|fastest]:[sync|async]:[nbloc ks_per_sync].')
			.option('--db-salvage', 'Try to salvage a blockchain database if it seems corrupted')
			.option('--p2p-bind-ip <string>', 'Interface for p2p network protocol')
			.option('--p2p-external-port <string>', 'External port for p2p network protocol (if port forwarding used with NAT)')
			.option('--allow-local-ip', 'Allow local ip add to peer list, mostly in debug purposes')
			.option('--add-peer <string>', 'Manually add peer to local peerlist')
			.option('--add-priority-node <string>', 'Specify list of peers to connect to and attempt to keep the connection open')
			.option('--add-exclusive-node <string>', 'Specify list of peers to connect to only. If this option is given the options add-priority-node and seed-node  are ignored')
			.option('--seed-node <string>', 'Connect to a node to retrieve peer  addresses, and disconnect')
			.option('--hide-my-port', 'Do not announce yourself as peerlist candidate')
			.option('--no-igd', 'Disable UPnP port mapping')
			.option('--offline', 'Do not listen for peers, nor connect to any')
			.option('--out-peers <string>', 'set max number of out peers')
			.option('--tos-flag', 'set TOS flag')
			.option('--limit-rate-up <string>', 'set limit-rate-up [kB/s]')
			.option('--limit-rate-down <string>', 'set limit-rate-down [kB/s]')
			.option('--limit-rate <string>', 'set limit-rate [kB/s]')
			.option('--save-graph', 'Save data for dr functions')
			.option('--rpc-bind-port <string>', 'Port for RPC server')
			.option('--testnet-rpc-bind-port <string>', 'Port for testnet RPC server')
			.option('--restricted-rpc', 'Restrict RPC to view only commands')
			.option('--rpc-bind-ip <string>', 'Specify ip to bind rpc server')
			.option('--rpc-login <string>', 'Specify username[:password] required for RPC server')
			.option('--confirm-external-bind', 'Confirm rpc-bind-ip value is NOT a loopback (local) IP')

			.action((args) => {
				LetheanDaemonLetheand.run(args);
				if (Deno.env.get('REST')) {
					throw new StringResponse('Started');
				}

			})
			.command('export', LetheanBlockchainExport.config())
			.command('import', LetheanBlockchainImport.config());

	}
}


