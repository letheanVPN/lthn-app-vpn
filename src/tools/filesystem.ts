import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import * as path from 'https://deno.land/std/path/mod.ts';
import {StringResponse} from './string-response.ts';
import {
	ensureDirSync
} from 'https://deno.land/std@0.114.0/fs/mod.ts';

export class Filesystem {

	static path(pathname: any): string {
		// turn .. into . @todo turn this into a loop, keep going on end result until no .. remains
		pathname = pathname.replace(/\.\./g, '.');

		if (pathname.match('/')) {
			pathname = pathname.split('/');
		} else if (pathname.match('\\')) {
			pathname = pathname.split('\\');
		}

		//@ts-ignore @todo grab --home-dir if passed to backend start
		const home: string = Deno.env.get('HOME') !== undefined ? Deno.env.get('HOME') : './';

		return path.join(home, 'Lethean', ...pathname);
	}

	static read(args: any) {
		return Deno.readTextFileSync(Filesystem.path(args.path));
	}

	static list(args: any) {
		const ret = [];
		for (const dirEntry of Deno.readDirSync(Filesystem.path(args.path))) {
			if (!dirEntry.name.startsWith('.')) {
				ret.push(dirEntry.name);
			}
		}
		return JSON.stringify(ret);
	}

	static write(path: string, data: string) {
		ensureDirSync(path);
		Deno.writeTextFileSync(Filesystem.path(path), data);
		return '1';
	}

	public static config() {

		return new Command().description('File System')
			.command('list', 'List entities in path')
			.option('--path <string>', 'File path to view')
			.action((args) => {
				throw new StringResponse(Filesystem.list(args));
			})
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
			.action((args) => {
				throw new StringResponse(Filesystem.write(args.path, args.data));
			});
	}

}
