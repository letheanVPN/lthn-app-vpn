import os from 'https://deno.land/x/dos@v0.11.0/mod.ts';
import {ensureDir} from 'https://deno.land/std@0.106.0/fs/mod.ts';
import {readLines} from 'https://deno.land/std@0.79.0/io/bufio.ts';
import EventEmitter from 'https://deno.land/std@0.79.0/node/events.ts';
import {existsSync} from 'https://deno.land/std/fs/mod.ts';
import * as path from 'https://deno.land/std/path/mod.ts';
import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import {parse} from 'https://deno.land/std@0.113.0/flags/mod.ts';

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
	private command: any;
	private exeFile: string;
	private binDir: any;
	private dataDir: any;
	private configFile: any;
	private debug: number = 1;
	private process: stdOutStream;
	private stopped: boolean = true;
	static options: any;

	constructor(daemonArgs: any) {

		daemonArgs = parse(daemonArgs);
		if (daemonArgs['debug']) {

			this.debug = 1;
		}
		if (!existsSync(daemonArgs['config-file'])) {
			throw new Error(`Config file not found: ${daemonArgs['config-file']}`);
		}
		this.configFile = daemonArgs['config-file'];
		this.dataDir = daemonArgs['data-dir'];

		if (!existsSync(daemonArgs['bin-dir'])) {
			throw new Error(`Lethean CLI Folder not found: ${daemonArgs['bin-dir']}`);
		}
		this.binDir = daemonArgs['bin-dir'] === undefined ? Deno.cwd() : daemonArgs['bin-dir'];
		this.exeFile = 'letheand' + (os.platform() === 'windows' ? '.exe' : '');
		this.command = path.join(this.binDir, this.exeFile);

		if (!existsSync(this.command)) {
			throw new Error(`Lethean CLI Command Not Found: ${this.command}`);
		}

		if (daemonArgs.debug) {
			console.log(`Platform: ${os.platform()}`);
		}
		if (daemonArgs.debug) {
			console.log(`Config File: ${this.configFile}`);
		}
		if (daemonArgs.debug) {
			console.log(`Data Directory: ${this.dataDir}`);
		}
		if (daemonArgs.debug) {
			console.log(`Command: ${this.command}`);
		}
		this.process = new stdOutStream();
	}

	run() {
		if (!this.stopped) return this.process;

		return ensureDir(this.dataDir).then(async () => {

			this.stopped = false;

			return this.process.on('stdout', stdout => {
				if (this.debug) {
					console.log('stdout: ' + stdout);
				}

			}).on('stderr', stderr => {
				if (this.debug) {
					console.log('stderr: ' + stderr);
				}

			}).on('end', status => {
				if (this.debug) {
					console.log(status);
				}
			}).run(this.command,
				`--config-file=${this.configFile}`,
				`--data-dir=${this.dataDir}`);


		});
	}

	/**
	 * :   --help                                Produce help message
stderr:   --version                             Output version information
stderr:   --os-version                          OS for which this executable was
stderr:                                         compiled
stderr:   --config-file arg (=/Users/snider/.intensecoin/intensecoin.conf)
stderr:   --test-dbg-lock-sleep arg (=0)        Sleep time in ms, defaults to 0 (off), used to debug before/after locking mutex. Values 100 to 1000 are good for tests.
stderr:
stderr:    arg
stderr:



	 * @returns {any}
	 */
	public static config() {
		return new Command()
			.description('Blockchain Functions')
			.command('start', 'Start chain daemon')
			.option('--config-file', 'Specify configuration file')
			.option('--detach', 'Run as daemon')
			.option('--pidfile', 'File path to write the daemon\'s PID to (optional, requires --detach)')
			.option('--non-interactive', 'Run non-interactive')
			.option('--log-file', 'Specify log file')
			.option('--log-level', '1-4')
			.option('--max-concurrency', 'Max number of threads to use for a parallel job')
			.option('--data-dir', 'Specify data directory')
			.option('--testnet-data-dir', 'Specify testnet data directory')
			.option('--test-drop-download', 'For net tests: in download, discard ALL blocks instead checking/saving them (very fast)')
			.option('--test-drop-download-height', 'Like test-drop-download but disards only after around certain height')
			.option('--testnet', 'Run on testnet. The wallet must be launched with --testnet flag.')
			.option('--enforce-dns-checkpointing', 'checkpoints from DNS server will be enforced')
			.option('--prep-blocks-threads', 'Max number of threads to use when preparing block hashes in groups.')
			.option('--fast-block-sync', 'Sync up most of the way by using embedded, known block hashes.')
			.option('--show-time-stats', 'Show time-stats when processingblocks/txs and disk synchronization')
			.option('--block-sync-size', 'How many blocks to sync at once during chain synchronization (0 = adaptive)')
			.option('--check-updates', 'Check for new versions of monero: [disabled|notify|download|update]')
			.option('--fluffy-blocks', 'Relay blocks as fluffy blocks where possible (automatic on testnet)')
			.option('--standard-json', 'Force standard JSON output (do not  return binary data in json fields)')
			.option('--testnet-p2p-bind-port', 'Port for testnet p2p network protocol')
			.option('--p2p-bind-port', 'Port for p2p network protocol')
			.option('--extra-messages-file', 'Specify file for extra messages to include into coinbase transactions')
			.option('--start-mining', 'Specify wallet address to mining for')
			.option('--mining-threads', 'Specify mining threads count')
			.option('--bg-mining-enable', 'enable/disable background mining')
			.option('--bg-mining-ignore-battery', 'if true, assumes plugged in when unable to query system power status')
			.option('--bg-mining-min-idle-interval', 'Specify min lookback interval in seconds for determining idle state')
			.option('--bg-mining-idle-threshold', 'Specify minimum avg idle percentage over lookback interval')
			.option('--bg-mining-miner-target', 'Specify maximum percentage cpu use by miner(s)')
			.option('--db-type', 'Specify database type, available: lmdb')
			.option('--db-sync-mode', 'Specify sync option, using format [safe|fast|fastest]:[sync|async]:[nbloc ks_per_sync].')
			.option('--db-salvage', 'Try to salvage a blockchain database if it seems corrupted')
			.option('--p2p-bind-ip', 'Interface for p2p network protocol')
			.option('--p2p-external-port', 'External port for p2p network protocol (if port forwarding used with NAT)')
			.option('--allow-local-ip', 'Allow local ip add to peer list, mostly in debug purposes')
			.option('--add-peer', 'Manually add peer to local peerlist')
			.option('--add-priority-node', 'Specify list of peers to connect to and attempt to keep the connection open')
			.option('--add-exclusive-node', 'Specify list of peers to connect to only. If this option is given the options add-priority-node and seed-node  are ignored')
			.option('--seed-node', 'Connect to a node to retrieve peer  addresses, and disconnect')
			.option('--hide-my-port', 'Do not announce yourself as peerlist candidate')
			.option('--no-igd', 'Disable UPnP port mapping')
			.option('--offline', 'Do not listen for peers, nor connect to any')
			.option('--out-peers', 'set max number of out peers')
			.option('--tos-flag', 'set TOS flag')
			.option('--limit-rate-up', 'set limit-rate-up [kB/s]')
			.option('--limit-rate-down', 'set limit-rate-down [kB/s]')
			.option('--limit-rate', 'set limit-rate [kB/s]')
			.option('--save-graph', 'Save data for dr functions')
			.option('--rpc-bind-port', 'Port for RPC server')
			.option('--testnet-rpc-bind-port', 'Port for testnet RPC server')
			.option('--restricted-rpc', 'Restrict RPC to view only commands')
			.option('--rpc-bind-ip arg', 'Specify ip to bind rpc server')
			.option('--rpc-login', 'Specify username[:password] required for RPC server')
			.option('--confirm-external-bind', 'Confirm rpc-bind-ip value is NOT a loopback (local) IP')

			.action(() => {new LetheanDaemonLetheand(Deno.args).run()})
			.command('stop', 'Stop chain daemon')
			.command('import', 'Import blockchain raw data')
			.command('export', 'Export blockchain raw data')

	}
}


