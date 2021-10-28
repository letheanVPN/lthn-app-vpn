import os from 'https://deno.land/x/dos@v0.11.0/mod.ts';
import {ensureDir} from 'https://deno.land/std@0.106.0/fs/mod.ts';
import {readLines} from 'https://deno.land/std@0.79.0/io/bufio.ts';
import EventEmitter from 'https://deno.land/std@0.79.0/node/events.ts';
import {existsSync} from 'https://deno.land/std/fs/mod.ts';
import * as path from 'https://deno.land/std/path/mod.ts';
import { Command } from "https://deno.land/x/cliffy/command/mod.ts";
import { parse } from "https://deno.land/std@0.113.0/flags/mod.ts";

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
  private debug: number = 0;
  private process: stdOutStream;
  private stopped: boolean = true;
  static options: any
  constructor(daemonArgs: any) {

    daemonArgs = parse(daemonArgs)
    if(daemonArgs['debug']) {

      this.debug = 1
    }
    if (!existsSync(daemonArgs['config-file'])) {
      throw new Error(`Config file not found: ${daemonArgs['config-file']}`);
    }
    this.configFile = daemonArgs['config-file'];
    this.dataDir = daemonArgs['data-dir'];

    if (!existsSync(daemonArgs['bin-dir'])) {
      throw new Error(`Lethean CLI Folder not found: ${daemonArgs['bin-dir']}`);
    }
    this.binDir = daemonArgs['bin-dir'] === undefined ? Deno.cwd() : daemonArgs['bin-dir']
    this.exeFile = 'letheand' + (os.platform() === 'windows' ? '.exe' : '')
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

  run(){
    if(!this.stopped) return this.process

   return ensureDir(this.dataDir).then(async () => {

      this.stopped = false

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

  static async init() {
    LetheanDaemonLetheand.options = await new Command()
        .name("Lethean CLI")
        .version("0.1.0")
        .description("Command line interface for Lethean")
        .option("-h, --home-dir", "Home directory.")
        .option("-d, --data-dir", "Directory to store data.")
        .option("-c, --config-file", "Daemon config(dep)")
        .option("-b, --bin-dir", "Binaries location")
        .parse(Deno.args);
    new LetheanDaemonLetheand(LetheanDaemonLetheand.options).run()
  }
}


