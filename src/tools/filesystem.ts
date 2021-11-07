import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import * as path from 'https://deno.land/std/path/mod.ts';
import {StringResponse} from './string-response.ts';

export class Filesystem {

	static path(args: any): string {
		if (args.match('/')) {
			args = args.split('/');
		} else if (args.match('\\')) {
			args = args.split('\\');
		}

		return path.join(...args);
	}

	static read(args: any) {
		console.log(args);
		return Deno.readTextFileSync(args.path);
	}

	static write(path: string, data: string) {
		return Deno.writeTextFileSync(path, data);
	}

	public static config() {

		return new Command().description('File System')
			.command('path', 'Returns correct')
			.option('--convert <string>', 'File path to convert')
			.action((args) => {
				throw new StringResponse(Filesystem.path(args.convert));
			})
			.command('read', 'Returns file')
			.option('--path <string>', 'File path to read')
			.action((args) => {
				throw new StringResponse(Filesystem.read(args));
			})
			.command('write', 'Write a file')
			.option('--path <string>', 'File path to read')
			.option('--data <string>', 'File data to save')
			.action((args) => Filesystem.write(args.path, args.data));
	}

}
